"""分析逻辑模块.

封装日收益率、相关性矩阵、涨跌榜等业务分析函数,
所有读取都通过 :mod:`src.storage` 的统一接口落库后再读.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from .storage import DEFAULT_DB_PATH, load_daily, load_many

PathLike = Optional[object]  # 兼容 Path 类型


def daily_returns(df: pd.DataFrame) -> pd.Series:
    """计算日收益率,首行 NaN 被丢弃."""
    if df is None or df.empty:
        return pd.Series(dtype=float)
    return df["close"].pct_change().dropna()


def cumulative_returns(df: pd.DataFrame) -> pd.Series:
    """累计收益率序列."""
    if df is None or df.empty:
        return pd.Series(dtype=float)
    return (1 + df["close"].pct_change().fillna(0)).cumprod() - 1


def correlation_matrix(codes: list[str], db_path: PathLike = None) -> pd.DataFrame:
    """多支股票日收益率相关系数矩阵."""
    if not codes:
        return pd.DataFrame()

    data = load_many(codes, db_path)
    series_map = {code: daily_returns(df) for code, df in data.items()}
    if not series_map:
        return pd.DataFrame()

    rets = pd.DataFrame(series_map)
    return rets.corr()


def top_gainers(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """涨幅前 N 个交易日."""
    if df is None or df.empty:
        return pd.DataFrame()
    return df.nlargest(n, "pct_change")[["code", "date", "close", "pct_change"]]


def top_losers(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """跌幅前 N 个交易日."""
    if df is None or df.empty:
        return pd.DataFrame()
    return df.nsmallest(n, "pct_change")[["code", "date", "close", "pct_change"]]


def summary(code: str, db_path: PathLike = None) -> dict:
    """返回单只股票的统计摘要."""
    df = load_daily(code, db_path)
    if df.empty:
        return {}

    rets = daily_returns(df)
    return {
        "code": code,
        "count": int(len(df)),
        "first_date": df["date"].iloc[0].strftime("%Y-%m-%d") if not df.empty else "",
        "last_date": df["date"].iloc[-1].strftime("%Y-%m-%d") if not df.empty else "",
        "last_close": float(df["close"].iloc[-1]),
        "mean_return": float(rets.mean()) if not rets.empty else 0.0,
        "volatility": float(rets.std()) if not rets.empty else 0.0,
        "max_drawdown": float(_max_drawdown(df["close"])),
    }


def _max_drawdown(prices: pd.Series) -> float:
    """最大回撤."""
    cummax = prices.cummax()
    drawdown = (prices - cummax) / cummax
    return float(drawdown.min()) if not drawdown.empty else 0.0
