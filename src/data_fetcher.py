"""通过 akshare 获取 A 股市场数据.

提供个股日线行情与行业板块数据的统一获取接口,
返回字段已对齐内部命名规范,便于后续清洗与存储.
"""

from __future__ import annotations

from typing import Optional

import akshare as ak
import pandas as pd


# akshare 原始字段 -> 内部字段
_DAILY_FIELDS = {
    "日期": "date",
    "开盘": "open",
    "收盘": "close",
    "最高": "high",
    "最低": "low",
    "成交量": "volume",
    "成交额": "amount",
    "振幅": "amplitude",
    "涨跌幅": "pct_change",
    "涨跌额": "change",
    "换手率": "turnover",
}


def _normalize_code(code: str) -> str:
    """补全 6 位股票代码."""
    return code.strip().zfill(6)


def fetch_daily(code: str, start: str, end: str, adjust: str = "qfq") -> pd.DataFrame:
    """获取个股日线行情.

    Args:
        code: 股票代码,如 ``"000001"``
        start: 起始日期,格式 ``YYYY-MM-DD``
        end: 结束日期,格式 ``YYYY-MM-DD``
        adjust: 复权方式,``qfq`` 前复权 / ``hfq`` 后复权 / ``""`` 不复权

    Returns:
        标准化后的日线 DataFrame,字段包含
        ``code / date / open / close / high / low / volume / amount / pct_change / turnover``.
    """
    symbol = _normalize_code(code)
    raw = ak.stock_zh_a_hist(
        symbol=symbol,
        period="daily",
        start_date=start.replace("-", ""),
        end_date=end.replace("-", ""),
        adjust=adjust,
    )
    if raw.empty:
        return pd.DataFrame()

    df = raw.rename(columns=_DAILY_FIELDS)
    df["date"] = pd.to_datetime(df["date"])
    df["code"] = symbol

    keep = ["code", "date", "open", "close", "high", "low",
            "volume", "amount", "pct_change", "turnover"]
    keep = [c for c in keep if c in df.columns]
    return df[keep]


def fetch_industry_list() -> pd.DataFrame:
    """获取东方财富行业板块列表."""
    raw = ak.stock_board_industry_name_em()
    return raw.rename(columns={
        "板块名称": "industry",
        "板块代码": "code",
        "最新价": "price",
        "涨跌幅": "pct_change",
    })


def fetch_industry_constituents(industry: str) -> pd.DataFrame:
    """获取指定行业板块的成分股列表."""
    raw = ak.stock_board_industry_cons_em(symbol=industry)
    return raw.rename(columns={
        "代码": "code",
        "名称": "name",
        "最新价": "price",
        "涨跌幅": "pct_change",
    })
