"""Plotly 可视化模块.

统一使用科技感深色主题,提供 K 线图、相关性热力图、行业涨跌榜等
交互式可视化函数,所有函数返回 ``plotly.graph_objects.Figure`` 对象.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 科技感深色主题
THEME = {
    "paper_bgcolor": "#0f1419",
    "plot_bgcolor": "#0f1419",
    "font": {"color": "#c9d1d9", "family": "Consolas, monospace"},
    "xaxis_gridcolor": "#21262d",
    "yaxis_gridcolor": "#21262d",
}

# 颜色方案
COLORS = {
    "up": "#26a69a",       # 涨:青绿
    "down": "#ef5350",     # 跌:红
    "accent": "#58a6ff",   # 强调蓝
    "warning": "#f0b429",  # 警示黄
    "neutral": "#8b949e",
}


def _apply_theme(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        paper_bgcolor=THEME["paper_bgcolor"],
        plot_bgcolor=THEME["plot_bgcolor"],
        font=THEME["font"],
        xaxis_gridcolor=THEME["xaxis_gridcolor"],
        yaxis_gridcolor=THEME["yaxis_gridcolor"],
    )
    return fig


def kline(df: pd.DataFrame, title: str = "K 线图") -> go.Figure:
    """K 线 + 成交量子图,自动叠加 MA5 / MA20."""
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.75, 0.25],
        vertical_spacing=0.03,
    )

    fig.add_trace(go.Candlestick(
        x=df["date"],
        open=df["open"], high=df["high"], low=df["low"], close=df["close"],
        name="K线",
        increasing_line_color=COLORS["up"],
        decreasing_line_color=COLORS["down"],
        increasing_fillcolor=COLORS["up"],
        decreasing_fillcolor=COLORS["down"],
    ), row=1, col=1)

    if "ma5" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["date"], y=df["ma5"], name="MA5",
            line=dict(color=COLORS["accent"], width=1.2),
        ), row=1, col=1)

    if "ma20" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["date"], y=df["ma20"], name="MA20",
            line=dict(color=COLORS["warning"], width=1.2),
        ), row=1, col=1)

    bar_colors = [
        COLORS["up"] if c > o else COLORS["down"]
        for o, c in zip(df["open"], df["close"])
    ]
    fig.add_trace(go.Bar(
        x=df["date"], y=df["volume"], name="成交量",
        marker_color=bar_colors, showlegend=False,
    ), row=2, col=1)

    fig.update_layout(title=title, xaxis_rangeslider_visible=False)
    return _apply_theme(fig)


def correlation_heatmap(corr: pd.DataFrame, title: str = "个股相关性热力图") -> go.Figure:
    """相关性热力图,值域固定 [-1, 1]."""
    fig = go.Figure(go.Heatmap(
        z=corr.values,
        x=list(corr.columns),
        y=list(corr.index),
        colorscale=[
            [0.0, "#ef5350"],
            [0.5, "#1a1f29"],
            [1.0, "#26a69a"],
        ],
        zmin=-1, zmax=1,
        colorbar=dict(title="相关系数"),
    ))
    fig.update_layout(title=title)
    return _apply_theme(fig)


def industry_bar(df: pd.DataFrame, title: str = "行业涨跌榜") -> go.Figure:
    """行业涨跌榜水平条形图."""
    df = df.sort_values("pct_change")
    colors = [COLORS["up"] if v >= 0 else COLORS["down"] for v in df["pct_change"]]

    fig = go.Figure(go.Bar(
        x=df["pct_change"],
        y=df["industry"],
        orientation="h",
        marker_color=colors,
        text=df["pct_change"].round(2),
        textposition="outside",
    ))
    fig.update_layout(
        title=title,
        xaxis_title="涨跌幅(%)",
        yaxis_title="",
        height=max(400, 30 * len(df)),
    )
    return _apply_theme(fig)


def returns_line(df: pd.DataFrame, title: str = "累计收益率") -> go.Figure:
    """累计收益曲线."""
    cum = (1 + df["close"].pct_change().fillna(0)).cumprod() - 1
    fig = go.Figure(go.Scatter(
        x=df["date"], y=cum * 100,
        mode="lines",
        line=dict(color=COLORS["accent"], width=1.5),
        fill="tozeroy",
        fillcolor="rgba(88, 166, 255, 0.15)",
    ))
    fig.update_layout(title=title, xaxis_title="日期", yaxis_title="累计收益(%)")
    return _apply_theme(fig)
