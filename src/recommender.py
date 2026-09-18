"""基于相关性的简易推荐模块.

对目标股票,在候选池中找出日收益率相关系数绝对值最高的若干支股票,
作为同涨同跌的相似标的推荐.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from .analyzer import daily_returns
from .storage import load_daily

PathLike = Optional[object]


def recommend(
    code: str,
    candidates: list[str],
    top_n: int = 5,
    min_overlap: int = 30,
    db_path: PathLike = None,
) -> list[tuple[str, float]]:
    """基于相关性推荐相似股票.

    Args:
        code: 目标股票代码
        candidates: 候选股票代码列表
        top_n: 返回前 N 个
        min_overlap: 至少有 N 个交易日重叠才计算相关系数
        db_path: 数据库路径

    Returns:
        ``[(code, correlation), ...]`` 按相关性绝对值降序排列.
    """
    target = load_daily(code, db_path)
    if target.empty:
        return []

    target_ret = daily_returns(target)
    if target_ret.empty:
        return []

    scores: list[tuple[str, float]] = []
    for cand in candidates:
        if cand.strip().zfill(6) == code.strip().zfill(6):
            continue

        df = load_daily(cand, db_path)
        if df.empty:
            continue

        ret = daily_returns(df)
        if ret.empty:
            continue

        combined = pd.concat([target_ret.rename("t"), ret.rename("c")], axis=1, join="inner")
        if len(combined) < min_overlap:
            continue

        corr = combined["t"].corr(combined["c"])
        if pd.isna(corr):
            continue

        scores.append((cand.strip().zfill(6), float(corr)))

    scores.sort(key=lambda x: abs(x[1]), reverse=True)
    return scores[:top_n]
