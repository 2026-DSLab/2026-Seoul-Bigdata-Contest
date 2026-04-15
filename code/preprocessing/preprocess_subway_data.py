import pandas as pd
from pathlib import Path

BASE      = Path(__file__).resolve().parent
RAW       = BASE / "../../data/raw"
PROCESSED = BASE / "../../data/preprocessed"
PROCESSED.mkdir(parents=True, exist_ok=True)

# ── 1. 파일 읽기 ──────────────────────────────────────────────────────────────
df_9 = pd.read_csv(
    RAW / "국가철도공단_수도권9호선_역위치_20250630.csv",
    encoding="cp949",
)
df_18 = pd.read_csv(
    RAW / "서울교통공사_1_8호선 역사 좌표(위경도) 정보_20250814.csv",
    encoding="cp949",
)

# ── 2. 컬럼 통일 ──────────────────────────────────────────────────────────────
df_9 = df_9.rename(columns={"선명": "호선"})[["호선", "역명", "위도", "경도"]]
df_9["호선"] = df_9["호선"].str.replace("호선", "").astype(int)

df_18 = df_18[["호선", "역명", "위도", "경도"]]

# ── 3. 합치기 ─────────────────────────────────────────────────────────────────
df_merged = pd.concat([df_18, df_9], ignore_index=True)

# ── 4. 환승역 처리 (역명 중복) ────────────────────────────────────────────────
dup_mask  = df_merged.duplicated(subset=["역명"], keep=False)
df_dup    = df_merged[dup_mask]
df_single = df_merged[~dup_mask]

df_transfer = (
    df_dup.groupby("역명", as_index=False)
    .agg(
        호선=("호선", lambda x: "+".join(str(v) for v in sorted(x))),
        위도=("위도", "mean"),
        경도=("경도", "mean"),
    )
)

df_merged = pd.concat([df_single, df_transfer], ignore_index=True)
df_merged["호선"] = df_merged["호선"].astype(str)

# ── 5. 정렬 & 저장 ────────────────────────────────────────────────────────────
df_merged = df_merged.sort_values("역명").reset_index(drop=True)
df_merged["역명"] = df_merged["역명"] + "역"
df_merged.to_csv(PROCESSED / "지하철역_위치정보.csv", index=False, encoding="utf-8-sig")
print(f"저장 완료 → data/preprocessed/지하철역_위치정보.csv  ({len(df_merged)}개 역)")
print(df_merged[df_merged["호선"].str.contains(r"\+", na=False)].to_string())  