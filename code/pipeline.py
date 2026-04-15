"""
pipeline.py  —  4단계 멀티에이전트 파이프라인 오케스트레이터

Stage 1: DataLoader          → enriched data dict
Stage 2: 3개 분석 에이전트   → 보고서 3개 (asyncio 병렬)
Stage 3: 종합 분석 + 작명     → 최종 보고서 2개 (asyncio 병렬)
Stage 4: 결과 출력 + JSON 저장
"""

import os
import json
import asyncio
from datetime import datetime
from data_loader import load_data
from agents import (
    CommercialActivityAgent,
    CompetitionAgent,
    IndustryRecommendAgent,
    SynthesisAgent,
    NamingAgent,
)

# ── 출력 폴더 ────────────────────────────────────────────────────
_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(_OUTPUT_DIR, exist_ok=True)


# ════════════════════════════════════════════════════════════════
# 배너 출력 유틸
# ════════════════════════════════════════════════════════════════

def _banner(stage: str, title: str):
    width = 60
    print("\n" + "=" * width)
    print(f"  {stage}  {title}")
    print("=" * width)


def _section(title: str, content: str):
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")
    print(content)


# ════════════════════════════════════════════════════════════════
# Stage 2: asyncio 병렬 실행 헬퍼
# ════════════════════════════════════════════════════════════════

async def _run_stage2_parallel(data: dict) -> tuple[str, str, str]:
    """Stage 2 에이전트 3개를 asyncio로 병렬 실행."""
    commercial_agent  = CommercialActivityAgent()
    competition_agent = CompetitionAgent()
    industry_agent    = IndustryRecommendAgent()

    loop = asyncio.get_event_loop()

    r1, r2, r3 = await asyncio.gather(
        loop.run_in_executor(None, commercial_agent.analyze,  data),
        loop.run_in_executor(None, competition_agent.analyze, data),
        loop.run_in_executor(None, industry_agent.analyze,    data),
    )
    return r1, r2, r3


async def _run_stage3_parallel(data: dict,
                                r_commercial: str,
                                r_competition: str,
                                r_industry: str) -> tuple[str, str]:
    """Stage 3 에이전트 2개를 asyncio로 병렬 실행."""
    synthesis_agent = SynthesisAgent()
    naming_agent    = NamingAgent()

    loop = asyncio.get_event_loop()

    r_synthesis, r_naming = await asyncio.gather(
        loop.run_in_executor(
            None,
            lambda: synthesis_agent.analyze(data, r_commercial, r_competition, r_industry),
        ),
        loop.run_in_executor(
            None,
            lambda: naming_agent.analyze(data, r_commercial, r_competition, r_industry),
        ),
    )
    return r_synthesis, r_naming


# ════════════════════════════════════════════════════════════════
# 메인 파이프라인
# ════════════════════════════════════════════════════════════════

def run_pipeline(user_input: dict) -> dict:
    """
    4단계 멀티에이전트 파이프라인을 실행합니다.

    Args:
        user_input: 사용자 입력 10개 필드 dict

    Returns:
        최종 결과 dict (모든 보고서 포함)
    """
    start_time = datetime.now()

    # ─── Stage 1 ───────────────────────────────────────────────
    _banner("⚙  STAGE 1", "데이터 로딩 & 조합")
    data = load_data(user_input)

    # ─── Stage 2 ───────────────────────────────────────────────
    _banner("🔍 STAGE 2", "분석 에이전트 (병렬 실행)")
    print("  상권활성도 / 경쟁환경 / 업종 추천 에이전트 동시 실행 중...")

    r_commercial, r_competition, r_industry = asyncio.run(
        _run_stage2_parallel(data)
    )

    _section("📊 상권활성도 보고서", r_commercial)
    _section("🏪 경쟁환경 보고서",   r_competition)
    _section("🗂️ 업종 추천 보고서",  r_industry)

    # ─── Stage 3 ───────────────────────────────────────────────
    _banner("🧠 STAGE 3", "종합 분석 & 상권 작명 (병렬 실행)")
    print("  종합 분석 / 상권 작명 에이전트 동시 실행 중...")

    r_synthesis, r_naming = asyncio.run(
        _run_stage3_parallel(data, r_commercial, r_competition, r_industry)
    )

    _section("🎯 종합 분석 보고서", r_synthesis)
    _section("🏷️ 상권 작명 결과",   r_naming)

    # ─── Stage 4 ───────────────────────────────────────────────
    elapsed = (datetime.now() - start_time).total_seconds()
    _banner("📤 STAGE 4", f"최종 출력 (총 소요 시간: {elapsed:.1f}초)")

    result = {
        "meta": {
            "timestamp":    datetime.now().isoformat(),
            "elapsed_sec":  round(elapsed, 2),
            "llm_provider": os.getenv("LLM_PROVIDER", "gemini"),
        },
        "input_data": data,
        "reports": {
            "상권활성도_보고서": r_commercial,
            "경쟁환경_보고서":   r_competition,
            "업종추천_보고서":   r_industry,
            "종합_분석_보고서":  r_synthesis,
            "상권_작명_결과":    r_naming,
        },
    }

    # JSON 저장
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    store_safe    = "".join(c if c.isalnum() or c in ("-", "_") else "_"
                            for c in user_input.get("상호명", "result"))
    out_path = os.path.join(_OUTPUT_DIR, f"result_{store_safe}_{timestamp_str}.json")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 분석 완료! 결과 저장: {out_path}")
    return result
