"""筛选沪深 300 权重前十股票，并计算其 20 日年化波动率。"""

from __future__ import annotations

import math
import os
import sys
import warnings
from datetime import date, timedelta
from pathlib import Path

import akshare as ak
import pandas as pd
import tushare as ts
from dotenv import load_dotenv


load_dotenv()
pro = ts.pro_api(os.getenv("TUSHARE_TOKEN"))


PROJECT_ROOT = Path(__file__).resolve().parent#获取根目录路径
OUTPUT_PATH = PROJECT_ROOT / "outputs" / "hs300_top10_volatility.xlsx"#结果保存在哪


def get_hs300_top10_by_weight() -> pd.DataFrame:#函数返回的是一个dataframe，是给人看的
    """获取沪深300成分股中权重最大的Top 10。

    使用中证指数官方权重数据，比拉全市场行情更快更稳。
    权重排名与市值排名基本一致（沪深300按流通市值加权）。

    Returns:
        包含 code, name, weight 三列的 DataFrame，按权重降序排列。

    Raises:
        RuntimeError: 当akshare接口调用失败时抛出。
    """
    print("正在获取沪深300成分股权重（中证指数官方数据）...")
    try:
        weights = ak.index_stock_cons_weight_csindex(symbol="000300")
    except Exception as exc:
        raise RuntimeError(f"获取沪深300权重失败：{exc}") from exc

    # 只保留需要的列并重命名（成分券代码→code，成分券名称→name，权重→weight）
    weights = weights[["成分券代码", "成分券名称", "权重"]].rename(
        columns={"成分券代码": "code", "成分券名称": "name", "权重": "weight"}
    )

    # 按权重降序取Top 10
    top10 = weights.sort_values("weight", ascending=False).head(10).reset_index(drop=True)#按照权重降序选取排前10的成分股，并且重置序号
    print("✅ 已选出权重最大的Top 10股票")
    return top10


def get_stock_daily(code: str, lookback_days: int = 120) -> pd.DataFrame:
    """获取指定股票过去N天的日线数据（用Tushare接口，稳定可靠）。

    Args:
        code: 6位股票代码，如 "600519"
        lookback_days: 回溯天数（自然日），默认120（保证覆盖60+个交易日）

    Returns:
        包含 trade_date, close 列的 DataFrame，按日期升序排列。

    Raises:
        RuntimeError: 当Tushare接口失败或返回空数据时抛出。
    """
    from datetime import date, timedelta

    end_date = date.today().strftime("%Y%m%d")#获取今天日期并且把日期对象转化为指定格式的字符串，%Y是年，%m是月，不够补0，%d是日，不够补0
    start_date = (date.today() - timedelta(days=lookback_days)).strftime("%Y%m%d")#计算出120天前的日期

    # Tushare的股票代码需要带交易所后缀
    if code.startswith("6"):#根据股票代码开头第一个数字判断是上交所还是其他市场的股票
        ts_code = f"{code}.SH"  # 上交所
    else:
        ts_code = f"{code}.SZ"  # 深交所（0/3开头）

    try:
        df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)#获取日线数据，比如开盘、最高、最低、成交量
    except Exception as exc:
        raise RuntimeError(f"获取股票 {code} 日线数据失败：{exc}") from exc#报运行错误，from exc是为了返回真实的错误

    if df.empty:
        raise RuntimeError(f"股票 {code} 未返回任何日线数据")

    # Tushare返回的是降序（最新的在前），要按日期升序排列
    df = df.sort_values("trade_date").reset_index(drop=True)#按照日期升序进行排序

    return df[["trade_date", "close"]]


def calculate_annualized_volatility(
    prices: pd.Series, window: int = 20
) -> float:
    """根据收盘价计算最近一期滚动年化波动率。

    Args:
        prices: 按时间升序排列的股票收盘价序列。
        window: 日收益率滚动标准差窗口，默认为 20 个交易日。

    Returns:
        最近一期年化波动率，以小数表示，例如 0.25 表示 25%。

    Raises:
        ValueError: 窗口无效、有效价格不足或无法计算波动率时抛出。
    """
    if window <= 1:
        raise ValueError("window 必须大于 1。")

    # 清洗收盘价并计算日收益率的滚动标准差，再按 252 个交易日年化。
    numeric_prices = pd.to_numeric(prices, errors="coerce").dropna()#to_numeric将收盘价转为数字，errors="coerce"的意思是转不了的变成 NaN，.dropna()是再去掉缺失值
    if len(numeric_prices) < window + 1:
        raise ValueError(
            f"有效收盘价不足：计算 {window} 日波动率至少需要 {window + 1} 个价格。"
        )

    daily_returns = numeric_prices.pct_change(fill_method=None)#pct_change 是 pandas 的百分比变化，判断后一天比前一天涨了多少。fill_method=None是遇到空值是不做处理，直接空着，不需要填充
    rolling_volatility = daily_returns.rolling(window=window).std() * math.sqrt(252)#计算每天的20日收益率的标准差，再乘根号252进行年化
    latest_volatility = rolling_volatility.iloc[-1]#取最近一个交易日对应的 20 日年化波动率。
    if pd.isna(latest_volatility):
        raise ValueError("最近一期年化波动率无法计算。")

    return float(latest_volatility)


def main() -> None:
    """执行沪深 300 权重前十股票波动率筛选流程。

    Returns:
        None。

    Raises:
        RuntimeError: 数据获取失败、没有可汇总结果或 Excel 保存失败时抛出。
    """
    top10 = get_hs300_top10_by_weight()

    summary_rows: list[dict[str, str | float]] = []#类型标注，给人和编辑器看，不改变运行结果。是一个 list，里面每个元素是 dict；字典的 键 是 str，值 是 str 或 float
    total_stocks = len(top10)

    for position, row in top10.iterrows():#.iterrows() 按行走，position是索引，row是这一行数据
        code = str(row["code"])
        name = str(row["name"])
        print(f"[{position + 1}/{total_stocks}] 计算 {name} 波动率...")

        daily_data = get_stock_daily(code, lookback_days=120)
        if daily_data.empty:
            warnings.warn(f"股票 {code}（{name}）日线数据为空，已跳过。", stacklevel=2)
            continue

        try:
            annualized_volatility = calculate_annualized_volatility(
                daily_data["close"], window=20
            )
        except ValueError as exc:
            warnings.warn(
                f"股票 {code}（{name}）无法计算波动率，已跳过：{exc}",
                stacklevel=2,
            )
            continue

        summary_rows.append(
            {
                "股票代码": code,
                "股票名称": name,
                "指数权重(%)": float(row["weight"]),
                "最近20日年化波动率": annualized_volatility,
            }
        )

    if not summary_rows:
        raise RuntimeError("所有股票均无有效日线数据，无法生成汇总结果。")

    # 汇总结果按年化波动率从高到低排列。
    summary = pd.DataFrame(summary_rows).sort_values(
        "最近20日年化波动率", ascending=False
    )
    summary = summary.reset_index(drop=True)

    print("\n最终结果：")
    print(summary.to_string(index=False))

    # 创建输出目录并将结果保存为 Excel 文件。
    try:
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        summary.to_excel(OUTPUT_PATH, index=False, engine="openpyxl")
    except Exception as exc:
        raise RuntimeError(f"保存 Excel 文件失败：{exc}") from exc

    print(f"\n结果已保存至：{OUTPUT_PATH}")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"程序执行失败：{error}", file=sys.stderr)
        sys.exit(1)
