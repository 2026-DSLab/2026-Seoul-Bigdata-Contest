"""
clustering.py  —  Phase 3: MBTI 클러스터링 및 Top3 상권 추천

상권을 "행정구역(구/동)"이 아니라 "정체성(MBTI)"으로 재정의한다는 것이 이 서비스의
핵심 차별점이다 (PDF 슬라이드 18 경쟁력3). 그래서 클러스터링의 주(主) 기준은 MBTI
8차원 벡터의 코사인 유사도이며, 구 경계는 전혀 신경 쓰지 않는다.

다만 정체성이 같아도 도보로 갈 수 없을 만큼 멀리 떨어져 있으면 공동 브랜딩(팝업,
투어 코스, 오프라인 이벤트)이 물리적으로 불가능하므로, 도보권(_WALK_CAP_M) 밖의
가게 쌍은 아예 같은 클러스터로 묶이지 않도록 하드 게이트만 걸어둔다 — 이 게이트는
클러스터링 기준이 아니라 "묶일 자격이 있는가"의 최소 조건이다.

클러스터의 지리적 경계는 멤버 좌표의 알파 셰이프(concave hull)로 근사해, 행정구역에
얽매이지 않는 자유형 도형으로 표현한다 (멤버가 1~2곳뿐이면 원형으로 대체).
"""

import math

import numpy as np
from scipy.spatial import ConvexHull, Delaunay
from sklearn.cluster import DBSCAN

import db
from agents.mbti_scorer import mbti_vector

MIN_STORES_FOR_CLUSTERING = 3   # DBSCAN min_samples — 이보다 적으면 클러스터로 보지 않음
_WALK_CAP_M = 500                # 도보권 상한 게이트(m) — 이보다 멀면 정체성이 같아도 묶지 않음
_MBTI_EPS = 0.08                 # MBTI 코사인 거리(0~1) 임계값 — 작을수록 더 엄격하게 묶음

_CIRCLE_RADIUS_M = 90            # 멤버 1~2곳뿐일 때 표시할 원형 버퍼 반경(m)
_HULL_PADDING_M = 50             # 헐이 멤버 좌표를 넉넉히 감싸도록 주는 여유(m)
_HULL_MAX_EDGE_M = 300           # 알파 셰이프에서 이 길이보다 긴 변은 잘라내 오목한 윤곽을 만듦
_HULL_MAX_RADIUS_M = 500         # 센트로이드로부터 헐 정점까지 최대 거리(m) — 이상치 안전장치
_OUTLIER_MAD_MULTIPLIER = 3.5    # 중앙값에서 이 배수(MAD 기준) 이상 떨어진 좌표는 이상치로 제외


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def _latlng_to_local_m(lat: float, lng: float, ref_lat: float, ref_lng: float) -> tuple[float, float]:
    """기준점(ref) 대비 (x, y) 미터 단위 평면 좌표로 근사 변환 (등장방형 투영)."""
    x = (lng - ref_lng) * 111_320 * math.cos(math.radians(ref_lat))
    y = (lat - ref_lat) * 111_320
    return x, y


def _local_m_to_latlng(x: float, y: float, ref_lat: float, ref_lng: float) -> list[float]:
    lat = ref_lat + y / 111_320
    lng = ref_lng + x / (111_320 * math.cos(math.radians(ref_lat)) or 1)
    return [lat, lng]


def _circle_polygon(lat: float, lng: float, radius_m: float = _CIRCLE_RADIUS_M, n: int = 32) -> list[list[float]]:
    """중심 좌표 기준 반경 radius_m 짜리 근사 원형 폴리곤 [[lat, lng], ...]."""
    points = []
    lat_rad = math.radians(lat)
    for i in range(n):
        angle = 2 * math.pi * i / n
        d_lat = (radius_m * math.cos(angle)) / 111_320
        d_lng = (radius_m * math.sin(angle)) / (111_320 * math.cos(lat_rad) or 1)
        points.append([lat + d_lat, lng + d_lng])
    return points


def _filter_outliers(xy: np.ndarray) -> np.ndarray:
    """중앙값 기준 MAD(median absolute deviation)로 이상치 좌표를 제거한다.
    잘못 지오코딩된 가게 1~2곳 때문에 헐 전체가 서울 전역만큼 커지는 것을 막기 위함."""
    if len(xy) < 4:
        return xy
    median = np.median(xy, axis=0)
    dist = np.linalg.norm(xy - median, axis=1)
    mad = np.median(dist)
    if mad < 1e-6:
        return xy
    keep = dist <= _OUTLIER_MAD_MULTIPLIER * mad
    filtered = xy[keep]
    return filtered if len(filtered) >= 3 else xy


def _alpha_shape_ring(xy: np.ndarray) -> np.ndarray | None:
    """
    들로네 삼각분할 후, 변 길이가 _HULL_MAX_EDGE_M보다 긴 삼각형을 잘라내
    남은 삼각형들의 경계(외곽 변)를 따라가는 오목한(concave) 윤곽선을 만든다.
    경계가 단순한 하나의 폐곡선이 아니면(구멍/여러 조각) None을 반환해 컨벡스 헐로 폴백한다.
    """
    if len(xy) < 4:
        return None
    try:
        tri = Delaunay(xy)
    except Exception:
        return None

    edge_count: dict[frozenset, int] = {}
    for simplex in tri.simplices:
        i, j, k = simplex
        e_ij = np.linalg.norm(xy[i] - xy[j])
        e_jk = np.linalg.norm(xy[j] - xy[k])
        e_ki = np.linalg.norm(xy[k] - xy[i])
        if max(e_ij, e_jk, e_ki) > _HULL_MAX_EDGE_M:
            continue
        for a, b in ((i, j), (j, k), (k, i)):
            key = frozenset((a, b))
            edge_count[key] = edge_count.get(key, 0) + 1

    boundary = [edge for edge, count in edge_count.items() if count == 1]
    if len(boundary) < 3:
        return None

    adjacency: dict[int, list[int]] = {}
    for edge in boundary:
        a, b = tuple(edge)
        adjacency.setdefault(a, []).append(b)
        adjacency.setdefault(b, []).append(a)

    if any(len(neighbors) != 2 for neighbors in adjacency.values()):
        return None  # 구멍이 있거나 여러 조각으로 쪼개짐 — 컨벡스 헐로 폴백

    start = next(iter(adjacency))
    ring_idx = [start]
    prev, current = None, start
    while True:
        n0, n1 = adjacency[current]
        nxt = n0 if n0 != prev else n1
        if nxt == start:
            break
        ring_idx.append(nxt)
        prev, current = current, nxt
        if len(ring_idx) > len(xy):
            return None  # 비정상 위상 — 안전하게 폴백

    return xy[ring_idx] if len(ring_idx) >= 3 else None


def _convex_hull_ring(xy: np.ndarray) -> np.ndarray | None:
    try:
        hull = ConvexHull(xy)
    except Exception:
        return None
    return xy[hull.vertices]


def _pad_ring(ring: np.ndarray) -> np.ndarray:
    """헐 윤곽선을 센트로이드 기준 바깥쪽으로 살짝 넓혀(_HULL_PADDING_M) 멤버 좌표를
    넉넉히 감싸 보이게 하고, 이상치로 인한 과도한 확장은 _HULL_MAX_RADIUS_M으로 제한한다."""
    center = ring.mean(axis=0)
    padded = []
    for point in ring:
        vec = point - center
        dist = float(np.linalg.norm(vec))
        if dist < 1e-6:
            direction = np.array([1.0, 0.0])
            dist = 1.0
        else:
            direction = vec / dist
        new_dist = min(dist + _HULL_PADDING_M, _HULL_MAX_RADIUS_M)
        padded.append(center + direction * new_dist)
    return np.array(padded)


def _hull_polygon(members: list[dict]) -> list[list[float]]:
    """
    멤버 좌표 분포를 감싸는 자유형(concave) 폴리곤을 동적으로 계산한다.
    (실제 가게 좌표 기반 — 하드코딩 아님. 매 호출마다 멤버 구성에 맞춰 다시 계산됨)
    """
    coords = [[m["lat"], m["lng"]] for m in members if m["lat"] is not None and m["lng"] is not None]
    if not coords:
        return []
    if len(coords) < 3:
        avg_lat = sum(c[0] for c in coords) / len(coords)
        avg_lng = sum(c[1] for c in coords) / len(coords)
        return _circle_polygon(avg_lat, avg_lng)

    ref_lat = sum(c[0] for c in coords) / len(coords)
    ref_lng = sum(c[1] for c in coords) / len(coords)
    xy = np.array([_latlng_to_local_m(lat, lng, ref_lat, ref_lng) for lat, lng in coords])
    xy = _filter_outliers(xy)

    if len(xy) < 3:
        avg = xy.mean(axis=0)
        return _circle_polygon(*_local_m_to_latlng(avg[0], avg[1], ref_lat, ref_lng))

    ring = _alpha_shape_ring(xy)
    if ring is None:
        ring = _convex_hull_ring(xy)
    if ring is None or len(ring) < 3:
        avg = xy.mean(axis=0)
        return _circle_polygon(*_local_m_to_latlng(avg[0], avg[1], ref_lat, ref_lng))

    ring = _pad_ring(ring)
    return [_local_m_to_latlng(x, y, ref_lat, ref_lng) for x, y in ring]


def _mbti_code_from_centroid(centroid: np.ndarray) -> str:
    from agents.mbti_scorer import _AXIS_META  # letter order reference
    code = ""
    for i, (axis, letter_left, letter_right, *_rest) in enumerate(_AXIS_META):
        left_val, right_val = centroid[i * 2], centroid[i * 2 + 1]
        code += letter_left if left_val >= right_val else letter_right
    return code


def _build_distance_matrix(stores: list[dict], vectors: np.ndarray) -> np.ndarray:
    """
    (n, n) 거리 행렬 — 도보권(_WALK_CAP_M) 밖의 쌍은 절대 묶이지 않도록 큰 값으로 마스킹하고,
    도보권 안의 쌍은 MBTI 코사인 거리(1 - cosine_similarity, 0~1)를 그대로 사용한다.
    즉 "묶일지 말지"는 MBTI 유사도가 결정하고, 거리는 최소 자격 조건일 뿐이다.
    """
    n = len(stores)
    ref_lat = sum(s["lat"] for s in stores) / n
    ref_lng = sum(s["lng"] for s in stores) / n
    xy = np.array([_latlng_to_local_m(s["lat"], s["lng"], ref_lat, ref_lng) for s in stores])

    geo_dist = np.linalg.norm(xy[:, None, :] - xy[None, :, :], axis=-1)

    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    normed = vectors / norms
    mbti_dist = 1.0 - normed @ normed.T
    mbti_dist = np.clip(mbti_dist, 0.0, None)

    BIG = 10.0  # eps(<=1)보다 항상 큰 값 — 도보권 밖은 사실상 이웃이 될 수 없게 함
    combined = np.where(geo_dist <= _WALK_CAP_M, mbti_dist, BIG)
    np.fill_diagonal(combined, 0.0)
    return combined


def cluster_all_stores(exclude_id: int | None = None) -> list[dict]:
    """
    도시 전역(구 무관) 가게들을 "도보권 안에서 MBTI 정체성이 비슷한 것끼리" 클러스터링한다.

    Returns:
        [{"members": [...], "centroid": np.ndarray, "centroid_mbti_code": str,
          "polygon": [[lat,lng],...]}]
        데이터가 부족하면 빈 리스트.
    """
    stores = db.list_all_stores(exclude_id=exclude_id)
    if len(stores) < MIN_STORES_FOR_CLUSTERING:
        return []

    vectors = np.array([mbti_vector({"axes": s["mbti_axes"]}) for s in stores])
    distance_matrix = _build_distance_matrix(stores, vectors)

    dbscan = DBSCAN(eps=_MBTI_EPS, min_samples=MIN_STORES_FOR_CLUSTERING, metric="precomputed")
    labels = dbscan.fit(distance_matrix).labels_

    clusters = []
    for label in sorted(set(labels) - {-1}):
        mask = labels == label
        members = [s for s, keep in zip(stores, mask) if keep]
        centroid = vectors[mask].mean(axis=0)
        clusters.append({
            "members": members,
            "centroid": centroid,
            "centroid_mbti_code": _mbti_code_from_centroid(centroid),
            "polygon": _hull_polygon(members),
        })
    return clusters


def recommend_top_clusters(store_id: int, n: int = 3) -> list[dict]:
    """
    특정 가게(store_id)와 도보권 안에 있으면서 MBTI 벡터가 가장 유사한 상권 클러스터 Top N을 반환한다.
    도보권 안에 클러스터링할 데이터가 부족하면 빈 리스트를 반환한다 (호출부에서 폴백 처리).
    """
    target = db.get_store(store_id)
    if target is None or target["lat"] is None or target["lng"] is None:
        return []

    clusters = cluster_all_stores(exclude_id=store_id)
    if not clusters:
        return []

    ref_lat, ref_lng = target["lat"], target["lng"]
    target_xy = np.array(_latlng_to_local_m(ref_lat, ref_lng, ref_lat, ref_lng))

    reachable = []
    for c in clusters:
        member_dists = [
            np.linalg.norm(target_xy - np.array(_latlng_to_local_m(m["lat"], m["lng"], ref_lat, ref_lng)))
            for m in c["members"] if m["lat"] is not None and m["lng"] is not None
        ]
        if member_dists and min(member_dists) <= _WALK_CAP_M:
            reachable.append(c)
    if not reachable:
        return []

    target_vec = np.array(mbti_vector({"axes": target["mbti_axes"]}))
    for c in reachable:
        c["similarity"] = _cosine_similarity(target_vec, c["centroid"])

    reachable.sort(key=lambda c: c["similarity"], reverse=True)
    return reachable[:n]
