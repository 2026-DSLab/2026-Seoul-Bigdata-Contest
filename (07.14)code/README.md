# 🏙️ 상권더하기

서울 빅데이터 공모전 출품작 — LLM 멀티에이전트와 클러스터링으로 "우리 가게 MBTI"를 진단하고,
축적된 가게 데이터를 기반으로 상권을 재정의해 소상공인 간 공동 브랜딩을 지원하는 웹 앱입니다.

전체 아키텍처, 화면 구성, 실행 방법은 **[ARCHITECTURE.md](ARCHITECTURE.md)** 를 참고하세요.

## 빠른 시작

```bash
# 백엔드
pip install -r requirements.txt
cp .env.example .env            # LLM_PROVIDER, API 키 입력
python seed_demo_data.py        # 데모 클러스터 데이터 시드 (최초 1회)
uvicorn api.main:app --reload --port 8000

# 프론트엔드 (새 터미널)
cd frontend
cp .env.example .env            # VITE_KAKAO_JS_KEY 입력
npm install
npm run dev                     # http://localhost:5173
```

## 디렉토리 개요

- **`api/`**: FastAPI 앱 (화면에서 호출하는 REST 엔드포인트)
- **`agents/`**: LLM 멀티에이전트 (상권활성도/경쟁환경/업종추천/종합분석/MBTI/브랜딩)
- **`frontend/`**: React(Vite) 웹앱 — 홈 / MBTI 진단 / 진단 결과 / 상권 추천 / 우리 상권+ 지도
- **`data_loader.py`, `db.py`, `clustering.py`**: 공공데이터 조회, 누적 저장, MBTI 클러스터링
- **`preprocessing/`**: Raw 공공데이터 가공 및 전처리
- **`utils/`**: (레거시) CLI 파이프라인용 데이터 유틸리티
- **`main.py`, `pipeline.py`**: 기존 CLI 진입점 (단발 분석, 웹앱과 별개로 계속 사용 가능)
