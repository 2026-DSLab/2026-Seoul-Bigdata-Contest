"""
지하철역 위치 데이터를 활용한 인접역 계산 유틸리티
"""
import pandas as pd
import os
from math import radians, sin, cos, sqrt, atan2

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE, "../../data/preprocessed")


def haversine(lat1, lon1, lat2, lon2):
    """
    Haversine 공식을 사용하여 두 좌표 간의 직선 거리(미터)를 산출함
    """
    R = 6371000  # 지구 반지름 (m)
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))


def get_nearest_station(위도, 경도):
    """
    입력 좌표 기준 반경 내 가장 인접한 지하철역 명칭 및 이격 거리를 반환함
    """
    df = pd.read_csv(
        os.path.join(DATA_PATH, "지하철역_위치정보.csv"), encoding='utf-8')

    df['거리'] = df.apply(
        lambda row: haversine(위도, 경도, row['위도'], row['경도']), axis=1)

    nearest = df.loc[df['거리'].idxmin()]

    return {
        "가장_가까운_역": nearest['역명'],
        "역까지_거리_m": int(nearest['거리']),
    }



if __name__ == "__main__":
    result = get_nearest_station(37.49916403482871, 127.0374209378493)
    print(result)