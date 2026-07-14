"""
db.py  —  분석 완료된 가게(좌표 + MBTI + 리포트)를 누적 저장하는 SQLite 저장소.

상권더하기의 핵심 자산: 소상공인이 분석을 완료할 때마다 이 테이블에 쌓이고,
clustering.py는 이 누적 데이터 위에서 상권 클러스터를 계산한다.
데모 시연을 위해 seed_demo_data.py로 초기 데이터를 채워둘 수 있지만,
이 모듈 자체는 INSERT만 수행하며 기존 행을 지우지 않는다.
"""

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime

_BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(_BASE, "stores.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS stores (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    상호명          TEXT NOT NULL,
    구              TEXT NOT NULL,
    동              TEXT NOT NULL,
    lat             REAL,
    lng             REAL,
    업종_카테고리   TEXT,
    mbti_code       TEXT,
    mbti_axes       TEXT,   -- JSON
    input_data      TEXT,   -- JSON
    reports         TEXT,   -- JSON (nullable, 데모 시드는 생략 가능)
    district_id     TEXT,
    district_label  TEXT,
    is_seed         INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_stores_gu ON stores(구);
CREATE INDEX IF NOT EXISTS idx_stores_district ON stores(district_id);
"""


@contextmanager
def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with _connect() as conn:
        conn.executescript(_SCHEMA)


def insert_store(
    상호명: str,
    구: str,
    동: str,
    lat: float | None,
    lng: float | None,
    업종_카테고리: str,
    mbti_code: str,
    mbti_axes: list,
    input_data: dict,
    reports: dict | None = None,
    is_seed: bool = False,
) -> int:
    with _connect() as conn:
        cur = conn.execute(
            """INSERT INTO stores
               (상호명, 구, 동, lat, lng, 업종_카테고리, mbti_code, mbti_axes,
                input_data, reports, is_seed, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                상호명, 구, 동, lat, lng, 업종_카테고리, mbti_code,
                json.dumps(mbti_axes, ensure_ascii=False),
                json.dumps(input_data, ensure_ascii=False),
                json.dumps(reports, ensure_ascii=False) if reports else None,
                1 if is_seed else 0,
                datetime.now().isoformat(),
            ),
        )
        return cur.lastrowid


def get_store(store_id: int) -> dict | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM stores WHERE id = ?", (store_id,)).fetchone()
        return _row_to_dict(row) if row else None


def list_all_stores(exclude_id: int | None = None) -> list[dict]:
    """구/동 무관 전체 가게 목록 (클러스터링은 행정구역이 아닌 도보거리+MBTI로 묶는다)."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM stores WHERE lat IS NOT NULL AND lng IS NOT NULL"
        ).fetchall()
    stores = [_row_to_dict(r) for r in rows]
    if exclude_id is not None:
        stores = [s for s in stores if s["id"] != exclude_id]
    return stores


def list_stores_by_district(district_id: str) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM stores WHERE district_id = ?", (district_id,)
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def assign_district(store_ids: list[int], district_id: str, district_label: str):
    with _connect() as conn:
        conn.executemany(
            "UPDATE stores SET district_id = ?, district_label = ? WHERE id = ?",
            [(district_id, district_label, sid) for sid in store_ids],
        )


def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    d["mbti_axes"] = json.loads(d["mbti_axes"]) if d["mbti_axes"] else []
    d["input_data"] = json.loads(d["input_data"]) if d["input_data"] else {}
    d["reports"] = json.loads(d["reports"]) if d["reports"] else None
    d["is_seed"] = bool(d["is_seed"])
    return d


init_db()
