"""命令行入口.

提供数据采集、指标计算、可视化与推荐四个子命令,
统一通过 ``argparse`` 解析参数.

示例::

    python cli.py fetch --code 000001 --start 2024-01-01 --end 2024-12-31
    python cli.py indicators --code 000001
    python cli.py visualize --code 000001 --type kline
    python cli.py recommend --code 000001 --top-n 5
    python cli.py list
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime

from src.analyzer import correlation_matrix, summary, top_gainers, top_losers
from src.cleaner import clean_daily
from src.data_fetcher import fetch_daily, fetch_industry_list
from src.indicators import attach_all
from src.recommender import recommend
from src.storage import list_codes, load_daily, save_daily
from src.visualizer import correlation_heatmap, industry_bar, kline, returns_line


def cmd_fetch(args: argparse.Namespace) -> None:
    """拉取并保存股票数据."""
    print(f"拉取 {args.code} 自 {args.start} 至 {args.end} ...")
    raw = fetch_daily(args.code, args.start, args.end, adjust=args.adjust)
    cleaned = clean_daily(raw)
    if cleaned.empty:
        print("未获取到数据,请检查代码或日期范围")
        sys.exit(1)
    saved = save_daily(cleaned)
    print(f"已保存,数据库中共有 {saved} 条 {args.code} 的日线记录")


def cmd_indicators(args: argparse.Namespace) -> None:
    """计算并展示技术指标."""
    df = load_daily(args.code)
    if df.empty:
        print(f"未找到 {args.code} 的数据,请先执行: python cli.py fetch --code {args.code}")
        sys.exit(1)
    df = attach_all(df)
    cols = ["date", "close", "ma5", "ma20", "dif", "dea", "macd_hist", "rsi14"]
    print(df[cols].tail(args.last).to_string(index=False))


def cmd_visualize(args: argparse.Namespace) -> None:
    """生成可视化图表."""
    df = load_daily(args.code)
    if df.empty:
        print(f"未找到 {args.code} 的数据")
        sys.exit(1)
    df = attach_all(df)

    if args.type == "kline":
        fig = kline(df, title=f"{args.code} 日K线")
    elif args.type == "returns":
        fig = returns_line(df, title=f"{args.code} 累计收益率")
    elif args.type == "corr":
        codes = [args.code]
        if args.codes:
            codes.extend(c.strip() for c in args.codes.split(","))
        else:
            codes = list_codes()
        if len(codes) < 2:
            print("相关性图至少需要 2 支股票,请用 --codes 指定或先 fetch 多支")
            sys.exit(1)
        corr = correlation_matrix(codes)
        fig = correlation_heatmap(corr, title="个股相关性热力图")
    elif args.type == "industry":
        df_ind = fetch_industry_list()
        fig = industry_bar(df_ind, title="行业涨跌榜")
    else:
        print(f"未知可视化类型: {args.type}")
        sys.exit(1)

    fig.show()


def cmd_recommend(args: argparse.Namespace) -> None:
    """推荐相似股票."""
    if args.codes:
        candidates = [c.strip() for c in args.codes.split(",")]
    else:
        candidates = list_codes()
    if args.code not in candidates:
        candidates.append(args.code)

    print(f"在 {len(candidates)} 支候选股票中查找与 {args.code} 相似的标的 ...")
    results = recommend(args.code, candidates, top_n=args.top_n)
    if not results:
        print("未找到符合条件的候选,可能数据不足或候选池太小")
        sys.exit(0)

    print(f"\n推荐结果(按相关性绝对值排序):")
    for i, (code, corr) in enumerate(results, 1):
        sign = "正相关" if corr >= 0 else "负相关"
        print(f"  {i}. {code}  corr={corr:+.4f}  ({sign})")


def cmd_summary(args: argparse.Namespace) -> None:
    """输出统计摘要."""
    info = summary(args.code)
    if not info:
        print(f"未找到 {args.code} 的数据")
        sys.exit(1)
    print(f"\n股票 {info['code']} 摘要:")
    print(f"  交易日数:    {info['count']}")
    print(f"  数据区间:    {info['first_date']} ~ {info['last_date']}")
    print(f"  最新收盘:    {info['last_close']:.4f}")
    print(f"  日均收益:    {info['mean_return'] * 100:.4f}%")
    print(f"  日波动率:    {info['volatility'] * 100:.4f}%")
    print(f"  最大回撤:    {info['max_drawdown'] * 100:.4f}%")


def cmd_top(args: argparse.Namespace) -> None:
    """涨跌幅前 N."""
    df = load_daily(args.code)
    if df.empty:
        print(f"未找到 {args.code} 的数据")
        sys.exit(1)
    print(f"\n涨幅前 {args.top_n}:")
    print(top_gainers(df, args.top_n).to_string(index=False))
    print(f"\n跌幅前 {args.top_n}:")
    print(top_losers(df, args.top_n).to_string(index=False))


def cmd_list(args: argparse.Namespace) -> None:
    """列出已存储股票."""
    codes = list_codes()
    print(f"已存储 {len(codes)} 支股票:")
    if codes:
        print("  " + ", ".join(codes))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stock-cli",
        description="A股市场数据分析与可视化工具",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_fetch = sub.add_parser("fetch", help="拉取并保存股票数据")
    p_fetch.add_argument("--code", required=True, help="股票代码,如 000001")
    p_fetch.add_argument("--start", default="2024-01-01", help="起始日期 YYYY-MM-DD")
    p_fetch.add_argument("--end", default=datetime.now().strftime("%Y-%m-%d"), help="结束日期 YYYY-MM-DD")
    p_fetch.add_argument("--adjust", default="qfq", choices=["qfq", "hfq", ""], help="复权方式")
    p_fetch.set_defaults(func=cmd_fetch)

    p_ind = sub.add_parser("indicators", help="计算技术指标")
    p_ind.add_argument("--code", required=True, help="股票代码")
    p_ind.add_argument("--last", type=int, default=20, help="展示最近 N 个交易日")
    p_ind.set_defaults(func=cmd_indicators)

    p_viz = sub.add_parser("visualize", help="生成可视化")
    p_viz.add_argument("--code", required=True, help="股票代码")
    p_viz.add_argument("--type", default="kline",
                        choices=["kline", "returns", "corr", "industry"],
                        help="可视化类型")
    p_viz.add_argument("--codes", help="相关性图的其他股票代码,逗号分隔")
    p_viz.set_defaults(func=cmd_visualize)

    p_rec = sub.add_parser("recommend", help="推荐相似股票")
    p_rec.add_argument("--code", required=True, help="目标股票代码")
    p_rec.add_argument("--codes", help="候选股票代码,逗号分隔;缺省使用数据库全部")
    p_rec.add_argument("--top-n", type=int, default=5, help="返回前 N 个推荐")
    p_rec.set_defaults(func=cmd_recommend)

    p_sum = sub.add_parser("summary", help="输出统计摘要")
    p_sum.add_argument("--code", required=True, help="股票代码")
    p_sum.set_defaults(func=cmd_summary)

    p_top = sub.add_parser("top", help="涨跌幅前 N")
    p_top.add_argument("--code", required=True, help="股票代码")
    p_top.add_argument("--top-n", type=int, default=10, help="前 N 名")
    p_top.set_defaults(func=cmd_top)

    p_list = sub.add_parser("list", help="列出已存储股票")
    p_list.set_defaults(func=cmd_list)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
