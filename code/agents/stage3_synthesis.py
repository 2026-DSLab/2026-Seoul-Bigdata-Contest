"""
agents/stage3_synthesis.py  —  Stage 3: 종합 분석 에이전트

입력:
  - Stage 2에서 생성된 3개의 보고서 (상권활성도 / 경쟁환경 / 업종 추천)
  - 사용자 고민사항

출력:
  - 종합 인사이트 + 우선순위별 실행 가능한 솔루션
"""

from .base_agent import BaseAgent

SYSTEM_PROMPT = """당신은 상권 분석 전문 컨설턴트 역할의 '종합 분석 에이전트'입니다.

역할:
- 세 가지 전문 에이전트(상권활성도 / 경쟁환경 / 업종 추천)의 분석 보고서를 통합하여
  점주에게 가장 실질적이고 구체적인 인사이트와 솔루션을 제공합니다.
- 데이터 기반의 논리적 근거를 항상 포함합니다.
- 단기(1개월) / 중기(3~6개월) / 장기(1년+) 전략을 구분하여 제시합니다.

출력 형식:
반드시 아래 마크다운 구조를 따르세요:

## 🎯 종합 분석 보고서 — 상권 컨설팅 인사이트

### 핵심 요약 (Executive Summary)
### 1. 통합 인사이트
### 2. 점주 고민 해결 방안 (고민사항 직접 답변)
### 3. 우선순위 액션 플랜
  #### 🔴 단기 (1개월 이내)
  #### 🟡 중기 (3~6개월)
  #### 🟢 장기 (1년+)
### 4. 리스크 및 주의사항

근거 없는 추측은 하지 말고, 세 보고서의 데이터를 반드시 인용하며 작성하세요.
한국어로 작성하세요."""


def _build_user_message(data: dict, report_commercial: str,
                         report_competition: str, report_industry: str) -> str:
    msg = f"""아래 세 보고서를 종합하여 종합 분석 보고서를 작성해주세요.

## 사용자 기본 정보
- 상호명: {data.get('상호명', '-')}
- 위치: {data.get('구', '-')} {data.get('동', '-')}
- 업종: {data.get('업종_카테고리', '-')}
- 운영 요일: {data.get('운영시간_요일', '-')}
- 시그니처 상품: {data.get('시그니쳐_상품', '-')}
- 분위기: {data.get('분위기', '-')}
- 타겟 고객: {data.get('고객_연령층', '-')} / {data.get('성별', '-')}
- 점주 고민사항: {data.get('고민_사항', '-')}

---

## [보고서 1] 상권활성도 분석
{report_commercial}

---

## [보고서 2] 경쟁환경 분석
{report_competition}

---

## [보고서 3] 업종 추천 분석
{report_industry}
"""
    return msg


class SynthesisAgent:
    """종합 분석 에이전트 — 3개 보고서 통합 인사이트 생성."""

    def __init__(self):
        self._llm = BaseAgent()

    def analyze(self, data: dict, report_commercial: str,
                report_competition: str, report_industry: str) -> str:
        """
        3개 Stage 2 보고서를 통합하여 종합 인사이트를 반환합니다.

        Args:
            data:               DataLoader가 반환한 최종 데이터 dict
            report_commercial:  상권활성도 보고서 (마크다운)
            report_competition: 경쟁환경 보고서 (마크다운)
            report_industry:    업종 추천 보고서 (마크다운)

        Returns:
            마크다운 형식의 종합 분석 보고서
        """
        print("[Stage3] 종합 분석 에이전트 분석 중...")
        user_msg = _build_user_message(data, report_commercial,
                                       report_competition, report_industry)
        report = self._llm.generate(SYSTEM_PROMPT, user_msg)
        print("[Stage3] ✅ 종합 분석 보고서 완성")
        return report
