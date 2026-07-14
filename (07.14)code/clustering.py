"""
clustering.py  —  Phase 3: MBTI 클러스터링 및 Top3 상권 추천

db.py에 누적된 같은 구(區) 내 가게들의 MBTI 8차원 벡터를 KMeans로 묶어
'상권 후보 클러스터'를 만들고, 특정 가게와 가장 유사한 클러스터 Top N을 추천한다.
클러스터의 지리적 경계는 멤버 좌표의 convex hull(3개 미만이면 원형 버퍼)로 근사한다.
"""

import math

import numpy as np
from sklearn.cluster import KMeans

import db
from agents.mbti_scorer import mbti_vector

MIN_STORES_FOR_CLUSTERING = 3
_CIRCLE_BUFFER_M = 90  # 멤버가 1~2곳뿐일 때 표시할 원형 버퍼 반경(m)


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def _circle_polygon(lat: float, lng: float, radius_m: float = _CIRCLE_BUFFER_M, n: int = 16) -> list[list[float]]:
    """중심 좌표 기준 반경 radius_m 짜리 근사 원형 폴리곤 [[lat, lng], ...]."""
    points = []
    lat_rad = math.radians(lat)
    for i in range(n):
        angle = 2 * math.pi * i / n
        d_lat = (radius_m * math.cos(angle)) / 111_320
        d_lng = (radius_m * math.sin(angle)) / (111_320 * math.cos(lat_rad) or 1)
        points.append([lat + d_lat, lng + d_lng])
    return points


def _hull_polygon(members: list[dict]) -> list[list[float]]:
    coords = [[m["lat"], m["lng"]] for m in members if m["lat"] is not None and m["lng"] is not None]
    if len(coords) < 3:
        if not coords:
            return []
        avg_lat = sum(c[0] for c in coords) / len(coords)
        avg_lng = sum(c[1] for c in coords) / len(coords)
        return _circle_polygon(avg_lat, avg_lng)

    try:
        from scipy.spatial import ConvexHull
        pts = np.array(coords)
        hull = ConvexHull(pts)
        return [list(pts[i]) for i in hull.vertices]
    except Exception:
        avg_lat = sum(c[0] for c in coords) / len(coords)
        avg_lng = sum(c[1] for c in coords) / len(coords)
        return _circle_polygon(avg_lat, avg_lng, radius_m=150)


def _mbti_code_from_centroid(centroid: np.ndarray) -> str:
    from agents.mbti_scorer import _AXIS_META  # letter order reference
    code = ""
    for i, (axis, letter_left, letter_right, *_rest) in enumerate(_AXIS_META):
        left_val, right_val = centroid[i * 2], centroid[i * 2 + 1]
        code += letter_left if left_val >= right_val else letter_right
    return code


def cluster_stores_in_gu(구: str, exclude_id: int | None = None) -> list[dict]:
    """
    같은 구 내 가게들을 MBTI 유사도로 클러스터링한다.

    Returns:
        [{"members": [...], "centroid": np.ndarray, "centroid_mbti_code": str,
          "polygon": [[lat,lng],...]}]
        데이터가 부족하면 빈 리스트.
    """
    stores = db.list_stores_by_gu(구, exclude_id=exclude_id)
    if len(stores) < MIN_STORES_FOR_CLUSTERING:
        return []

    vectors = np.array([mbti_vector({"axes": s["mbti_axes"]}) for s in stores])
    k = max(1, min(3, len(stores) // 3))
    kmeans = KMeans(n_clusters=k, n_init=10, random_state=42).fit(vectors)

    clusters = []
    for cluster_idx in range(k):
        member_mask = kmeans.labels_ == cluster_idx
        members = [s for s, keep in zip(stores, member_mask) if keep]
        if not members:
            continue
        centroid = kmeans.cluster_centers_[cluster_idx]
        clusters.append({
            "members": members,
            "centroid": centroid,
            "centroid_mbti_code": _mbti_code_from_centroid(centroid),
            "polygon": _hull_polygon(members),
        })
    return clusters


def recommend_top_clusters(store_id: int, n: int = 3) -> list[dict]:
    """
    특정 가게(store_id)와 MBTI 벡터가 가장 유사한 상권 클러스터 Top N을 반환한다.
    같은 구에 클러스터링할 데이터가 부족하면 빈 리스트를 반환한다 (호출부에서 폴백 처리).
    """
    target = db.get_store(store_id)
    if target is None:
        return []

    clusters = cluster_stores_in_gu(target["구"], exclude_id=store_id)
    if not clusters:
        return []

    target_vec = np.array(mbti_vector({"axes": target["mbti_axes"]}))
    for c in clusters:
        c["similarity"] = _cosine_similarity(target_vec, c["centroid"])

    clusters.sort(key=lambda c: c["similarity"], reverse=True)
    return clusters[:n]
