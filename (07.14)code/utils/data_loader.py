"""
공공데이터셋(CSV) 로드 및 데이터 추출 유틸리티
"""
import pandas as pd
import numpy as np
import os

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE, "../../data/preprocessed")

def load_data():
    """
    전처리된 점포, 유동인구, 매출 데이터를 통합 로드함
    """
    store = pd.read_csv(
        os.path.join(DATA_PATH, "상권분석_점포_행정동_전처리.csv"), encoding='utf-8')
    population = pd.read_csv(
        os.path.join(DATA_PATH, "상권분석_길단위인구_행정동_20254분기.csv"), encoding='utf-8')
    sales = pd.read_csv(
        os.path.join(DATA_PATH, "상권분석_추정매출_행정동_20254분기_v2.csv"), encoding='utf-8')
    return store, population, sales

def safe_rate(value):
    """
    비율값에 대한 이상치(inf/nan) 처리 및 퍼센트 변환을 수행함
    """
    if value is None or np.isinf(value) or np.isnan(value):
        return None
    return round(float(value) * 100, 1)


def get_dong_code(구, 동):
    """
    자치구 및 행정동 명칭을 기반으로 고유 행정동 코드를 반환함
    """
    store, _, _ = load_data()
    result = store[
        (store['자치구_코드_명'] == 구) &
        (store['행정동_코드_명'] == 동)
    ]
    if result.empty:
        raise ValueError(f"'{구} {동}' 에 해당하는 행정동을 찾을 수 없어요.")
    return int(result.iloc[0]['행정동_코드'])


def get_store_data(행정동_코드, 업종_카테고리):
    """
    특정 행정동의 업종별 점포 현황 및 통계 지표를 조회함
    """
    store, _, _ = load_data()

    업종_row = store[
        (store['행정동_코드'] == 행정동_코드) &
        (store['카테고리'] == 업종_카테고리)
    ]
    동_df = store[store['행정동_코드'] == 행정동_코드]

    if 업종_row.empty:
        raise ValueError(f"행정동 {행정동_코드} + 카테고리 {업종_카테고리} 데이터 없음")

    r = 업종_row.iloc[0]

    return {
        "카테고리_점포수": int(r['점포_수']),
        "카테고리_개업률": safe_rate(r['개업_율']),
        "카테고리_폐업률": safe_rate(r['폐업_률']),
        "카테고리_프랜차이즈_점포수": int(r['프랜차이즈_점포_수']),

        "동_전체_점포수": int(r['동_총_점포_수']),
        "동_개업률": safe_rate(동_df['개업_율'].mean()),
        "동_폐업률": safe_rate(동_df['폐업_률'].replace([np.inf, -np.inf], np.nan).mean()),
        "동_전체_프랜차이즈_점포수": int(동_df['프랜차이즈_점포_수'].sum()),
    }


def get_population(행정동_코드, 고객_연령층, 성별):
    """
    특정 행정동의 유동인구 분포 통계를 조회함
    """
    _, population, _ = load_data()

    df = population[population['행정동_코드'] == 행정동_코드]
    if df.empty:
        raise ValueError(f"행정동 {행정동_코드} 유동인구 데이터 없음")

    row = df.iloc[0]

    시간대_cols = {
        "00~06시": '시간대_00_06_유동인구_수',
        "06~11시": '시간대_06_11_유동인구_수',
        "11~14시": '시간대_11_14_유동인구_수',
        "14~17시": '시간대_14_17_유동인구_수',
        "17~21시": '시간대_17_21_유동인구_수',
        "21~24시": '시간대_21_24_유동인구_수',
    }
    시간대_값 = {k: row[v] for k, v in 시간대_cols.items()}
    최다_시간대 = max(시간대_값, key=시간대_값.get)
    최저_시간대 = min(시간대_값, key=시간대_값.get)

    성별_값 = {'남성': row['남성_유동인구_수'], '여성': row['여성_유동인구_수']}
    우세_성별 = max(성별_값, key=성별_값.get)
    열세_성별 = min(성별_값, key=성별_값.get)

    연령대_cols = {
        "10대": '연령대_10_유동인구_수',
        "20대": '연령대_20_유동인구_수',
        "30대": '연령대_30_유동인구_수',
        "40대": '연령대_40_유동인구_수',
        "50대": '연령대_50_유동인구_수',
        "60대이상": '연령대_60_이상_유동인구_수',
    }
    연령대_값 = {k: row[v] for k, v in 연령대_cols.items()}
    연령대_1위 = max(연령대_값, key=연령대_값.get)
    연령대_꼴등 = min(연령대_값, key=연령대_값.get)

    타겟_연령_col = f'연령대_{고객_연령층}_유동인구_수'
    타겟_성별_col = f'{성별}_유동인구_수'

    return {
        "최다_유동인구_시간대": 최다_시간대,
        "최다_유동인구_시간대_수": int(시간대_값[최다_시간대]),
        "최저_유동인구_시간대": 최저_시간대,
        "최저_유동인구_시간대_수": int(시간대_값[최저_시간대]),

        "유동인구_성별_우세": 우세_성별,
        "유동인구_성별_우세_수": int(성별_값[우세_성별]),
        "유동인구_성별_열세": 열세_성별,
        "유동인구_성별_열세_수": int(성별_값[열세_성별]),

        "유동인구_연령대_1위": 연령대_1위,
        "유동인구_연령대_1위_수": int(연령대_값[연령대_1위]),
        "유동인구_연령대_꼴등": 연령대_꼴등,
        "유동인구_연령대_꼴등_수": int(연령대_값[연령대_꼴등]),

        "타겟_연령대_유동인구": int(row[타겟_연령_col]),
        "타겟_성별_유동인구": int(row[타겟_성별_col]),
    }


def get_sales(행정동_코드, 업종_카테고리, 고객_연령층, 성별):
    """
    특정 행정동 및 업종의 매출 추정 지표를 조회함
    """
    _, _, sales = load_data()

    df = sales[
        (sales['행정동_코드'] == 행정동_코드) &
        (sales['카테고리'] == 업종_카테고리)
    ]
    if df.empty:
        raise ValueError(f"행정동 {행정동_코드} + 카테고리 {업종_카테고리} 매출 데이터 없음")

    row = df.iloc[0]

    시간대_cols = {
        "00~06시": '시간대_00~06_매출_금액',
        "06~11시": '시간대_06~11_매출_금액',
        "11~14시": '시간대_11~14_매출_금액',
        "14~17시": '시간대_14~17_매출_금액',
        "17~21시": '시간대_17~21_매출_금액',
        "21~24시": '시간대_21~24_매출_금액',
    }
    시간대_값 = {k: row[v] for k, v in 시간대_cols.items()}
    최다_시간대 = max(시간대_값, key=시간대_값.get)
    최저_시간대 = min(시간대_값, key=시간대_값.get)

    성별_값 = {'남성': row['남성_매출_금액'], '여성': row['여성_매출_금액']}
    우세_성별 = max(성별_값, key=성별_값.get)
    열세_성별 = min(성별_값, key=성별_값.get)

    연령대_cols = {
        "10대": '연령대_10_매출_금액',
        "20대": '연령대_20_매출_금액',
        "30대": '연령대_30_매출_금액',
        "40대": '연령대_40_매출_금액',
        "50대": '연령대_50_매출_금액',
        "60대이상": '연령대_60_이상_매출_금액',
    }
    연령대_값 = {k: row[v] for k, v in 연령대_cols.items()}
    연령대_1위 = max(연령대_값, key=연령대_값.get)
    연령대_꼴등 = min(연령대_값, key=연령대_값.get)

    타겟_연령_col = f'연령대_{고객_연령층}_매출_금액'
    타겟_성별_col = f'{성별}_매출_금액'

    return {
        "최다_매출_시간대": 최다_시간대,
        "최다_매출_시간대_금액": int(시간대_값[최다_시간대]),
        "최저_매출_시간대": 최저_시간대,
        "최저_매출_시간대_금액": int(시간대_값[최저_시간대]),

        "매출_성별_우세": 우세_성별,
        "매출_성별_우세_금액": int(성별_값[우세_성별]),
        "매출_성별_열세": 열세_성별,
        "매출_성별_열세_금액": int(성별_값[열세_성별]),

        "매출_연령대_1위": 연령대_1위,
        "매출_연령대_1위_금액": int(연령대_값[연령대_1위]),
        "매출_연령대_꼴등": 연령대_꼴등,
        "매출_연령대_꼴등_금액": int(연령대_값[연령대_꼴등]),

        "타겟_연령대_매출": int(row[타겟_연령_col]),
        "타겟_성별_매출": int(row[타겟_성별_col]),
    }



if __name__ == "__main__":
    dong_code = get_dong_code("강남구", "역삼1동")
    print("행정동_코드:", dong_code)
    print(get_store_data(dong_code, "외식/F&B"))
    print(get_population(dong_code, "20", "여성"))
    print(get_sales(dong_code, "외식/F&B", "20", "여성"))