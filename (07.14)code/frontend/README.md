# 상권더하기 — 프론트엔드

React(Vite) + TypeScript 기반 웹앱. 모바일 뷰포트(430px) SPA로 구성되어 있으며,
[../ARCHITECTURE.md](../ARCHITECTURE.md) 에 전체 시스템 구조가 정리되어 있습니다.

## 실행

```bash
cp .env.example .env   # VITE_API_BASE_URL, VITE_KAKAO_JS_KEY 입력
npm install
npm run dev             # http://localhost:5173 (백엔드 :8000 이 먼저 떠 있어야 함)
```

## 화면 (src/pages/)

| 파일 | 라우트 | 설명 |
|---|---|---|
| `Home.tsx` | `/` | 검색바 + MBTI 진단 CTA |
| `Diagnosis.tsx` | `/diagnosis` | 가게 정보 입력 폼 → 백엔드 분석 요청 |
| `DiagnosisResult.tsx` | `/diagnosis/result` | MBTI 4글자 코드 + 축별 비교 그래프 |
| `Recommendations.tsx` | `/recommendations` | Top3 상권 클러스터 추천 → 확정 |
| `District.tsx` | `/district/:districtId` | 확정된 상권 지도(Kakao Maps) + 공동 브랜딩 전략 |

## 구조

- `api/` — 백엔드 fetch 래퍼(`client.ts`)와 타입 정의(`types.ts`)
- `state/AppState.tsx` — 진단 결과/선택 상권 등 화면 간 공유 상태 (Context)
- `components/` — TopBar, BottomNav, Card, ChipSelect, RangeSlider, MbtiProgressBar, KakaoMap
- `assets/logo-full.png` — 실제 서비스 로고 이미지
- `styles/tokens.css` — 색상/라운드/그림자 등 디자인 토큰
