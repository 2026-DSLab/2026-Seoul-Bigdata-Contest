1. Overview

Crowd-Aware Urban Navigation AI

서울시 공공데이터를 활용하여 특정 공간/지역 단위의 혼잡도를 예측하고, 사용자에게 최적의 방문 시간 및 대체 지역을 추천하는 멀티에이전트 기반 서비스

2. Problem

서울의 주요 공간(홍대, 성수, 축제, 팝업 등):

실시간 혼잡 정보 부족
방문 전 혼잡도 예측 불가
특정 시간대 과밀로 인한 경험 저하

특히 다음 공간은 예약 시스템이 존재하지 않음:

거리 상권
야시장 / 축제
팝업스토어
공원 및 공공 공간

결과
“가보고 나서야 붐비는지 아는 문제”

3. Solution

서울시 공공데이터를 기반으로, 1) 공간 단위 혼잡도 분석 2) 시간대별 혼잡 예측 3) 방문 최적 시간 추천 4) 대체 지역 추천

4. System Architecture (Multi-Agent)
4.1 Event Agent
역할: 혼잡 발생 요인 탐지
데이터:
서울시 문화행사 정보
사용 Feature:
event_location (위경도)
event_date
event_type (공연, 전시, 축제)
event_duration
Output:
event_intensity_score
4.2 Crowd Agent
역할: 현재 공간 혼잡도 추정
데이터:
서울 실시간 도시데이터
사용 Feature:
population_density
floating_population
time_slot
area_id (서울 주요 122개 지점 기준)
Output:
current_crowd_score
4.3 Flow Agent
역할: 유입/유출 기반 혼잡 변화 예측
데이터:
지하철 역별 승하차 인원
사용 Feature:
subway_inflow
subway_outflow
time_slot
station_proximity_to_area
핵심 Insight:
특정 시간대 유입 증가 → 혼잡 증가
Output:
incoming_flow_score
4.4 Hotspot Agent
역할: 혼잡 지역 탐지
입력:
Crowd Agent + Flow Agent + Event Agent
처리:
지역별 혼잡 점수 계산
Hotspot Score =
현재 혼잡도
+ 유입 증가율
+ 행사 영향도
Output:
hotspot_rank
4.5 Prediction Agent
역할: 미래 혼잡 예측
입력:
current_crowd_score
incoming_flow_score
event_intensity_score
Output:
predicted_crowd(t+1 ~ t+3 hour)
4.6 Decision Agent
역할: 사용자 의사결정 지원
Output:
방문 추천 시간
혼잡 회피 시간
대체 지역 추천

예시:

“홍대 18~21시 혼잡 (회피 권장)”
“성수 20시 이후 방문 추천”
“대체 지역: 합정”
5. Data Sources (Seoul Open Data)

사용 데이터:

서울시 문화행사 정보
서울 실시간 도시데이터
지하철 역별 승하차 인원
버스정류소 위치정보 (보조)
따릉이 대여소 정보 (접근성 보조)
6. Feature Engineering (핵심)
6.1 공간 단위 정의
서울 주요 지점 (122개 기준)
또는 행정동/핫플 지역 단위로 매핑
6.2 혼잡도 계산
Crowd Score =
정규화된 population_density
+ 시간대 가중치
6.3 유입량 계산
Flow Score =
(subway_inflow - subway_outflow)
× 거리 가중치
6.4 행사 영향도
Event Score =
행사 규모 × 시간 겹침 여부
6.5 최종 혼잡도
Final Crowd Score =
Crowd Score
+ Flow Score
+ Event Score
7. Key Insights
동일 지역도 시간대에 따라 혼잡도가 크게 변함
혼잡은 “현재 상태”보다 “유입 변화”가 더 중요
행사 데이터는 강력한 혼잡 트리거
지하철 유입은 혼잡의 선행 지표
8. MVP Scope

포함:

지역별 혼잡도 시각화
시간대별 혼잡 예측
Top-K 혼잡 지역 및 회피 추천

제외:

길찾기 기능
개인 위치 기반 추천
9. Business Model
B2C
혼잡 회피 추천 앱
프리미엄 기능 (시간 추천, 핫플 알림)
B2B
행사 운영 분석
상권 혼잡 리포트
10. Limitations
실시간 상권 매출 데이터 부재
공간 내부 혼잡 (매장 수준) 반영 불가
특정 이벤트 규모 추정 제한
11. Future Work
카드 매출 데이터 결합
GPS 기반 실제 이동 데이터 반영
공간 내부 혼잡도 추정 고도화
