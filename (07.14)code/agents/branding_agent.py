"""
agents/branding_agent.py  —  Phase 3~4: 상권 브랜딩 에이전트

stage3_naming.py(개별 가게 1곳의 상권 이름 제안)와 달리,
이미 MBTI 유사도로 클러스터링된 "가게 그룹"을 입력받아
그 그룹 전체를 대표하는 상권 정체성(레이블/태그/공동 브랜딩 전략)을
구조화된 JSON으로 산출한다. (슬라이드 12 Phase3, 슬라이드 15 화면용)
"""

import json
import re

from .base_agent import BaseAgent

SYSTEM_PROMPT = """당신은 '상권 브랜딩 에이전트'입니다. 개별 가게가 아니라,
MBTI 성향이 비슷해 하나의 클러스터로 묶인 '가게 그룹 전체'를 대표하는
상권(골목) 정체성을 만듭니다.

다음은 참고할 작명 예시(Few-Shot)입니다.
[예시] 20대 여성 유동인구 중심, 카페/주점/루프탑 밀집, 통과형(역세권) 그룹
→ 레이블: "서교 힙스팟" / 태그: #20대 #통과형 #젊음 #트렌디

[예시] 30~40대 로컬 단골 중심, 조용하고 여유로운 분위기, 카페/브런치/책방 그룹
→ 레이블: "티 로드" / 태그: #2030 #통과형 #여유 #감각적

반드시 아래 JSON 형식만 출력하세요. 다른 설명 텍스트를 절대 포함하지 마세요.
{
  "label": "상권(골목) 이름",
  "tags": ["#태그1", "#태그2", "#태그3", "#태그4"],
  "main_categories": "대표 업종 (쉼표로 나열)",
  "mood": "대표 분위기 한 줄",
  "visitor_feature": "방문 특징 한 줄 (예: 20대 여성 유동인구 중심)",
  "strategies": [
    {"title": "공동 브랜딩 전략 제목", "description": "1~2문장 설명", "effect": "기대 효과 한 줄"},
    {"title": "공동 브랜딩 전략 제목 2", "description": "1~2문장 설명", "effect": "기대 효과 한 줄"}
  ]
}"""


def _build_user_message(members: list[dict], centroid_mbti_code: str) -> str:
    lines = [f"- {m.get('상호명', '가게')} | 업종: {m.get('업종_카테고리', '-')} | "
             f"분위기: {m.get('분위기', '-')} | MBTI: {m.get('mbti_code', '-')}"
             for m in members]
    return f"""이 클러스터의 대표 MBTI: {centroid_mbti_code}
그룹에 속한 가게 {len(members)}곳:
{chr(10).join(lines)}

위 그룹 전체를 대표하는 상권 정체성을 JSON으로 만들어주세요."""


class BrandingAgent:
    """클러스터(가게 그룹) 단위 상권 브랜딩 에이전트."""

    def __init__(self):
        self._llm = BaseAgent()

    def brand_cluster(self, members: list[dict], centroid_mbti_code: str) -> dict:
        """
        클러스터 멤버 목록을 받아 상권 브랜딩 결과(JSON dict)를 반환한다.
        LLM 응답 파싱에 실패하면 최소한의 폴백 구조를 반환한다.
        """
        user_msg = _build_user_message(members, centroid_mbti_code)
        raw = self._llm.generate(SYSTEM_PROMPT, user_msg)
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        categories = ", ".join(sorted({m.get("업종_카테고리", "-") for m in members}))
        return {
            "label": f"{centroid_mbti_code} 상권",
            "tags": [f"#{centroid_mbti_code}"],
            "main_categories": categories,
            "mood": "-",
            "visitor_feature": "-",
            "strategies": [],
        }
