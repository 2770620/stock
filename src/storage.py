"""SQLite 数据存储层.

所有持久化均落到本地 ``data/stock.db``;
同一交易日同一股票重复写入时自动去重,
保留最近一条记录.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional, Sequence

import pandas as pd

DEFAULT_DB_PATH = Path("data/stock.db")


_DAILY_SCHEMA = """
CREATE TABLE IF NOT EXISTS daily (
    code      TEXT NOT NULL,
    date      TEXT NOT NULL,
    open      REAL,
    close     REAL,
    high      REAL,
    low       REAL,
    volume    REAL,
    amount    REAL,
    pct_change REAL,
    turnover  REAL,
    PRIMARY KEY (code, date)
)
"""


def get_conn(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """获取 SQLite 连接,目录不存在则自动创建,并确保 daily 表已建."""
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.executescript(_DAILY_SCHEMA)
    return conn


def _dedupe(conn: sqlite3.Connection, table: str, keys: Sequence[str]) -> None:
    """按业务主键去重,保留最新写入."""
    key_cols = ", ".join(keys)
    conn.execute(
        f"""
        DELETE FROM {table}
        WHERE rowid NOT IN (
            SELECT MAX(rowid) FROM {table} GROUP BY {key_cols}
        )
        """,
    )
    conn.commit()


def save_daily(df: pd.DataFrame, db_path: Optional[Path] = None) -> int:
    """保存日线数据,自动去重,返回最终落库行数."""
    if df is None or df.empty:
        return 0
    with get_conn(db_path) as conn:
        df.to_sql("daily", conn, if_exists="append", index=False)
        _dedupe(conn, "daily", ["code", "date"])
        cur = conn.execute("SELECT COUNT(*) FROM daily WHERE code = ?", (df["code"].iloc[0],))
        return int(cur.fetchone()[0])


def load_daily(code: str, db_path: Optional[Path] = None) -> pd.DataFrame:
    """加载个股全部日线数据."""
    with get_conn(db_path) as conn:
        df = pd.read_sql(
            "SELECT * FROM daily WHERE code = ? ORDER BY date",
            conn,
            params=[code.strip().zfill(6)],
        )
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df


def load_many(codes: Sequence[str], db_path: Optional[Path] = None) -> dict[str, pd.DataFrame]:
    """批量加载多支股票."""
    result = {}
    for c in codes:
        df = load_daily(c, db_path)
        if not df.empty:
            result[c.strip().zfill(6)] = df
    return result


def list_codes(db_path: Optional[Path] = None) -> list[str]:
    """列出数据库中已存储的股票代码."""
    with get_conn(db_path) as conn:
        cur = conn.execute("SELECT DISTINCT code FROM daily ORDER BY code")
        return [r[0] for r in cur.fetchall()]


def clear(db_path: Optional[Path] = None) -> None:
    """清空数据库(谨慎使用)."""
    with get_conn(db_path) as conn:
        conn.execute("DELETE FROM daily")
        conn.commit()
