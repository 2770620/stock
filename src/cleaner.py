"""数据清洗模块.

负责对原始日线数据进行去重、排序、停牌过滤与缺失值填充,
确保进入指标计算环节的数据是干净且连续的.
"""

from __future__ import annotations

import pandas as pd


def clean_daily(df: pd.DataFrame) -> pd.DataFrame:
    """清洗日线数据.

    步骤:
        1. 按 ``code / date`` 去重,保留首条
        2. 按日期升序排序
        3. 过滤成交量为 0 的停牌交易日
    """
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.drop_duplicates(subset=["code", "date"]).copy()
    df = df.sort_values(["code", "date"]).reset_index(drop=True)
    df = df[df["volume"].fillna(0) > 0].reset_index(drop=True)
    return df


def fill_missing(df: pd.DataFrame, method: str = "ffill") -> pd.DataFrame:
    """填充缺失值.

    Args:
        df: 输入数据
        method: ``ffill`` 前向填充 / ``bfill`` 后向填充 / ``zero`` 填 0
    """
    if df is None or df.empty:
        return df

    if method == "ffill":
        return df.ffill().dropna()
    if method == "bfill":
        return df.bfill().dropna()
    if method == "zero":
        return df.fillna(0)
    raise ValueError(f"unsupported fill method: {method}")


def trim_outliers(df: pd.DataFrame, col: str = "close", k: float = 5.0) -> pd.DataFrame:
    """按 Z-score 过滤异常值."""
    if df is None or df.empty or col not in df.columns:
        return df if df is not None else pd.DataFrame()
    z = (df[col] - df[col].mean()) / (df[col].std(ddof=0) + 1e-10)
    return df[z.abs() < k].reset_index(drop=True)
