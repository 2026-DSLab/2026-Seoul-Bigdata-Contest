"""
agents/stage2_commercial.py  —  Stage 2: 상권활성도 에이전트

분석 항목:
  - 유동인구 시간대·성별·연령대 분포
  - 역세권 여부 (거리 ≤ 300m)
  - 매출 시간대 분포
  - 타겟 고객과 실제 유동인구/매출 정합성
"""

from .base_agent import BaseAgent

SYSTEM_PROMPT = """당신은 서울시 상권 데이터를 분석하는 '상권활성도 전문 에이전트'입니다.

역할:
- 제공된 정량적 데이터를 바탕으로 해당 상권의 활성도를 객관적으로 평가합니다.
- 유동인구, 매출 패턴, 역세권 여부를 종합하여 분석합니다.
- 운영 중인 가게 점주의 관점에서 실용적인 분석을 제공합니다.

출력 형식:
반드시 아래 마크다운 구조를 따르세요:

## 📊 상권활성도 분석 보고서

### 1. 역세권 분석
### 2. 유동인구 패턴 분석
### 3. 매출 패턴 분석
### 4. 타겟 고객 정합성
### 5. 종합 평가 (상권활성도 등급: 매우활발/활발/보통/저조)

각 섹션에서 수치를 인용하고, 간결하고 명확하게 작성하세요.
한국어로 작성하되, 전문적이고 읽기 쉬운 보고서 형식을 유지하세요."""


def _format_number(n: int | float) -> str:
    """숫자를 K/M 단위로 포맷."""
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def _build_user_message(data: dict) -> str:
    """에이전트에 전달할 사용자 메시지 생성."""
    거리 = data.get("역까지_거리_m", -1)
    if 거리 == -1:
        역세권 = "정보없음 (카카오 API 키 필요)"
        거리_표시 = "정보없음"
    elif 거리 <= 300:
        역세권 = f"역세권 ({거리}m)"
        거리_표시 = f"{거리}m"
    else:
        역세권 = f"역세권 아님 ({거리}m)"
        거리_표시 = f"{거리}m"

    msg = f"""다음 데이터를 분석하여 상권활성도 보고서를 작성해주세요.

## 기본 정보
- 상호명: {data.get('상호명', '-')}
- 위치: {data.get('구', '-')} {data.get('동', '-')}
- 업종: {data.get('업종_카테고리', '-')}
- 운영 요일: {data.get('운영시간_요일', '-')}
- 점주 고민사항: {data.get('고민_사항', '-')}
- 타겟 고객: {data.get('고객_연령층', '-')} / {data.get('성별', '-')}

## 역세권 정보
- 가장 가까운 역: {data.get('가장_가까운_역', '정보없음')} ({거리_표시})
- 역세권 여부: {역세권}

## 유동인구 현황
- 최다 유동인구 시간대: {data.get('최다_유동인구_시간대', '-')} ({_format_number(data.get('최다_유동인구_시간대_수', 0))}명)
- 최저 유동인구 시간대: {data.get('최저_유동인구_시간대', '-')} ({_format_number(data.get('최저_유동인구_시간대_수', 0))}명)
- 유동인구 성별 우세: {data.get('유동인구_성별_우세', '-')} ({_format_number(data.get('유동인구_성별_우세_수', 0))}명)
- 유동인구 성별 열세: {data.get('유동인구_성별_열세', '-')} ({_format_number(data.get('유동인구_성별_열세_수', 0))}명)
- 유동인구 연령대 1위: {data.get('유동인구_연령대_1위', '-')} ({_format_number(data.get('유동인구_연령대_1위_수', 0))}명)
- 유동인구 연령대 꼴등: {data.get('유동인구_연령대_꼴등', '-')} ({_format_number(data.get('유동인구_연령대_꼴등_수', 0))}명)
- 타겟({data.get('고객_연령층', '-')}) 유동인구: {_format_number(data.get('타겟_연령대_유동인구', 0))}명
- 타겟({data.get('성별', '-')}) 유동인구: {_format_number(data.get('타겟_성별_유동인구', 0))}명

## 매출 현황
- 최다 매출 시간대: {data.get('최다_매출_시간대', '-')} ({_format_number(data.get('최다_매출_시간대_금액', 0))}원)
- 최저 매출 시간대: {data.get('최저_매출_시간대', '-')} ({_format_number(data.get('최저_매출_시간대_금액', 0))}원)
- 매출 성별 우세: {data.get('매출_성별_우세', '-')} ({_format_number(data.get('매출_성별_우세_금액', 0))}원)
- 매출 성별 열세: {data.get('매출_성별_열세', '-')} ({_format_number(data.get('매출_성별_열세_금액', 0))}원)
- 매출 연령대 1위: {data.get('매출_연령대_1위', '-')} ({_format_number(data.get('매출_연령대_1위_금액', 0))}원)
- 타겟({data.get('고객_연령층', '-')}) 매출: {_format_number(data.get('타겟_연령대_매출', 0))}원
- 타겟({data.get('성별', '-')}) 매출: {_format_number(data.get('타겟_성별_매출', 0))}원
"""
    return msg


class CommercialActivityAgent:
    """상권활성도 분석 에이전트."""

    def __init__(self):
        self._llm = BaseAgent()

    def analyze(self, data: dict) -> str:
        """
        상권 활성도를 분석하고 보고서를 반환합니다.

        Args:
            data: DataLoader가 반환한 최종 데이터 dict

        Returns:
            마크다운 형식의 상권활성도 보고서
        """
        print("[Stage2] 상권활성도 에이전트 분석 중...")
        user_msg = _build_user_message(data)
        report   = self._llm.generate(SYSTEM_PROMPT, user_msg)
        print("[Stage2] 상권활성도 보고서 완성")
        return report
