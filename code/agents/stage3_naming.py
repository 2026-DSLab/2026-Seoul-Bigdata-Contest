"""
agents/stage3_naming.py  —  Stage 3: 상권 작명 에이전트

입력:
  - Stage 2 보고서 3개
  - 사용자 입력 (분위기, 시그니처 상품, 위치 등)

출력:
  - 상권 이름 후보 3개 + 각 작명 근거
"""

from .base_agent import BaseAgent

SYSTEM_PROMPT = """당신은 창의적인 브랜드 네이밍 전문가이면서 상권 분석가인 '상권 작명 에이전트'입니다.

역할:
- 해당 상권의 특성(유동인구, 경쟁환경, 업종 특성)과 가게의 정체성(분위기, 시그니처 상품)을 결합하여
  이 상권을 한 단어나 짧은 문구로 표현하는 창의적인 이름을 제안합니다.
- 이름은 상권의 실제 데이터와 지역적 특성을 담아야 합니다.
- 누구나 들었을 때 그 상권의 분위기와 특성을 직관적으로 이해할 수 있어야 합니다.

출력 형식:
반드시 아래 마크다운 구조를 따르세요:

## 🏷️ 상권 작명 결과

### 작명 철학
(이 상권의 핵심 특성 요약)

### 후보 1: [이름]
- **의미**: 
- **작명 근거**: (데이터 기반 설명)
- **활용 예시**: (슬로건이나 마케팅 문구)

### 후보 2: [이름]
- **의미**: 
- **작명 근거**: 
- **활용 예시**: 

### 후보 3: [이름]
- **의미**: 
- **작명 근거**: 
- **활용 예시**: 

### 최종 추천
(3개 중 가장 적합한 이름과 이유)

한국어로 작성하되, 이름 자체는 한국어·영어·혼합 모두 가능합니다."""


def _build_user_message(data: dict, report_commercial: str,
                         report_competition: str, report_industry: str) -> str:
    msg = f"""아래 정보를 바탕으로 이 상권의 이름을 3개 제안해주세요.

## 가게 정체성
- 상호명: {data.get('상호명', '-')}
- 위치: {data.get('구', '-')} {data.get('동', '-')}
- 업종: {data.get('업종_카테고리', '-')}
- 분위기: {data.get('분위기', '-')}
- 시그니처 상품: {data.get('시그니쳐_상품', '-')}
- 타겟 고객: {data.get('고객_연령층', '-')} / {data.get('성별', '-')}
- 운영 요일: {data.get('운영시간_요일', '-')}

## 핵심 상권 데이터
- 가장 가까운 역: {data.get('가장_가까운_역', '-')} ({data.get('역까지_거리_m', '-')}m)
- 역세권 여부: {'역세권 ✅' if data.get('역까지_거리_m', 9999) <= 300 else '역세권 아님'}
- 최다 유동인구 시간대: {data.get('최다_유동인구_시간대', '-')}
- 유동인구 1위 연령대: {data.get('유동인구_연령대_1위', '-')}
- 최다 매출 시간대: {data.get('최다_매출_시간대', '-')}
- 카테고리: {data.get('업종_카테고리', '-')}

---

## [보고서 1] 상권활성도 분석 요약
{report_commercial[:800]}...

---

## [보고서 2] 경쟁환경 분석 요약
{report_competition[:800]}...

---

## [보고서 3] 업종 추천 분석 요약
{report_industry[:800]}...
"""
    return msg


class NamingAgent:
    """상권 작명 에이전트."""

    def __init__(self):
        self._llm = BaseAgent()

    def analyze(self, data: dict, report_commercial: str,
                report_competition: str, report_industry: str) -> str:
        """
        상권 이름 후보 3개를 생성하고 반환합니다.

        Args:
            data:               DataLoader가 반환한 최종 데이터 dict
            report_commercial:  상권활성도 보고서
            report_competition: 경쟁환경 보고서
            report_industry:    업종 추천 보고서

        Returns:
            마크다운 형식의 상권 작명 결과
        """
        print("[Stage3] 상권 작명 에이전트 분석 중...")
        user_msg = _build_user_message(data, report_commercial,
                                       report_competition, report_industry)
        result = self._llm.generate(SYSTEM_PROMPT, user_msg)
        print("[Stage3] ✅ 상권 작명 완성")
        return result
