"""技术指标计算模块.

包含 MA / EMA / MACD / RSI 四类常用指标,
对外暴露 :func:`attach_all` 一次性给 DataFrame 追加所有指标列.
"""

from __future__ import annotations

import pandas as pd


def ma(series: pd.Series, period: int = 5) -> pd.Series:
    """简单移动平均(SMA)."""
    return series.rolling(window=period, min_periods=period).mean()


def ema(series: pd.Series, period: int = 12) -> pd.Series:
    """指数移动平均(EMA)."""
    return series.ewm(span=period, adjust=False).mean()


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """MACD 指标.

    Args:
        series: 收盘价序列
        fast: 快线周期
        slow: 慢线周期
        signal: 信号线周期

    Returns:
        ``(dif, dea, hist)`` 三元组,分别对应 DIF、DEA 与 MACD 柱状线.
    """
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal, adjust=False).mean()
    hist = (dif - dea) * 2  # 国内惯例 MACD 柱状线 = (DIF - DEA) * 2
    return dif, dea, hist


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """RSI 相对强弱指标.

    使用 Wilder 平滑(等价于 ``ewm(alpha=1/period)``),与通达信等行情软件对齐.
    """
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0).ewm(alpha=1.0 / period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0.0)).ewm(alpha=1.0 / period, adjust=False).mean()
    rs = gain / loss.replace(0, 1e-10)
    return 100 - (100 / (1 + rs))


def attach_all(df: pd.DataFrame, col: str = "close") -> pd.DataFrame:
    """一次性追加 MA5 / MA20 / EMA12 / DIF / DEA / MACD / RSI 列."""
    if df is None or df.empty:
        return df if df is not None else pd.DataFrame()

    out = df.copy()
    close = out[col]

    out["ma5"] = ma(close, 5)
    out["ma20"] = ma(close, 20)
    out["ema12"] = ema(close, 12)

    dif, dea, hist = macd(close)
    out["dif"] = dif
    out["dea"] = dea
    out["macd_hist"] = hist

    out["rsi14"] = rsi(close, 14)
    return out
