# 🏙️ 상권더하기 — 아키텍처 문서

> **프로젝트**: 2026 서울 빅데이터 공모전
> **목적**: 점주(사용자)의 입력 + 서울시 공공데이터를 바탕으로 LLM 멀티에이전트가 "우리 가게 MBTI"를 진단하고,
> 축적된 가게 데이터를 클러스터링해 "상권 단위" 추천·공동 브랜딩까지 제공하는 웹 앱

---

## 0. 앱 사용 흐름 (STEP1~3)

```
STEP1. 우리 가게 MBTI 진단   →   STEP2. 우리 가게 상권 추천   →   STEP3. 우리 상권 공동 브랜딩
(진단 폼 입력 → 4축 MBTI 산출)   (MBTI 유사도로 Top3 상권 클러스터 추천)   (상권 확정 → 공동 브랜딩 전략 대시보드)
```

프론트엔드 화면 5개가 이 흐름에 그대로 대응한다: 홈 → MBTI 진단 폼 → MBTI 진단 결과 → 상권 추천 결과 → 우리 상권+ (지도 대시보드).

---

## 1. 전체 시스템 구조

```
┌───────────────────────────┐        HTTP/JSON        ┌────────────────────────────────┐
│  React (Vite) 프론트엔드   │  ──────────────────────▶ │   FastAPI 백엔드 (api/main.py)  │
│  localhost:5173           │  ◀────────────────────── │   localhost:8000                │
│  모바일 뷰포트(430px) SPA  │                          └───────────────┬──────────────────┘
└───────────────────────────┘                                          │
        │ Kakao Maps JS SDK (지도 렌더링)                                │
        ▼                                                              ▼
┌───────────────────────────┐   ┌──────────────────┐   ┌──────────────────────────────┐
│  Kakao Maps (지도 타일)     │   │  LLM (OpenAI/     │   │  data/preprocessed/*.csv      │
│                            │   │  Gemini)          │   │  (점포·매출·유동인구·지하철)   │
└───────────────────────────┘   └──────────────────┘   └──────────────────────────────┘
                                                                        │
                                                                        ▼
                                                          ┌──────────────────────────────┐
                                                          │  stores.db (SQLite)           │
                                                          │  분석 완료된 가게가 계속 쌓임   │
                                                          │  → 클러스터링의 원천 자산       │
                                                          └──────────────────────────────┘
```

- **기존 CLI 파이프라인(`main.py` / `pipeline.py`)은 그대로 유지**되며, `api/main.py`가 같은 `data_loader.py` / `agents/`를 재사용해 HTTP API로 감싼 것이다. CLI로 단발 분석만 하고 싶다면 `python main.py`도 여전히 동작한다.

---

## 2. 백엔드 파이프라인 (Phase 1~4)

```
┌─────────────────────────────────────────────────────────────────┐
│  Phase 1 — DataLoader (data_loader.py)                          │
│  ① 카카오 로컬 API  → 가게 좌표(위도/경도)                       │
│  ② 지하철역 CSV     → 최근접 역명 + 거리(m) [Haversine]          │
│  ③ 점포 CSV         → 반경 유사업종 수, 개·폐업률, 프랜차이즈    │
│  ④ 매출 CSV         → 시간대·성별·연령대 매출                    │
│  ⑤ 유동인구 CSV     → 시간대·성별·연령대 유동인구                │
└────────────────────────┬──────────────────────────────────────┘
                         │ enriched data dict (위도/경도 포함)
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Phase 2 — 분석 에이전트 3종 (asyncio 병렬, agents/stage2_*.py)  │
│  상권활성도 / 경쟁환경 / 업종 추천 → 보고서 3개                  │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Phase 3 — MBTI 산출 + 종합 분석 (신규)                          │
│  · agents/mbti_scorer.py  : 4축(D/N,U/F,T/L,M/G) 구조화 JSON 산출│
│    - D/N, T/L, M/G : 정량 데이터 규칙 기반 계산 (LLM 미사용)     │
│    - U/F           : 분위기·시그니처상품 텍스트를 LLM에 짧게 질의│
│  · agents/stage3_synthesis.py : 3개 보고서 통합 인사이트         │
│    (MBTI는 여기서 다시 만들지 않음 — mbti_scorer가 단일 진실源)  │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Phase 3.5 — 누적 저장 (db.py, SQLite stores 테이블)             │
│  분석 완료된 가게(좌표+MBTI+원본데이터+보고서)를 INSERT           │
│  → 소상공인이 합류할수록 쌓이는 클러스터링의 원천 자산            │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Phase 4 — MBTI 클러스터링 + 상권 브랜딩                         │
│  · clustering.py         : 같은 구(區) 내 가게들의 MBTI 8차원    │
│    벡터를 KMeans로 묶고, 신규 가게와 코사인 유사도 Top3 클러스터 │
│    추천 (멤버 좌표 convex hull → 지도 폴리곤 좌표)               │
│  · agents/branding_agent.py : 클러스터(가게 그룹) 단위로         │
│    상권 정체성 레이블·태그·공동 브랜딩 전략을 JSON으로 산출      │
│  · 사용자가 Top3 중 하나를 선택(join-district)하면 해당 클러스터 │
│    멤버 전원이 같은 district_id로 확정됨                         │
└─────────────────────────────────────────────────────────────────┘
```

### MBTI 4축 정의

| 축 | 의미 | 계산 방식 |
|---|---|---|
| D(주간형) / N(야간형) | 언제 강한 상권인가 | 최다 유동인구/매출 시간대가 주간(06~17시)인지 야간(17~06시)인지 |
| U(실용형) / F(감성형) | 왜 선택받는가 | 분위기·시그니처상품·고민사항 텍스트를 LLM이 짧게 판정 |
| T(통과형) / L(로컬형) | 누구에게 기대는가 | 역세권 거리 + 반경 유사업종 밀도 |
| M(대중형) / G(틈새형) | 어떻게 경쟁하는가 | 카테고리 내 프랜차이즈 점포 비율 |

---

## 3. FastAPI 엔드포인트 (`api/main.py`)

| Method | Path | 설명 | 대응 화면 |
|---|---|---|---|
| POST | `/api/analyze` | 사용자 입력 → Phase1~3.5 실행, DB 저장 | MBTI 진단 폼 → 결과 |
| GET | `/api/stores/{id}` | 저장된 가게 원본 조회 | - |
| GET | `/api/stores/{id}/recommendations` | Phase4 클러스터링 → Top3 상권 추천 | 상권 추천 결과 |
| POST | `/api/stores/{id}/join-district` | Top3 중 하나 확정 | 상권 추천 결과 → 우리 상권+ |
| GET | `/api/districts/{district_id}` | 확정된 상권의 지도/브랜딩 데이터 | 우리 상권+ |
| GET | `/api/health` | 헬스체크 | - |

---

## 4. 디렉토리 구조

```
2026-Seoul-Bigdata-Contest/
├── (07.14)code/                        ← 이 문서가 있는 루트
│   ├── .env / .env.example             ← 백엔드 환경변수
│   ├── requirements.txt
│   ├── main.py / pipeline.py           ← CLI 진입점 (기존, 그대로 유지)
│   ├── data_loader.py                  ← Stage1: 데이터 조회 & 조합 (위도/경도 포함)
│   ├── db.py                           ← SQLite stores 테이블 (누적 저장소)
│   ├── clustering.py                   ← KMeans 기반 Top3 상권 클러스터링
│   ├── seed_demo_data.py               ← 데모용 가게 15곳 시드 스크립트
│   ├── stores.db                       ← SQLite DB 파일 (실행 시 자동 생성)
│   ├── api/
│   │   ├── __init__.py
│   │   └── main.py                     ← FastAPI 앱 (엔드포인트 6종)
│   ├── agents/
│   │   ├── base_agent.py               ← Gemini/OpenAI 공통 LLM 래퍼
│   │   ├── mbti_scorer.py              ← 4축 MBTI 구조화 산출 (신규)
│   │   ├── branding_agent.py           ← 클러스터 단위 상권 브랜딩 (신규)
│   │   ├── stage2_commercial.py        ← 상권활성도 에이전트
│   │   ├── stage2_competition.py       ← 경쟁환경 에이전트
│   │   ├── stage2_industry.py          ← 업종 추천 에이전트
│   │   ├── stage3_synthesis.py         ← 종합 분석 에이전트
│   │   └── stage3_naming.py            ← (레거시) 개별 가게 상권 작명
│   ├── output/                         ← CLI 실행 결과 JSON (자동 생성)
│   └── frontend/                       ← React(Vite) 웹앱
│       ├── .env / .env.example         ← 프론트 환경변수
│       ├── src/
│       │   ├── api/                    ← client.ts(fetch 래퍼), types.ts
│       │   ├── state/AppState.tsx      ← 진단결과/선택상권 등 전역 상태
│       │   ├── components/             ← TopBar, BottomNav, Card, ChipSelect,
│       │   │                             RangeSlider, MbtiProgressBar, KakaoMap
│       │   ├── pages/                  ← Home, Diagnosis, DiagnosisResult,
│       │   │                             Recommendations, District
│       │   ├── assets/logo-full.png    ← PDF에서 받은 실제 로고 이미지
│       │   └── styles/tokens.css       ← 디자인 토큰(색상/라운드/그림자)
│       └── package.json
│
├── data/
│   ├── preprocessed/                   ← 전처리 완료 CSV (점포/매출/유동인구/지하철)
│   └── raw/                            ← 원본 공공데이터
└── ...
```

---

## 5. 프론트엔드 화면 구성

| 라우트 | 화면 | 설명 |
|---|---|---|
| `/` | 홈 | 검색바 + MBTI 진단 CTA + (진단 완료 시) 결과 요약 카드 |
| `/diagnosis` | MBTI 진단 폼 | 기본정보 / 추가정보 / 함께 성장하기 3섹션 폼 → `POST /api/analyze` |
| `/diagnosis/result` | MBTI 진단 결과 | 4글자 코드 + 축별 설명 + 비교 막대그래프 |
| `/recommendations` | 상권 추천 결과 | Top3 클러스터 카드 → 선택 → `POST /join-district` |
| `/district/:districtId` | 우리 상권+ | Kakao 지도(클러스터 폴리곤+멤버 핀) + 공동 브랜딩 전략 |

상태 관리는 전역 Context(`state/AppState.tsx`) 하나로 충분한 규모라 Redux 등은 도입하지 않았다.

---

## 6. LLM 제공자 분기

```
.env
└── LLM_PROVIDER=gemini  또는  openai
          │
          ▼
   agents/base_agent.py
   ├── gemini  → google-generativeai SDK (gemini-2.0-flash)
   └── openai  → openai SDK (gpt-4o-mini)
          │
          ▼
   generate(system_prompt, user_message) → str
   (Stage2/3 에이전트, mbti_scorer의 U/F축, branding_agent 모두 동일 인터페이스 사용)
```

---

## 7. 실행 방법

```bash
cd "(07.14)code"

# 1. 백엔드 의존성 설치 + 환경변수
pip install -r requirements.txt
cp .env.example .env   # OPENAI_API_KEY 또는 GEMINI_API_KEY, KAKAO_API_KEY 입력

# 2. (최초 1회) 데모 클러스터 시드 — 마포구 서교동에 가게 15곳 생성
python seed_demo_data.py

# 3. 백엔드 실행 (:8000)
uvicorn api.main:app --reload --port 8000

# 4. 프론트엔드 (별도 터미널)
cd frontend
cp .env.example .env   # VITE_KAKAO_JS_KEY 입력 (Kakao Maps JS 키, REST 키와 다름)
npm install
npm run dev             # http://localhost:5173

# (참고) 기존 CLI 단발 실행도 그대로 가능
python main.py --example
```

---

## 8. 환경변수 목록

### 백엔드 (`(07.14)code/.env`)

| 변수명 | 설명 | 필수 여부 |
|--------|------|----------|
| `LLM_PROVIDER` | `gemini` 또는 `openai` | 필수 |
| `GEMINI_API_KEY` / `GEMINI_MODEL` | Gemini 사용 시 | LLM_PROVIDER=gemini일 때 |
| `OPENAI_API_KEY` / `OPENAI_MODEL` | OpenAI 사용 시 | LLM_PROVIDER=openai일 때 |
| `KAKAO_API_KEY` | 카카오 로컬 REST API 키 (가게 좌표 조회용) | 선택 (없으면 좌표 없이 진행) |
| `DATA_DIR` | 전처리 데이터 폴더 경로 | 선택 (기본: `../data/preprocessed`) |

### 프론트엔드 (`(07.14)code/frontend/.env`)

| 변수명 | 설명 | 필수 여부 |
|--------|------|----------|
| `VITE_API_BASE_URL` | FastAPI 백엔드 주소 | 선택 (기본: `http://localhost:8000`) |
| `VITE_KAKAO_JS_KEY` | Kakao Maps **JavaScript** 키 (REST 키와 발급 경로 다름) | 지도 화면(`/district/:id`) 사용 시 필수 |

---

## 9. 알려진 제약사항

- **클러스터링은 같은 구(區)에 가게가 최소 3곳 이상 쌓여야 동작한다.** 시드 스크립트로 마포구 서교동에 15곳을 미리 채워두었고, 이후 실사용자가 `/api/analyze`를 호출할 때마다 같은 `stores.db`에 실제 데이터로 계속 누적된다.
- 시드 데이터(`seed_demo_data.py`)는 실제 카카오/CSV 조회 없이 손으로 구성한 대표값이며 `is_seed=1`로 표시된다. 데모 목적이며 실제 매출/유동인구를 대표하지 않는다.
- `agents/stage3_naming.py`(개별 가게 상권 작명)는 초기 CLI 파이프라인의 유산으로 남아있으나, 앱 화면에서는 클러스터 단위인 `branding_agent.py`가 그 역할을 대체한다.
