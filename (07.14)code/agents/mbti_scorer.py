"""
agents/mbti_scorer.py  —  상권 MBTI 구조화 산출기

DataLoader가 만든 enriched data dict로부터 4개 축(D/N, U/F, T/L, M/G)의
쏠림 비율(%)을 계산해 프론트에서 바로 쓸 수 있는 구조화 JSON을 반환한다.

- D/N, T/L, M/G 축은 이미 계산되어 있는 정량 데이터(시간대 유동인구/매출,
  역세권 거리, 프랜차이즈 비율)로부터 규칙 기반으로 산출한다 (LLM 미사용,
  결과가 항상 안정적이고 재현 가능함).
- U/F 축(실용형 vs 감성형)은 정량 데이터만으로 판단할 수 없는 정성적 축이라
  분위기/시그니처 상품/고민사항 텍스트를 BaseAgent에 짧게 물어 산출한다.
"""

import json
import re

from .base_agent import BaseAgent

_DAY_SLOTS = {"06~11시", "11~14시", "14~17시"}
_NIGHT_SLOTS = {"00~06시", "17~21시", "21~24시"}

_UF_SYSTEM_PROMPT = """당신은 상권 MBTI의 '가치 제안 축(U/F)'만 판정하는 채점기입니다.
U(실용형/Utility): 가성비, 빠른 회전, 실속, 필요에 의한 방문을 의미합니다.
F(감성형/Feeling): 분위기, 사진 찍기 좋음, 힐링, 취향 소비를 의미합니다.
가게의 분위기/시그니처 상품/고민사항 설명을 읽고 U와 F의 쏠림 비율(합 100)만 판정하세요.
반드시 아래 JSON 형식만 출력하세요. 다른 텍스트는 절대 포함하지 마세요.
{"U": 정수, "F": 정수}"""


def _pct(a: float, b: float) -> tuple[int, int]:
    """a, b 두 값의 비율을 합 100의 정수 % 쌍으로 변환."""
    total = a + b
    if total <= 0:
        return 50, 50
    left = round(a / total * 100)
    return left, 100 - left


def _score_dn(data: dict) -> tuple[int, int]:
    """D(주간형)/N(야간형) — 6개 시간대 유동인구+매출 전체 분포 기반.

    DataLoader가 실제 CSV에서 집계한 시간대별 전체 분포(유동인구_시간대별/매출_시간대별)가
    있으면 그걸 가중합해 완만한 점수를 낸다. "피크 시간대 하나"만 보고 낮/밤을 이분류하면
    피크가 우연히 밤 슬롯에 걸릴 때 0%/100%처럼 극단적으로 튀기 쉬운데, 6개 슬롯 전체를
    보면 그런 쏠림이 크게 줄어든다.

    전체 분포가 없는 경우(예: seed_demo_data.py처럼 손으로 만든 피크 값만 있는 데이터)는
    기존처럼 피크 시간대 하나만으로 이분류하는 방식으로 폴백한다.
    """
    pop_by_slot = data.get("유동인구_시간대별") or {}
    sales_by_slot = data.get("매출_시간대별") or {}

    if pop_by_slot or sales_by_slot:
        day_score = (
            sum(v for k, v in pop_by_slot.items() if k in _DAY_SLOTS)
            + sum(v for k, v in sales_by_slot.items() if k in _DAY_SLOTS)
        )
        night_score = (
            sum(v for k, v in pop_by_slot.items() if k in _NIGHT_SLOTS)
            + sum(v for k, v in sales_by_slot.items() if k in _NIGHT_SLOTS)
        )
        if day_score > 0 or night_score > 0:
            return _pct(day_score, night_score)

    # 폴백: 피크 시간대 하나만으로 낮/밤 이분류
    pop_day = pop_night = sales_day = sales_night = 0

    최다_유동_시간대 = data.get("최다_유동인구_시간대")
    최다_유동_수 = data.get("최다_유동인구_시간대_수", 0)
    if 최다_유동_시간대 in _DAY_SLOTS:
        pop_day += 최다_유동_수
    elif 최다_유동_시간대 in _NIGHT_SLOTS:
        pop_night += 최다_유동_수

    최다_매출_시간대 = data.get("최다_매출_시간대")
    최다_매출_금액 = data.get("최다_매출_시간대_금액", 0)
    if 최다_매출_시간대 in _DAY_SLOTS:
        sales_day += 최다_매출_금액
    elif 최다_매출_시간대 in _NIGHT_SLOTS:
        sales_night += 최다_매출_금액

    day_score = pop_day + sales_day
    night_score = pop_night + sales_night
    return _pct(day_score, night_score)


def _score_tl(data: dict) -> tuple[int, int]:
    """T(통과형)/L(로컬형) — 역세권 거리 + 반경 유사업종 밀도 기반."""
    거리 = data.get("역까지_거리_m", None)
    밀도 = data.get("반경_유사업종_점포수", 0) or 0

    # 역이 가까울수록(<=300m 역세권) + 주변 밀도가 높을수록 '통과형(유입형)'
    if 거리 is None or 거리 < 0:
        station_score = 50
    else:
        station_score = max(0, 100 - min(거리, 1000) / 10)  # 0m→100, 1000m+→0

    density_score = min(밀도, 3000) / 3000 * 100  # 0~3000개 스케일

    t_score = station_score * 0.6 + density_score * 0.4
    l_score = 100 - t_score
    return _pct(t_score, l_score)


def _score_mg(data: dict) -> tuple[int, int]:
    """M(대중형)/G(틈새형) — 카테고리 내 프랜차이즈 점포 비율 기반."""
    cat_total = data.get("카테고리_점포수", 0) or 0
    cat_franchise = data.get("카테고리_프랜차이즈_점포수", 0) or 0

    if cat_total <= 0:
        return 50, 50

    franchise_rate = cat_franchise / cat_total * 100  # 프랜차이즈 비율이 높을수록 '대중형'
    m = round(franchise_rate)
    m = max(5, min(95, m))
    return m, 100 - m


def _score_uf(data: dict) -> tuple[int, int]:
    """U(실용형)/F(감성형) — 정성 텍스트 기반 LLM 판정 (실패 시 중립값)."""
    try:
        llm = BaseAgent()
        user_msg = f"""가게 정보:
- 분위기: {data.get('분위기', '-')}
- 시그니처 상품: {data.get('시그니쳐_상품', '-')}
- 고민사항: {data.get('고민_사항', '-')}
- 업종: {data.get('업종_카테고리', '-')}"""
        raw = llm.generate(_UF_SYSTEM_PROMPT, user_msg)
        match = re.search(r"\{[^{}]*\}", raw, re.DOTALL)
        if not match:
            return 50, 50
        obj = json.loads(match.group(0))
        u, f = int(obj.get("U", 50)), int(obj.get("F", 50))
        return _pct(u, f)
    except Exception:
        return 50, 50


_AXIS_META = [
    ("D/N", "D", "N", "주간형", "야간형", _score_dn),
    ("U/F", "U", "F", "실용형", "감성형", _score_uf),
    ("T/L", "T", "L", "통과형", "로컬형", _score_tl),
    ("M/G", "M", "G", "대중형", "틈새형", _score_mg),
]


def compute_mbti(data: dict) -> dict:
    """
    DataLoader 결과 dict로부터 구조화된 상권 MBTI를 계산한다.

    Returns:
        {
          "code": "DUTM",
          "axes": [
            {"axis": "D/N", "letter_left": "D", "letter_right": "N",
             "label_left": "주간형", "label_right": "야간형",
             "pct_left": 70, "pct_right": 30},
            ...
          ]
        }
    """
    axes = []
    code = ""
    for axis, letter_left, letter_right, label_left, label_right, scorer in _AXIS_META:
        pct_left, pct_right = scorer(data)
        code += letter_left if pct_left >= pct_right else letter_right
        axes.append({
            "axis": axis,
            "letter_left": letter_left,
            "letter_right": letter_right,
            "label_left": label_left,
            "label_right": label_right,
            "pct_left": pct_left,
            "pct_right": pct_right,
        })

    return {"code": code, "axes": axes}


def mbti_vector(mbti: dict) -> list[float]:
    """클러스터링용 8차원 벡터 (각 축의 letter_left 비율 4개 + letter_right 비율 4개)."""
    vec = []
    for a in mbti["axes"]:
        vec.append(a["pct_left"] / 100.0)
        vec.append(a["pct_right"] / 100.0)
    return vec
