"""
agents/stage2_industry.py  —  Stage 2: 업종 추천 에이전트

분석 항목:
  - 동 내 카테고리별 매출 순위
  - 사용자 업종의 상대적 위치
  - 최대·최소 매출 업종과 비교
  - 업종 전환 또는 유지 권고
"""

from .base_agent import BaseAgent

SYSTEM_PROMPT = """당신은 서울시 상권 데이터를 분석하는 '업종 추천 전문 에이전트'입니다.

역할:
- 해당 행정동(동)의 업종별 매출 순위 데이터를 바탕으로
  현재 점주의 업종이 얼마나 경쟁력 있는지 분석합니다.
- 최대 매출 업종과 최소 매출 업종을 기준으로 점주의 위치를 파악합니다.
- 업종 유지 / 부업 추가 / 업종 전환 등 실용적인 방향을 제시합니다.

출력 형식:
반드시 아래 마크다운 구조를 따르세요:

## 🗂️ 업종 추천 분석 보고서

### 1. 해당 동 업종별 매출 순위
### 2. 현재 업종 포지셔닝
### 3. 최대 매출 업종 비교 분석
### 4. 최소 매출 업종 비교 분석
### 5. 업종 전략 권고

한국어로 작성하며, 수치를 명확히 인용하세요."""


def _format_number(n: int | float) -> str:
    if n >= 1_000_000_000_000:
        return f"{n / 1_000_000_000_000:.1f}조"
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}억원대"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.0f}만원"
    if n >= 1_000:
        return f"{n / 1_000:.1f}천원"
    return f"{n}원"


def _build_user_message(data: dict) -> str:
    category   = data.get("업종_카테고리", "-")
    max_cat    = data.get("동_카테고리_매출_최대_업종", "-")
    min_cat    = data.get("동_카테고리_매출_최소_업종", "-")
    ranking    = data.get("동_카테고리_매출_순위", [])

    # 순위 테이블 생성
    if ranking:
        rank_table = "| 순위 | 업종 | 월매출 합계 |\n|---|---|---|\n"
        for r in ranking[:10]:  # 상위 10개만
            rank_table += f"| {r['순위']}위 | {r['업종']} | {_format_number(r['매출'])} |\n"
        # 현재 업종 순위 찾기
        user_rank = next((r['순위'] for r in ranking if r['업종'] == category), "순위 외")
        max_sales = next((r['매출'] for r in ranking if r['업종'] == max_cat), 0)
        min_sales = next((r['매출'] for r in ranking if r['업종'] == min_cat), 0)
        user_sales = next((r['매출'] for r in ranking if r['업종'] == category), 0)
    else:
        rank_table = "데이터 없음"
        user_rank = "-"
        max_sales = user_sales = min_sales = 0

    msg = f"""다음 데이터를 분석하여 업종 추천 보고서를 작성해주세요.

## 기본 정보
- 상호명: {data.get('상호명', '-')}
- 위치: {data.get('구', '-')} {data.get('동', '-')}
- 현재 업종: {category}
- 점주 고민사항: {data.get('고민_사항', '-')}
- 타겟 고객: {data.get('고객_연령층', '-')} / {data.get('성별', '-')}
- 시그니처 상품: {data.get('시그니쳐_상품', '-')}
- 분위기: {data.get('분위기', '-')}

## 동 내 업종별 월매출 순위 (상위 10개)
{rank_table}

## 핵심 비교 지표
- 최대 매출 업종: {max_cat} ({_format_number(max_sales)})
- 최소 매출 업종: {min_cat} ({_format_number(min_sales)})
- 현재 업종({category}) 순위: {user_rank}위 ({_format_number(user_sales)})
- 최대 대비 현재 비율: {round(user_sales / max_sales * 100, 1) if max_sales else 0}%
"""
    return msg


class IndustryRecommendAgent:
    """업종 추천 분석 에이전트."""

    def __init__(self):
        self._llm = BaseAgent()

    def analyze(self, data: dict) -> str:
        """
        업종 경쟁력을 분석하고 보고서를 반환합니다.

        Args:
            data: DataLoader가 반환한 최종 데이터 dict (카테고리 순위 포함)

        Returns:
            마크다운 형식의 업종 추천 보고서
        """
        print("[Stage2] 업종 추천 에이전트 분석 중...")
        user_msg = _build_user_message(data)
        report   = self._llm.generate(SYSTEM_PROMPT, user_msg)
        print("[Stage2] ✅ 업종 추천 보고서 완성")
        return report
