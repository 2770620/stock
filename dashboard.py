"""Streamlit 交互式看板.

启动方式::

    streamlit run dashboard.py

页面包含:
    - 个股 K 线图 + 均线 + 成交量
    - 指标摘要卡片(最新价 / RSI / MACD柱)
    - 个股相关性热力图
    - 相似股票推荐
"""

from __future__ import annotations

import streamlit as st

from src.analyzer import correlation_matrix, summary
from src.indicators import attach_all
from src.recommender import recommend
from src.storage import list_codes, load_daily
from src.visualizer import correlation_heatmap, kline, returns_line


st.set_page_config(
    page_title="A股数据分析看板",
    page_icon="📊",
    layout="wide",
)

# 自定义深色科技感主题
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0f1419;
        color: #c9d1d9;
    }
    .stMarkdown, .stText, .stMetricLabel, .stMetricValue {
        color: #c9d1d9 !important;
    }
    .stMetricValue {
        font-family: 'Consolas', monospace;
    }
    section[data-testid="stSidebar"] {
        background-color: #161b22;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📊 A 股市场数据分析看板")
st.caption("数据来源: akshare · 本地 SQLite 存储 · Plotly 交互可视化")


@st.cache_data(ttl=60)
def get_codes() -> list[str]:
    return list_codes()


codes = get_codes()
if not codes:
    st.warning(
        "数据库为空,请先用命令行拉取数据:\n"
        "`python cli.py fetch --code 000001 --start 2024-01-01 --end 2024-12-31`"
    )
    st.stop()


# ---- 侧边栏设置 ----
st.sidebar.header("设置")
selected = st.sidebar.selectbox("选择股票", codes, index=0)
show_ma = st.sidebar.checkbox("显示均线", value=True)
show_vol = st.sidebar.checkbox("显示成交量", value=True)
window_hint = st.sidebar.slider("K 线最近交易日数", 30, 500, 250)


# ---- 主体内容 ----
df = load_daily(selected)
if df.empty:
    st.error(f"无法加载 {selected} 的数据,可能数据库被清空")
    st.stop()

df = attach_all(df)
df_view = df.tail(window_hint)


st.subheader(f"{selected} K 线图")
fig_k = kline(df_view, title=f"{selected} 近 {window_hint} 日 K 线")
if not show_ma:
    fig_k.data = tuple(t for t in fig_k.data if t.name not in ("MA5", "MA20"))
if not show_vol:
    fig_k.data = tuple(t for t in fig_k.data if t.name != "成交量")
st.plotly_chart(fig_k, use_container_width=True)


st.subheader("指标摘要")
info = summary(selected)
c1, c2, c3, c4 = st.columns(4)
c1.metric("最新收盘", f"{info.get('last_close', 0):.4f}")
c2.metric("RSI(14)", f"{df['rsi14'].iloc[-1]:.2f}")
c3.metric("MACD 柱", f"{df['macd_hist'].iloc[-1]:+.4f}")
c4.metric("最大回撤", f"{info.get('max_drawdown', 0) * 100:.2f}%")


st.divider()
st.subheader("累计收益率")
st.plotly_chart(returns_line(df_view, title=f"{selected} 累计收益率"), use_container_width=True)


st.divider()
st.subheader("个股相关性")
if len(codes) >= 2:
    corr = correlation_matrix(codes)
    if not corr.empty:
        st.plotly_chart(correlation_heatmap(corr), use_container_width=True)
    else:
        st.info("数据不足,无法计算相关性")
else:
    st.info("至少需要 2 支股票才能计算相关性")


st.divider()
st.subheader("相似股票推荐")
with st.expander("基于日收益率相关性的推荐"):
    top_n = st.slider("推荐数量", 1, 10, 5, key="rec_n")
    if st.button("生成推荐", key="rec_btn"):
        with st.spinner("计算中..."):
            recs = recommend(selected, codes, top_n=top_n)
        if recs:
            for i, (code, corr) in enumerate(recs, 1):
                sign = "📈 正相关" if corr >= 0 else "📉 负相关"
                st.write(f"{i}. **{code}**  corr=`{corr:+.4f}`  {sign}")
        else:
            st.warning("候选不足或数据重叠天数过少")


st.divider()
st.caption("提示: 修改 `data/stock.db` 后请按 R 刷新缓存")
