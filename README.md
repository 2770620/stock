# A 股市场数据分析与可视化系统

> 基于 akshare 的 A 股市场数据分析工具,覆盖数据采集、技术指标计算、可视化与简易推荐。

## 功能概览

- **数据采集**：通过 akshare 拉取个股日线行情与行业板块数据
- **技术指标**：MA / EMA / MACD / RSI 等常用指标计算
- **可视化**：K 线图、成交量、行业涨跌榜、个股相关性热力图
- **简易推荐**：基于收益率相关性的相似个股推荐
- **交互看板**：Streamlit 单页应用 + 命令行入口

## 项目结构

```
stock-analysis/
├── README.md
├── requirements.txt
├── cli.py                # 命令行入口
├── dashboard.py          # Streamlit 看板
├── src/
│   ├── data_fetcher.py   # 数据采集模块
│   ├── storage.py        # SQLite 存储
│   ├── cleaner.py        # 数据清洗
│   ├── indicators.py     # 技术指标计算
│   ├── visualizer.py     # 可视化模块
│   ├── analyzer.py        # 分析逻辑
│   └── recommender.py    # 简易推荐
└── tests/
    └── test_indicators.py
```

## 安装

```bash
pip install -r requirements.txt
```

## 使用示例

```bash
# 1. 拉取个股数据
python cli.py fetch --code 000001 --start 2024-01-01 --end 2024-12-31

# 2. 计算指标(展示最近 20 个交易日)
python cli.py indicators --code 000001 --last 20

# 3. K 线可视化(系统默认浏览器打开)
python cli.py visualize --code 000001 --type kline

# 4. 累计收益曲线
python cli.py visualize --code 000001 --type returns

# 5. 多支股票相关性热力图
python cli.py visualize --code 000001 --type corr --codes 000002,600519,000858

# 6. 行业涨跌榜
python cli.py visualize --code 000001 --type industry

# 7. 相似股票推荐
python cli.py recommend --code 000001 --top-n 5

# 8. 统计摘要
python cli.py summary --code 000001

# 9. 启动交互看板
streamlit run dashboard.py
```

## 设计说明

- **数据来源**：东方财富(通过 akshare 间接接入),前复权日线
- **存储**：本地 SQLite,业务主键 `(code, date)` 自动去重
- **指标计算**：RSI 采用 Wilder 平滑,MACD 柱状线按国内惯例乘以 2,与主流行情软件对齐
- **可视化**：统一科技感深色主题,涨绿跌红(符合 A 股习惯)
- **推荐算法**：基于日收益率 Pearson 相关系数,要求至少 30 个交易日重叠

## 开发说明

按业务开发顺序划分为四个 Milestone:

1. **M1 数据采集模块** — akshare 接入与 SQLite 落库
2. **M2 数据清洗与指标计算** — pandas 清洗 + MA / MACD / RSI
3. **M3 可视化模块** — Plotly 交互图与行业分析
4. **M4 CLI 入口与交互看板** — argparse CLI + Streamlit 看板

详见 git 提交历史。

## License

MIT
