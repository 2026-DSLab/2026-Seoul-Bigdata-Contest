"""
api/main.py  —  상권더하기 FastAPI 앱

기존 CLI 파이프라인(data_loader.py, agents/, pipeline.py)을 그대로 재사용하여
슬라이드 7·9·13·15의 화면에 필요한 4개 엔드포인트를 제공한다.

실행: uvicorn api.main:app --reload --port 8000  (반드시 (07.14)code/ 디렉토리에서 실행)
"""

import asyncio
import os
import sys
import uuid

# Windows 콘솔 기본 코드페이지(cp949)로는 로그 속 이모지·em dash가 깨져 UnicodeEncodeError로
# 요청 자체가 500 나는 경우가 있어, 실행 방식(터미널/서비스)과 무관하게 항상 UTF-8로 고정한다.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# api/ 의 부모 디렉토리(코드 루트)를 sys.path에 추가 — 실행 위치와 무관하게 기존 모듈 임포트 보장
_CODE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _CODE_ROOT not in sys.path:
    sys.path.insert(0, _CODE_ROOT)

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

load_dotenv()

import db
import clustering
from data_loader import load_data
from agents import (
    CommercialActivityAgent,
    CompetitionAgent,
    IndustryRecommendAgent,
    SynthesisAgent,
    BrandingAgent,
    compute_mbti,
)

app = FastAPI(title="상권더하기 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 데모 목적. 배포 시 프론트 도메인으로 제한 권장.
    allow_methods=["*"],
    allow_headers=["*"],
)


# ════════════════════════════════════════════════════════════════
# 요청/응답 모델
# ════════════════════════════════════════════════════════════════

class AnalyzeRequest(BaseModel):
    상호명: str
    구: str
    동: str
    업종_카테고리: str
    운영_요일: str = "주7일"
    오픈_시간: str = "09:00"
    마감_시간: str = "22:00"
    시그니쳐_상품: str = ""
    분위기: str = ""
    고민_사항: str = ""
    주고객_연령층: str = "20대"
    주고객_성별: str = "여성"
    extra: dict = Field(default_factory=dict)  # 슬라이드9의 추가 정보 필드(객단가, 가게 장점 등) 자유 저장


class JoinDistrictRequest(BaseModel):
    district_id: str
    district_label: str
    member_store_ids: list[int]


# ════════════════════════════════════════════════════════════════
# 내부 헬퍼
# ════════════════════════════════════════════════════════════════

async def _run_stage2(data: dict) -> tuple[str, str, str]:
    loop = asyncio.get_event_loop()
    commercial_agent = CommercialActivityAgent()
    competition_agent = CompetitionAgent()
    industry_agent = IndustryRecommendAgent()
    return await asyncio.gather(
        loop.run_in_executor(None, commercial_agent.analyze, data),
        loop.run_in_executor(None, competition_agent.analyze, data),
        loop.run_in_executor(None, industry_agent.analyze, data),
    )


def _cluster_to_card(cluster: dict, branding: dict) -> dict:
    return {
        "district_id": None,  # join 시점에 확정
        "label": branding.get("label", cluster["centroid_mbti_code"]),
        "tags": branding.get("tags", []),
        "main_categories": branding.get("main_categories", ""),
        "mood": branding.get("mood", ""),
        "visitor_feature": branding.get("visitor_feature", ""),
        "strategies": branding.get("strategies", []),
        "mbti_code": cluster["centroid_mbti_code"],
        "similarity": round(cluster.get("similarity", 0.0), 3),
        "member_store_ids": [m["id"] for m in cluster["members"]],
        "member_count": len(cluster["members"]),
        "polygon": cluster["polygon"],
        "member_pins": [
            {"id": m["id"], "상호명": m["상호명"], "lat": m["lat"], "lng": m["lng"],
             "mbti_code": m["mbti_code"], "업종_카테고리": m["업종_카테고리"]}
            for m in cluster["members"]
        ],
    }


# ════════════════════════════════════════════════════════════════
# 엔드포인트
# ════════════════════════════════════════════════════════════════

@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest):
    """STEP1: 우리 가게 MBTI 진단 — Stage1+2+MBTI+종합분석 실행 후 DB에 저장."""
    user_input = req.model_dump(exclude={"extra"})

    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, load_data, user_input)

    r_commercial, r_competition, r_industry = await _run_stage2(data)
    mbti = await loop.run_in_executor(None, compute_mbti, data)

    synthesis_agent = SynthesisAgent()
    r_synthesis = await loop.run_in_executor(
        None, synthesis_agent.analyze, data, r_commercial, r_competition, r_industry
    )

    store_id = db.insert_store(
        상호명=data.get("상호명", req.상호명),
        구=data.get("구", req.구),
        동=data.get("동", req.동),
        lat=data.get("위도"),
        lng=data.get("경도"),
        업종_카테고리=data.get("업종_카테고리", req.업종_카테고리),
        mbti_code=mbti["code"],
        mbti_axes=mbti["axes"],
        input_data=data,
        reports={
            "상권활성도_보고서": r_commercial,
            "경쟁환경_보고서": r_competition,
            "업종추천_보고서": r_industry,
            "종합_분석_보고서": r_synthesis,
        },
    )

    return {
        "store_id": store_id,
        "mbti": mbti,
        "reports": {
            "상권활성도_보고서": r_commercial,
            "경쟁환경_보고서": r_competition,
            "업종추천_보고서": r_industry,
            "종합_분석_보고서": r_synthesis,
        },
    }


@app.get("/api/stores/{store_id}")
def get_store(store_id: int):
    store = db.get_store(store_id)
    if not store:
        raise HTTPException(404, "가게를 찾을 수 없습니다.")
    return store


@app.get("/api/stores/{store_id}/recommendations")
def get_recommendations(store_id: int):
    """STEP2: 우리 가게 상권 추천 — MBTI 유사도 기반 Top3 클러스터."""
    store = db.get_store(store_id)
    if not store:
        raise HTTPException(404, "가게를 찾을 수 없습니다.")

    clusters = clustering.recommend_top_clusters(store_id, n=3)
    if not clusters:
        return {
            "status": "insufficient_data",
            "message": "도보권 내에 비교할 가게 데이터가 아직 충분하지 않습니다. "
                       "새로운 상권을 시작하는 첫 가게가 되어보세요!",
            "recommendations": [],
        }

    branding_agent = BrandingAgent()
    cards = []
    for cluster in clusters:
        branding = branding_agent.brand_cluster(cluster["members"], cluster["centroid_mbti_code"])
        cards.append(_cluster_to_card(cluster, branding))

    return {"status": "ok", "recommendations": cards}


@app.post("/api/stores/{store_id}/join-district")
def join_district(store_id: int, req: JoinDistrictRequest):
    """STEP2 확정: Top3 중 하나 선택 → 클러스터 멤버 + 본인 가게를 같은 district_id로 확정."""
    store = db.get_store(store_id)
    if not store:
        raise HTTPException(404, "가게를 찾을 수 없습니다.")

    all_ids = list(set(req.member_store_ids + [store_id]))
    db.assign_district(all_ids, req.district_id, req.district_label)
    return {"status": "ok", "district_id": req.district_id, "member_count": len(all_ids)}


@app.get("/api/districts/{district_id}")
async def get_district(district_id: str):
    """
    STEP3: 우리 상권+ 대시보드 — 지도 폴리곤 + 멤버 핀 + 공동 브랜딩 전략.

    슬라이드 15처럼 지도 위에 "우리 상권"뿐 아니라 도보권 안의 다른 정체성 클러스터들도
    함께 보여준다 (색으로 구분). 클러스터 경계는 매 요청마다 현재 stores.db 상태로
    다시 계산되므로 하드코딩이 아니라 실시간 재계산 값이다.

    "우리 상권"은 확정된 멤버(district_id)를 그대로 하나의 폴리곤으로 고정 표시한다.
    재클러스터링 결과가 확정 멤버를 두 클러스터로 쪼개더라도(예: MBTI가 애매하게
    갈리는 경우) 같은 이름의 폴리곤이 지도에 중복 표시되지 않도록, 확정 멤버를 포함하는
    클러스터는 "주변 상권" 목록에서 제외한다.
    """
    members = db.list_stores_by_district(district_id)
    if not members:
        raise HTTPException(404, "상권을 찾을 수 없습니다.")

    mbti_codes = [m["mbti_code"] for m in members if m["mbti_code"]]
    dominant_code = max(set(mbti_codes), key=mbti_codes.count) if mbti_codes else "----"

    branding_agent = BrandingAgent()
    branding = branding_agent.brand_cluster(members, dominant_code)
    our_label = members[0].get("district_label") or branding.get("label")

    confirmed_ids = {m["id"] for m in members}
    all_clusters = clustering.cluster_all_stores()
    our_polygon = clustering._hull_polygon(members)

    neighbor_clusters = [
        c for c in all_clusters
        if not ({m["id"] for m in c["members"]} & confirmed_ids)
        # 우리 상권과 겹치는 클러스터는 위에서 이미 고정 표시했으므로 건너뜀
    ]

    # "주변 상권"도 원시 MBTI 코드가 아니라 "우리 상권"과 동일하게 AI가 재정의한
    # 상권 이름을 보여준다 (여러 클러스터이므로 병렬로 호출해 지연을 줄인다).
    # 클라이언트 인스턴스를 스레드 간에 공유하지 않도록 호출마다 새로 만든다.
    def _brand_neighbor(cluster_members: list[dict], code: str) -> dict:
        return BrandingAgent().brand_cluster(cluster_members, code)

    loop = asyncio.get_event_loop()
    neighbor_brandings = await asyncio.gather(*[
        loop.run_in_executor(None, _brand_neighbor, c["members"], c["centroid_mbti_code"])
        for c in neighbor_clusters
    ]) if neighbor_clusters else []

    clusters_payload = [{
        "label": our_label,
        "name": our_label,
        "is_ours": True,
        "mbti_code": dominant_code,
        "polygon": our_polygon,
        "distance_m": 0,
        "tags": branding.get("tags", []),
        "main_categories": branding.get("main_categories", ""),
        "mood": branding.get("mood", ""),
        "visitor_feature": branding.get("visitor_feature", ""),
        "member_pins": [
            {"id": m["id"], "상호명": m["상호명"], "lat": m["lat"], "lng": m["lng"],
             "mbti_code": m["mbti_code"], "업종_카테고리": m["업종_카테고리"]}
            for m in members
        ],
    }]
    for cluster, n_branding in zip(neighbor_clusters, neighbor_brandings):
        동_list = [m["동"] for m in cluster["members"] if m.get("동")]
        dominant_동 = max(set(동_list), key=동_list.count) if 동_list else ""

        dist_m = clustering.nearest_distance_m(members, cluster["members"])
        dist_suffix = ""
        if dist_m is not None:
            dist_suffix = f" · 도보 {round(dist_m)}m" if dist_m < 1000 else f" · 도보 {dist_m / 1000:.1f}km"

        # 재정의된 상권 이름(브랜딩 실패 시 brand_cluster 자체 폴백인 "{코드} 상권" 사용) +
        # 동 이름(서로 다른 물리적 클러스터가 우연히 같은 이름/코드를 가질 때 범례에서 구분용) +
        # 실제 거리(dist_suffix)까지 함께 보여준다.
        neighbor_label = n_branding.get("label") or f"{cluster['centroid_mbti_code']} 상권"
        label = (
            f"{neighbor_label} ({dominant_동}){dist_suffix}"
            if dominant_동 else f"{neighbor_label}{dist_suffix}"
        )
        clusters_payload.append({
            "label": label,
            "name": neighbor_label,
            "is_ours": False,
            "mbti_code": cluster["centroid_mbti_code"],
            "polygon": cluster["polygon"],
            "distance_m": round(dist_m) if dist_m is not None else None,
            "tags": n_branding.get("tags", []),
            "main_categories": n_branding.get("main_categories", ""),
            "mood": n_branding.get("mood", ""),
            "visitor_feature": n_branding.get("visitor_feature", ""),
            "member_pins": [
                {"id": m["id"], "상호명": m["상호명"], "lat": m["lat"], "lng": m["lng"],
                 "mbti_code": m["mbti_code"], "업종_카테고리": m["업종_카테고리"]}
                for m in cluster["members"]
            ],
        })

    return {
        "district_id": district_id,
        "label": our_label,
        "polygon": our_polygon,
        "clusters": clusters_payload,
        "member_pins": [
            {"id": m["id"], "상호명": m["상호명"], "lat": m["lat"], "lng": m["lng"],
             "mbti_code": m["mbti_code"], "업종_카테고리": m["업종_카테고리"]}
            for m in members
        ],
        "member_count": len(members),
        "tags": branding.get("tags", []),
        "main_categories": branding.get("main_categories", ""),
        "strategies": branding.get("strategies", []),
    }


@app.get("/api/health")
def health():
    return {"status": "ok"}
