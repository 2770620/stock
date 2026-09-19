"""指标计算单元测试."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.indicators import attach_all, ema, macd, ma, rsi


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """生成 100 个交易日的合成行情数据."""
    rng = np.random.default_rng(seed=42)
    n = 100
    close = 100.0 + np.cumsum(rng.standard_normal(n) * 0.5)
    return pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=n, freq="B"),
        "open": close - 0.3,
        "close": close,
        "high": close + 0.8,
        "low": close - 0.8,
        "volume": rng.integers(1_000, 10_000, n),
    })


def test_ma_length_and_nan(sample_df):
    result = ma(sample_df["close"], period=5)
    assert len(result) == len(sample_df)
    assert result.isna().sum() == 4


def test_ema_no_nan(sample_df):
    result = ema(sample_df["close"], period=12)
    assert result.isna().sum() == 0


def test_macd_components_length(sample_df):
    dif, dea, hist = macd(sample_df["close"])
    assert len(dif) == len(sample_df)
    assert len(dea) == len(sample_df)
    assert len(hist) == len(sample_df)


def test_rsi_in_range(sample_df):
    result = rsi(sample_df["close"], period=14)
    valid = result.dropna()
    assert (valid >= 0).all() and (valid <= 100).all()


def test_attach_all_columns(sample_df):
    out = attach_all(sample_df)
    expected = ["ma5", "ma20", "ema12", "dif", "dea", "macd_hist", "rsi14"]
    for col in expected:
        assert col in out.columns, f"missing column: {col}"


def test_attach_all_idempotent(sample_df):
    out1 = attach_all(sample_df)
    out2 = attach_all(out1)
    pd.testing.assert_frame_equal(out1, out2)


def test_empty_input():
    assert ma(pd.Series([], dtype=float), period=5).empty
    assert ema(pd.Series([], dtype=float), period=12).empty


def test_constant_series():
    s = pd.Series([100.0] * 50)
    dif, dea, hist = macd(s)
    assert (dif == 0).all()
    assert (dea == 0).all()
    assert (hist == 0).all()
