"""
data_loader.py  —  Stage 1: 데이터 조회 & 조합

사용자 입력(10개 필드)을 받아 카카오 API + 전처리 CSV 를 조합하여
input_example.json 스키마와 동일한 최종 데이터 dict를 반환합니다.

조회 순서:
  1. 카카오 로컬 API → 가게 좌표 (위도/경도)
  2. 지하철역 CSV    → 최근접 역·거리 (Haversine)
  3. 점포 CSV        → 반경 유사업종 수, 개·폐업률, 프랜차이즈 수
  4. 매출 CSV        → 시간대·성별·연령대 매출
  5. 유동인구 CSV    → 시간대·성별·연령대 유동인구
"""

import os
import math
import requests
import pandas as pd
import numpy as np
from dotenv import load_dotenv

load_dotenv()

# ── 경로 설정 ────────────────────────────────────────────────────
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.getenv(
    "DATA_DIR",
    os.path.join(_BASE_DIR, "..", "data", "preprocessed"),
)

# CSV 파일 경로
_STORE_CSV   = os.path.join(DATA_DIR, "상권분석_점포_행정동_전처리.csv")
_SALES_CSV   = os.path.join(DATA_DIR, "상권분석_추정매출_행정동_20254분기_v2.csv")
_PEOPLE_CSV  = os.path.join(DATA_DIR, "상권분석_길단위인구_행정동_20254분기.csv")
_SUBWAY_CSV  = os.path.join(DATA_DIR, "지하철역_위치정보.csv")

# 업종 카테고리 매핑 (실제 CSV 카테고리명 기준)
# CSV 카테고리: 외식/F&B, 식품/식재료, 생활서비스, 생활/홈인테리어,
#              의료/건강, 교육, 오락/여가, 숙박/부동산,
#              전문서비스, 전자/디지털, 자동차/이동수단, 패션/뷰티
CATEGORY_MAP = {
    "외식/F&B":        "외식/F&B",
    "식품/식재료":     "식품/식재료",
    "생활서비스":      "생활서비스",
    "생활/홈인테리어": "생활/홈인테리어",
    "의료/건강":       "의료/건강",
    "교육":            "교육",
    "오락/여가":       "오락/여가",
    "숙박/부동산":     "숙박/부동산",
    "전문서비스":      "전문서비스",
    "전자/디지털":     "전자/디지털",
    "자동차/이동수단": "자동차/이동수단",
    "패션/뷰티":       "패션/뷰티",
}

# 연령대 레이블 → 컬럼 접두사 매핑
AGE_LABEL_MAP = {
    "10대": "연령대_10",
    "20대": "연령대_20",
    "30대": "연령대_30",
    "40대": "연령대_40",
    "50대": "연령대_50",
    "60대이상": "연령대_60_이상",
    "60대": "연령대_60_이상",
}

GENDER_LABEL_MAP = {
    "남성": "남성",
    "여성": "여성",
}

# ── CSV 캐시 ─────────────────────────────────────────────────────
_cache: dict = {}

def _load_csv(path: str) -> pd.DataFrame:
    if path not in _cache:
        _cache[path] = pd.read_csv(path, encoding="utf-8-sig")
    return _cache[path]


# ════════════════════════════════════════════════════════════════
# 1. 카카오 로컬 API
# ════════════════════════════════════════════════════════════════

def _kakao_get_coords(store_name: str, gu: str, dong: str) -> tuple[float, float] | None:
    """
    카카오 키워드 검색으로 가게 좌표를 가져옵니다.
    Returns: (위도, 경도) 또는 None
    """
    api_key = os.getenv("KAKAO_API_KEY")
    if not api_key:
        print("[DataLoader] KAKAO_API_KEY 없음 → 좌표 조회 생략")
        return None

    query = f"{gu} {dong} {store_name}"
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {api_key}"}
    params = {"query": query, "size": 1}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=5)
        resp.raise_for_status()
        docs = resp.json().get("documents", [])
        if docs:
            lat = float(docs[0]["y"])
            lng = float(docs[0]["x"])
            return lat, lng
        print(f"[DataLoader] 카카오 검색 결과 없음: '{query}'")
        return None
    except Exception as e:
        print(f"[DataLoader] 카카오 API 오류: {e}")
        return None


# ════════════════════════════════════════════════════════════════
# 2. 지하철역 최근접 계산 (Haversine)
# ════════════════════════════════════════════════════════════════

def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """두 좌표 사이의 거리(m) 반환."""
    R = 6_371_000  # 지구 반지름 (m)
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _get_nearest_subway(lat: float, lng: float, gu: str) -> dict:
    """
    지하철역 CSV에서 가장 가까운 역과 거리를 반환합니다.
    Returns: {"역명": str, "거리_m": int}
    """
    df = _load_csv(_SUBWAY_CSV)

    # 같은 자치구 역 우선 필터 (없으면 전체)
    df_gu = df[df["시군구명"] == gu] if "시군구명" in df.columns else df
    if df_gu.empty:
        df_gu = df

    df_gu = df_gu.copy()
    df_gu["거리"] = df_gu.apply(
        lambda r: _haversine(lat, lng, r["위도"], r["경도"]), axis=1
    )
    nearest = df_gu.loc[df_gu["거리"].idxmin()]
    return {
        "역명": nearest["역명"],
        "거리_m": int(round(nearest["거리"])),
    }


# ════════════════════════════════════════════════════════════════
# 3. 점포 CSV 조회
# ════════════════════════════════════════════════════════════════

def _get_store_info(gu: str, dong: str, category: str) -> dict:
    """
    점포 CSV에서 해당 동의 업종·점포 정보를 집계합니다.
    실제 컬럼명: 자치구_코드_명, 행정동_코드_명, 개업_율, 폐업_률, 프랜차이즈_점포_수
    Returns: 점포 관련 필드 dict
    """
    df = _load_csv(_STORE_CSV)

    # 행정동 필터
    mask_dong = df["행정동_코드_명"].astype(str).str.contains(dong, na=False)
    mask_gu   = df["자치구_코드_명"].astype(str).str.contains(gu,   na=False)
    df_dong = df[mask_dong & mask_gu]

    # 전체 동 점포 수 (동_총_점포_수 컬럼 존재 시 첫 번째 값 사용, 없으면 합산)
    if "동_총_점포_수" in df_dong.columns and not df_dong.empty:
        dong_total = int(df_dong["동_총_점포_수"].iloc[0])
    else:
        dong_total = int(df_dong["점포_수"].sum()) if "점포_수" in df_dong.columns else 0

    dong_franchise  = int(df_dong["프랜차이즈_점포_수"].sum()) if "프랜차이즈_점포_수" in df_dong.columns else 0

    # 동 개업률 / 폐업률 (평균) — 컬럼명: 개업_율 / 폐업_률 -> 소수점이므로 * 100
    dong_open_rate  = round(float(df_dong["개업_율"].mean()) * 100,  1) if "개업_율"  in df_dong.columns and not df_dong.empty else 0.0
    dong_close_rate = round(float(df_dong["폐업_률"].mean()) * 100,  1) if "폐업_률"  in df_dong.columns and not df_dong.empty else 0.0

    # 카테고리 필터
    cat_mapped = CATEGORY_MAP.get(category, category)
    df_cat = df_dong[df_dong["카테고리"].astype(str) == cat_mapped] if "카테고리" in df_dong.columns else df_dong

    cat_total      = int(df_cat["점포_수"].sum())             if "점포_수"         in df_cat.columns else 0
    cat_franchise  = int(df_cat["프랜차이즈_점포_수"].sum())  if "프랜차이즈_점포_수" in df_cat.columns else 0
    cat_open_rate  = round(float(df_cat["개업_율"].mean()) * 100, 1) if "개업_율"  in df_cat.columns and not df_cat.empty else 0.0
    cat_close_rate = round(float(df_cat["폐업_률"].mean()) * 100, 1) if "폐업_률"  in df_cat.columns and not df_cat.empty else 0.0

    # 유사업종 반경 점포 수 (유사_업종_점포_수 컬럼 존재 시 합산, 없으면 카테고리 수)
    if "유사_업종_점포_수" in df_cat.columns and not df_cat.empty:
        similar_store_count = int(df_cat["유사_업종_점포_수"].mean())
    else:
        similar_store_count = cat_total

    return {
        "반경_유사업종_점포수":        similar_store_count,
        "카테고리_점포수":             cat_total,
        "카테고리_개업률":             cat_open_rate,
        "카테고리_폐업률":             cat_close_rate,
        "카테고리_프랜차이즈_점포수":  cat_franchise,
        "동_전체_점포수":              dong_total,
        "동_개업률":                   dong_open_rate,
        "동_폐업률":                   dong_close_rate,
        "동_전체_프랜차이즈_점포수":   dong_franchise,
        # 업종 매출 순위용 원본 DataFrame (pipeline에서 사용)
        "_df_dong_store":              df_dong,
    }


# ════════════════════════════════════════════════════════════════
# 4. 매출 CSV 조회
# ════════════════════════════════════════════════════════════════

def _get_sales_info(gu: str, dong: str, category: str,
                    target_age: str, target_gender: str) -> dict:
    """
    매출 CSV에서 해당 동·카테고리 매출 정보를 집계합니다.
    실제 컬럼명: 자치구_코드_명, 행정동_코드_명, 당월_매출_금액, 시간대_XX~XX_매출_금액 등
    Returns: 매출 관련 필드 dict
    """
    df = _load_csv(_SALES_CSV)

    # 행정동 필터
    mask_dong = df["행정동_코드_명"].astype(str).str.contains(dong, na=False)
    mask_gu   = df["자치구_코드_명"].astype(str).str.contains(gu,   na=False)
    df_dong = df[mask_dong & mask_gu]

    cat_mapped = CATEGORY_MAP.get(category, category)
    df_cat = df_dong[df_dong["카테고리"].astype(str) == cat_mapped] if "카테고리" in df_dong.columns else df_dong

    if df_cat.empty:
        df_cat = df_dong  # fallback

    # 시간대별 매출 금액 컬럼 — 실제: 시간대_06~11_매출_금액
    time_cols = {
        "06~11시": "시간대_06~11_매출_금액",
        "11~14시": "시간대_11~14_매출_금액",
        "14~17시": "시간대_14~17_매출_금액",
        "17~21시": "시간대_17~21_매출_금액",
        "21~24시": "시간대_21~24_매출_금액",
        "00~06시": "시간대_00~06_매출_금액",
    }

    time_sums = {k: int(df_cat[v].sum()) for k, v in time_cols.items() if v in df_cat.columns}

    if time_sums:
        max_time = max(time_sums, key=time_sums.get)
        min_time = min(time_sums, key=time_sums.get)
    else:
        max_time, min_time = "데이터없음", "데이터없음"
        time_sums = {max_time: 0}

    # 성별 매출 — 실제 컬럼명: 남성_매출_금액, 여성_매출_금액
    male_sales   = int(df_cat["남성_매출_금액"].sum())   if "남성_매출_금액"   in df_cat.columns else 0
    female_sales = int(df_cat["여성_매출_금액"].sum())   if "여성_매출_금액"   in df_cat.columns else 0

    if male_sales >= female_sales:
        gender_dominant, gender_dominant_val = "남성", male_sales
        gender_minor,    gender_minor_val    = "여성", female_sales
    else:
        gender_dominant, gender_dominant_val = "여성", female_sales
        gender_minor,    gender_minor_val    = "남성", male_sales

    # 연령대별 매출 — 실제 컬럼명: 연령대_10_매출_금액 ... 연령대_60_이상_매출_금액
    age_labels   = ["10대", "20대", "30대", "40대", "50대", "60대이상"]
    age_col_keys = ["연령대_10_매출_금액", "연령대_20_매출_금액", "연령대_30_매출_금액",
                    "연령대_40_매출_금액", "연령대_50_매출_금액", "연령대_60_이상_매출_금액"]
    age_sums = {}
    for label, key in zip(age_labels, age_col_keys):
        if key in df_cat.columns:
            age_sums[label] = int(df_cat[key].sum())

    if age_sums:
        age_top    = max(age_sums, key=age_sums.get)
        age_bottom = min(age_sums, key=age_sums.get)
    else:
        age_top, age_bottom = "30대", "10대"
        age_sums = {age_top: 0, age_bottom: 0}

    # 타겟 매출
    target_age_key = target_age if target_age in age_sums else age_top
    target_gender_val = (
        female_sales if target_gender in ("여성", "여자")
        else male_sales
    )

    return {
        "최다_매출_시간대":        max_time,
        "최다_매출_시간대_금액":   time_sums.get(max_time, 0),
        "최저_매출_시간대":        min_time,
        "최저_매출_시간대_금액":   time_sums.get(min_time, 0),
        "매출_성별_우세":          gender_dominant,
        "매출_성별_우세_금액":     gender_dominant_val,
        "매출_성별_열세":          gender_minor,
        "매출_성별_열세_금액":     gender_minor_val,
        "매출_연령대_1위":         age_top,
        "매출_연령대_1위_금액":    age_sums.get(age_top, 0),
        "매출_연령대_꼴등":        age_bottom,
        "매출_연령대_꼴등_금액":   age_sums.get(age_bottom, 0),
        "타겟_연령대_매출":        age_sums.get(target_age_key, 0),
        "타겟_성별_매출":          target_gender_val,
        # 업종 추천 에이전트용 원본
        "_df_dong_sales": df_dong,
    }


def _get_category_sales_ranking(df_dong_sales: pd.DataFrame) -> dict:
    """
    동 내 카테고리별 월매출 합계 → 최대/최소 업종 반환.
    실제 컬럼명: 당월_매출_금액
    Returns: {"최대_매출_업종": str, "최소_매출_업종": str, "순위": list}
    """
    if df_dong_sales.empty or "카테고리" not in df_dong_sales.columns:
        return {"최대_매출_업종": "N/A", "최소_매출_업종": "N/A", "순위": []}

    # 실제 컬럼명: 당월_매출_금액
    total_col = "당월_매출_금액" if "당월_매출_금액" in df_dong_sales.columns else None
    if not total_col:
        total_col = next(
            (c for c in df_dong_sales.columns
             if "매출_금액" in c and "시간대" not in c and "성별" not in c
             and "연령" not in c and "주중" not in c and "주말" not in c and "요일" not in c),
            None
        )
    if not total_col:
        return {"최대_매출_업종": "N/A", "최소_매출_업종": "N/A", "순위": []}

    grp = df_dong_sales.groupby("카테고리")[total_col].sum().sort_values(ascending=False)
    ranking = [{"순위": i + 1, "업종": k, "매출": int(v)} for i, (k, v) in enumerate(grp.items())]
    return {
        "최대_매출_업종": grp.index[0] if len(grp) > 0 else "N/A",
        "최소_매출_업종": grp.index[-1] if len(grp) > 0 else "N/A",
        "순위": ranking,
    }


# ════════════════════════════════════════════════════════════════
# 5. 유동인구 CSV 조회
# ════════════════════════════════════════════════════════════════

def _get_people_info(gu: str, dong: str, target_age: str, target_gender: str) -> dict:
    """
    유동인구 CSV에서 해당 동 유동인구 정보를 집계합니다.
    실제 컬럼명: 자치구_코드_명, 행정동_코드_명, 남성_유동인구_수, 시간대_06_11_유동인구_수 등
    Returns: 유동인구 관련 필드 dict
    """
    df = _load_csv(_PEOPLE_CSV)

    mask_dong = df["행정동_코드_명"].astype(str).str.contains(dong, na=False)
    mask_gu   = df["자치구_코드_명"].astype(str).str.contains(gu,   na=False)
    df_dong = df[mask_dong & mask_gu]
    if df_dong.empty:
        df_dong = df[mask_dong]

    # 시간대 유동인구 — 실제 컬럼명: 시간대_06_11_유동인구_수 (언더스코어 구분)
    time_cols_ppl = {
        "06~11시": "시간대_06_11_유동인구_수",
        "11~14시": "시간대_11_14_유동인구_수",
        "14~17시": "시간대_14_17_유동인구_수",
        "17~21시": "시간대_17_21_유동인구_수",
        "21~24시": "시간대_21_24_유동인구_수",
        "00~06시": "시간대_00_06_유동인구_수",
    }
    time_sums = {k: int(df_dong[v].sum()) for k, v in time_cols_ppl.items() if v in df_dong.columns}

    if time_sums:
        max_time = max(time_sums, key=time_sums.get)
        min_time = min(time_sums, key=time_sums.get)
    else:
        max_time, min_time = "데이터없음", "데이터없음"
        time_sums = {}

    # 성별 유동인구 — 실제 컬럼명: 남성_유동인구_수, 여성_유동인구_수
    male_pop   = int(df_dong["남성_유동인구_수"].sum())   if "남성_유동인구_수"   in df_dong.columns else 0
    female_pop = int(df_dong["여성_유동인구_수"].sum())   if "여성_유동인구_수"   in df_dong.columns else 0

    if male_pop >= female_pop:
        pop_dominant, pop_dominant_val = "남성", male_pop
        pop_minor,    pop_minor_val    = "여성", female_pop
    else:
        pop_dominant, pop_dominant_val = "여성", female_pop
        pop_minor,    pop_minor_val    = "남성", male_pop

    # 연령대 유동인구 — 실제 컬럼명: 연령대_10_유동인구_수 ... 연령대_60_이상_유동인구_수
    age_labels   = ["10대", "20대", "30대", "40대", "50대", "60대이상"]
    age_col_keys = ["연령대_10_유동인구_수", "연령대_20_유동인구_수", "연령대_30_유동인구_수",
                    "연령대_40_유동인구_수", "연령대_50_유동인구_수", "연령대_60_이상_유동인구_수"]
    age_sums = {}
    for label, key in zip(age_labels, age_col_keys):
        if key in df_dong.columns:
            age_sums[label] = int(df_dong[key].sum())

    if age_sums:
        age_top    = max(age_sums, key=age_sums.get)
        age_bottom = min(age_sums, key=age_sums.get)
    else:
        age_top, age_bottom = "30대", "10대"
        age_sums = {age_top: 0, age_bottom: 0}

    target_age_key   = target_age if target_age in age_sums else age_top
    target_gender_val = (
        female_pop if target_gender in ("여성", "여자")
        else male_pop
    )

    return {
        "최다_유동인구_시간대":        max_time,
        "최다_유동인구_시간대_수":     time_sums.get(max_time, 0),
        "최저_유동인구_시간대":        min_time,
        "최저_유동인구_시간대_수":     time_sums.get(min_time, 0),
        "유동인구_성별_우세":          pop_dominant,
        "유동인구_성별_우세_수":       pop_dominant_val,
        "유동인구_성별_열세":          pop_minor,
        "유동인구_성별_열세_수":       pop_minor_val,
        "유동인구_연령대_1위":         age_top,
        "유동인구_연령대_1위_수":      age_sums.get(age_top, 0),
        "유동인구_연령대_꼴등":        age_bottom,
        "유동인구_연령대_꼴등_수":     age_sums.get(age_bottom, 0),
        "타겟_연령대_유동인구":        age_sums.get(target_age_key, 0),
        "타겟_성별_유동인구":          target_gender_val,
    }


# ════════════════════════════════════════════════════════════════
# 메인 공개 함수
# ════════════════════════════════════════════════════════════════

def load_data(user_input: dict) -> dict:
    """
    사용자 입력을 받아 최종 데이터 dict를 반환합니다.

    Args:
        user_input: {
            "상호명": str, "구": str, "동": str,
            "업종_카테고리": str, "운영시간_요일": str,
            "시그니쳐_상품": str, "분위기": str, "고민_사항": str,
            "고객_연령층": str, "성별": str
        }

    Returns:
        input_example.json 스키마 + 업종 매출 순위 포함 dict
    """
    store_name = user_input.get("상호명", "알수없음")
    gu         = user_input.get("구", "-")
    dong       = user_input.get("동", "-")
    category   = user_input.get("업종_카테고리", "-")
    age        = user_input.get("주고객_연령층", user_input.get("고객_연령층", "30대"))
    gender     = user_input.get("주고객_성별", user_input.get("성별", "여성"))

    print(f"\n[DataLoader] 데이터 로딩 시작: {store_name} ({gu} {dong})")

    # 1. 카카오 좌표 조회
    print("[DataLoader] [1/5] 카카오 API 좌표 조회...")
    coords = _kakao_get_coords(store_name, gu, dong)

    # 2. 지하철역
    if coords:
        print("[DataLoader] [2/5] 지하철역 거리 계산...")
        subway_info = _get_nearest_subway(coords[0], coords[1], gu)
    else:
        subway_info = {"역명": "정보없음", "거리_m": -1}

    # 3. 점포 정보
    print("[DataLoader] [3/5] 점포 CSV 조회...")
    store_info = _get_store_info(gu, dong, category)

    # 4. 매출 정보
    print("[DataLoader] [4/5] 매출 CSV 조회...")
    sales_info = _get_sales_info(gu, dong, category, age, gender)

    # 5. 유동인구 정보
    print("[DataLoader] [5/5] 유동인구 CSV 조회...")  
    people_info = _get_people_info(gu, dong, age, gender)

    # 업종 매출 순위 (Stage 2 업종추천 에이전트용)
    category_ranking = _get_category_sales_ranking(sales_info.pop("_df_dong_sales"))
    store_info.pop("_df_dong_store", None)

    # 최종 결합
    result = {
        **user_input,
        "위도":                            coords[0] if coords else None,
        "경도":                            coords[1] if coords else None,
        "반경_유사업종_점포수":            store_info["반경_유사업종_점포수"],
        "가장_가까운_역":                  subway_info["역명"],
        "역까지_거리_m":                   subway_info["거리_m"],
        "카테고리_점포수":                 store_info["카테고리_점포수"],
        "카테고리_개업률":                 store_info["카테고리_개업률"],
        "카테고리_폐업률":                 store_info["카테고리_폐업률"],
        "카테고리_프랜차이즈_점포수":      store_info["카테고리_프랜차이즈_점포수"],
        "동_전체_점포수":                  store_info["동_전체_점포수"],
        "동_개업률":                       store_info["동_개업률"],
        "동_폐업률":                       store_info["동_폐업률"],
        "동_전체_프랜차이즈_점포수":       store_info["동_전체_프랜차이즈_점포수"],
        **people_info,
        **sales_info,
        # 업종 매출 순위 (에이전트 분석용 추가 필드)
        "동_카테고리_매출_최대_업종":      category_ranking["최대_매출_업종"],
        "동_카테고리_매출_최소_업종":      category_ranking["최소_매출_업종"],
        "동_카테고리_매출_순위":           category_ranking["순위"],
    }

    print("[DataLoader] 데이터 로딩 완료\n")
    return result
