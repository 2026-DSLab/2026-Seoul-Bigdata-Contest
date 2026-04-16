import requests
import os
from dotenv import load_dotenv
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()
KAKAO_API_KEY = os.getenv("KAKAO_API_KEY")
HEADERS = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}


def get_store_info(구, 동, 상호명):
    """
    상호명과 주소를 기반으로 위도, 경도 좌표 및 카테고리 코드를 추출 (Fallback 검색 적용)
    """
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    
    # 단계별 검색어 리스트 (구체적 -> 일반적)
    queries = [
        f"{구} {동} {상호명}",   # 1순위: 구 + 동 + 상호명
        f"{구} {상호명}",        # 2순위: 구 + 상호명 (동 정보 불일치 대비)
        f"{상호명}"              # 3순위: 상호명만 (지점명이 명확할 경우)
    ]

    result = None
    last_query = ""

    for query in queries:
        params = {"query": query, "size": 1}
        response = requests.get(url, headers=HEADERS, params=params, verify=False)
        response.raise_for_status()
        res_json = response.json()
        
        if res_json['documents']:
            result = res_json['documents'][0]
            print(f"[Kakao API] '{query}' 검색 성공")
            break
        last_query = query
        print(f"[Kakao API] '{query}' 검색 결과 없음, 다음 단계 시도...")

    if not result:
        raise ValueError(f"데이터 파일의 주소/상호명으로 장소를 찾을 수 없습니다. (구: {구}, 동: {동}, 상호명: {상호명})")

    위도 = float(result['y'])
    경도 = float(result['x'])
    category_code = result.get('category_group_code', '') or None

    return 위도, 경도, category_code


def get_nearby_category_count(위도, 경도, category_group_code, radius=500):
    """
    지정된 좌표 반경 내 특정 카테고리 그룹의 점포 총합을 조회
    """
    url = "https://dapi.kakao.com/v2/local/search/category.json"
    params = {
        "category_group_code": category_group_code,
        "x": 경도,
        "y": 위도,
        "radius": radius,
        "size": 1,
        "page": 1,
        "sort": "distance",
    }
    response = requests.get(url, headers=HEADERS, params=params, verify=False)
    response.raise_for_status()
    result = response.json()

    return result['meta']['total_count']


def get_nearby_keyword_count(위도, 경도, keyword, radius=200): # 반경 (200m단위로 현재 설정해놨습니다.)
    """
    지정된 좌표 반경 내 특정 키워드에 해당하는 점포 총합을 조회
    """
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    params = {
        "query": keyword,
        "x": 경도,
        "y": 위도,
        "radius": radius,
        "size": 1,
        "page": 1,
        "sort": "distance",
    }
    response = requests.get(url, headers=HEADERS, params=params, verify=False)
    response.raise_for_status()
    result = response.json()

    return result['meta']['total_count']


def get_kakao_data(구, 동, 상호명, 업종_키워드, radius=200):
    """
    위치 정보와 업종별 경쟁 점포 현황을 종합하여 반환
    """
    위도, 경도, category_code = get_store_info(구, 동, 상호명)

    if category_code:
        count = get_nearby_category_count(위도, 경도, category_code, radius)
    else:
        count = get_nearby_keyword_count(위도, 경도, 업종_키워드, radius)

    return {
        "위도": 위도,
        "경도": 경도,
        "반경_유사업종_점포수": count,
    }


if __name__ == "__main__":
    result = get_kakao_data("마포구", "서교동", "무신사 스탠다드 홍대")
    print(result)