"""
agents/stage2_competition.py  —  Stage 2: 경쟁환경 에이전트

분석 항목:
  - 반경 내 유사업종 점포 수
  - 동 전체 vs 카테고리 개·폐업률 비교
  - 프랜차이즈 비율 (시장 포화도)
  - 경쟁 강도 종합 평가
"""

from .base_agent import BaseAgent

SYSTEM_PROMPT = """당신은 서울시 상권 데이터를 분석하는 '경쟁환경 전문 에이전트'입니다.

역할:
- 제공된 점포 수, 개·폐업률, 프랜차이즈 비율 데이터를 바탕으로
  해당 상권의 경쟁 강도와 시장 동향을 분석합니다.
- 점주가 현재 위치에서 생존 및 성장 가능성을 판단할 수 있도록 돕습니다.

출력 형식:
반드시 아래 마크다운 구조를 따르세요:

## 🏪 경쟁환경 분석 보고서

### 1. 유사업종 경쟁 현황
### 2. 시장 성장성 분석 (개·폐업률)
### 3. 프랜차이즈 vs 독립 점포 구도
### 4. 종합 경쟁 강도 평가 (매우치열/치열/보통/완화)

수치를 인용하고, 점주 입장에서 실질적으로 도움이 되는 인사이트를 포함하세요.
한국어로 작성하세요."""


def _build_user_message(data: dict) -> str:
    cat_total = data.get("카테고리_점포수", 0)
    dong_total = data.get("동_전체_점포수", 1)
    cat_franchise = data.get("카테고리_프랜차이즈_점포수", 0)
    dong_franchise = data.get("동_전체_프랜차이즈_점포수", 0)

    cat_share = round(cat_total / dong_total * 100, 1) if dong_total else 0
    cat_franchise_rate = round(cat_franchise / cat_total * 100, 1) if cat_total else 0
    dong_franchise_rate = round(dong_franchise / dong_total * 100, 1) if dong_total else 0

    msg = f"""다음 데이터를 분석하여 경쟁환경 보고서를 작성해주세요.

## 기본 정보
- 상호명: {data.get('상호명', '-')}
- 위치: {data.get('구', '-')} {data.get('동', '-')}
- 업종: {data.get('업종_카테고리', '-')}
- 점주 고민사항: {data.get('고민_사항', '-')}

## 유사업종 점포 현황
- 반경 내 유사업종 점포 수: {data.get('반경_유사업종_점포수', 0)}개
- 해당 동 카테고리 전체 점포 수: {cat_total}개
- 해당 동 전체 점포 수: {dong_total}개
- 카테고리가 동 전체 점포에서 차지하는 비율: {cat_share}%

## 개·폐업률 (시장 성장성)
| 구분 | 개업률 | 폐업률 |
|---|---|---|
| 카테고리({data.get('업종_카테고리', '-')}) | {data.get('카테고리_개업률', 0)}% | {data.get('카테고리_폐업률', 0)}% |
| 해당 동 전체 | {data.get('동_개업률', 0)}% | {data.get('동_폐업률', 0)}% |

## 프랜차이즈 현황
- 카테고리 프랜차이즈 점포 수: {cat_franchise}개 / 전체 {cat_total}개 ({cat_franchise_rate}%)
- 동 전체 프랜차이즈 점포 수: {dong_franchise}개 / 전체 {dong_total}개 ({dong_franchise_rate}%)
"""
    return msg


class CompetitionAgent:
    """경쟁환경 분석 에이전트."""

    def __init__(self):
        self._llm = BaseAgent()

    def analyze(self, data: dict) -> str:
        """
        경쟁환경을 분석하고 보고서를 반환합니다.

        Args:
            data: DataLoader가 반환한 최종 데이터 dict

        Returns:
            마크다운 형식의 경쟁환경 보고서
        """
        print("[Stage2] 경쟁환경 에이전트 분석 중...")
        user_msg = _build_user_message(data)
        report   = self._llm.generate(SYSTEM_PROMPT, user_msg)
        print("[Stage2] ✅ 경쟁환경 보고서 완성")
        return report
