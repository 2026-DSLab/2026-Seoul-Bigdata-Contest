"""
데이터 소스로부터 정보 수집 및 최종 분석 컨텍스트 통합 모듈
"""
import json
import os
from load_input import load_user_input
from data_loader import get_dong_code, get_store_data, get_population, get_sales
from kakao_api import get_kakao_data
from subway_station import get_nearest_station

BASE = os.path.dirname(os.path.abspath(__file__))


def parse_age(고객_연령층):
    """
    연령대 표기에서 숫자 부분만 파싱함
    """
    return 고객_연령층.replace("대", "")


def build_input(folder='test', filename='user_input5.json'):
    """
    개별 소스(입력, 카카오, 지하철, 공공데이터)를 통합하여 최종 분석 페이로드를 생성 및 저장함
    """
    user_input = load_user_input(folder, filename)

    구 = user_input['구']
    동 = user_input['동']
    상호명 = user_input['상호명']
    업종_카테고리 = user_input['업종_카테고리']
    업종_키워드 = user_input['업종_키워드']
    고객_연령층 = parse_age(user_input['주고객_연령층'])
    성별 = user_input['주고객_성별']
    
    행정동_코드 = get_dong_code(구, 동)

    # 지리 정보 및 경쟁 가구수 분석
    kakao = get_kakao_data(구, 동, 상호명, 업종_키워드)
    위도 = kakao['위도']
    경도 = kakao['경도']

    # 인접 인프라 분석
    subway = get_nearest_station(위도, 경도)

    # 공공데이터 통계 지표 결합
    store = get_store_data(행정동_코드, 업종_카테고리)
    population = get_population(행정동_코드, 고객_연령층, 성별)
    sales = get_sales(행정동_코드, 업종_카테고리, 고객_연령층, 성별)

    output = {
        "상호명": user_input['상호명'],
        "구": 구,
        "동": 동,
        "업종_카테고리": 업종_카테고리,
        "업종_키워드" : 업종_키워드,
        "운영_요일": user_input['운영_요일'],
        "오픈_시간": user_input['오픈_시간'],
        "마감_시간": user_input['마감_시간'],
        "시그니쳐_상품": user_input.get('시그니쳐_상품'),
        "분위기": user_input['분위기'],
        "고민_사항": user_input.get('고민_사항'),
        "주고객_연령층": user_input['주고객_연령층'],
        "주고객_성별": user_input['주고객_성별'],

        "반경_유사업종_점포수": kakao['반경_유사업종_점포수'],
        "가장_가까운_역": subway['가장_가까운_역'],
        "역까지_거리_m": subway['역까지_거리_m'],

        **store,
        **population,
        **sales,
    }

    output_filename = filename.replace("user_input", "output")
    output_path = os.path.join(BASE, "../../data", folder, "outputs", output_filename)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)

    print(f"[Done] {output_filename} 저장 완료")
    return output



if __name__ == "__main__":
    result = build_input()
    print(json.dumps(result, ensure_ascii=False, indent=4))