"""获取贵州茅台近期行情、计算基础指标并生成收盘价走势图。"""

from __future__ import annotations

import os
import sys
from datetime import date, timedelta
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import tushare as ts
from dotenv import load_dotenv


STOCK_CODE = "600519.SH"
TRADING_DAYS = 30
PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_PATH = PROJECT_ROOT / "outputs" / "maotai_price.png"


def get_stock_data(token: str, trading_days: int = TRADING_DAYS) -> pd.DataFrame:
    """从 Tushare 获取贵州茅台最近若干个交易日的日 K 线数据。

    为覆盖周末和节假日，函数先查询最近 120 个自然日，再按交易日期排序并
    截取最后 ``trading_days`` 条记录。

    Args:
        token: Tushare API Token。
        trading_days: 需要保留的最近交易日数量，默认是 30。

    Returns:
        按交易日期升序排列的日 K 线 DataFrame，其中 ``trade_date`` 为日期类型。

    Raises:
        RuntimeError: Tushare API 调用失败时抛出。
        ValueError: API 返回空数据，或有效数据不足指定交易日数量时抛出。
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=120)

    try:
        pro = ts.pro_api(token)
        data = pro.daily(
            ts_code=STOCK_CODE,
            start_date=start_date.strftime("%Y%m%d"),
            end_date=end_date.strftime("%Y%m%d"),
        )
    except Exception as exc:
        raise RuntimeError(
            "Tushare API 调用失败，请检查网络连接、Token 是否有效及接口权限。"
        ) from exc

    if data is None or data.empty:
        raise ValueError(
            f"未获取到 {STOCK_CODE} 的行情数据，请检查查询日期、Token 和接口权限。"
        )

    required_columns = {"trade_date", "close", "vol"}
    missing_columns = required_columns.difference(data.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"API 返回数据缺少必要字段：{missing}。")

    # Tushare 默认按日期倒序返回；计算收益率前必须先改为时间正序。
    data = data.copy()
    data["trade_date"] = pd.to_datetime(data["trade_date"], format="%Y%m%d")
    data = data.sort_values("trade_date").tail(trading_days).reset_index(drop=True)

    if len(data) < trading_days:
        raise ValueError(
            f"仅获取到 {len(data)} 个交易日的数据，少于要求的 {trading_days} 个交易日。"
        )

    return data


def calculate_metrics(data: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
    """计算每日收益率、累计收益率、最大回撤和平均日成交量。

    Args:
        data: 按交易日期升序排列的行情数据，需包含 ``close`` 和 ``vol`` 列。

    Returns:
        一个二元组：
        - 增加每日收益率、累计收益率和回撤列后的 DataFrame；
        - 包含汇总指标的字典。

    Notes:
        Tushare 日线接口中的 ``vol`` 单位通常为“手”，1 手等于 100 股。
        每日收益率第一天没有前一日价格，因此其值为缺失值（NaN）。
    """
    result = data.copy()

    # pct_change 计算“今日收盘价 / 昨日收盘价 - 1”。
    result["daily_return"] = result["close"].pct_change()

    # 累计收益率以这 30 个交易日中的第一天收盘价为基准。
    result["cumulative_return"] = result["close"] / result["close"].iloc[0] - 1

    # 回撤表示当前价格相对历史最高收盘价的跌幅，最小值即最大回撤。
    result["drawdown"] = result["close"] / result["close"].cummax() - 1

    metrics = {
        "cumulative_return": float(result["cumulative_return"].iloc[-1]),
        "max_drawdown": float(result["drawdown"].min()),
        "average_volume": float(result["vol"].mean()),
    }
    return result, metrics


def plot_closing_price(data: pd.DataFrame, output_path: Path = OUTPUT_PATH) -> None:
    """绘制贵州茅台收盘价折线图，并将图片保存到指定路径。

    Args:
        data: 包含 ``trade_date`` 和 ``close`` 列的行情数据。
        output_path: 图片输出路径，默认为 ``outputs/maotai_price.png``。

    Raises:
        RuntimeError: 图片生成或保存失败时抛出。
    """
    try:
        # macOS 优先使用苹方；若不可用，则回退到 Arial Unicode MS。
        plt.rcParams["font.sans-serif"] = ["PingFang SC", "Arial Unicode MS"]
        plt.rcParams["axes.unicode_minus"] = False

        output_path.parent.mkdir(parents=True, exist_ok=True)
        figure, axis = plt.subplots(figsize=(12, 6))
        axis.plot(
            data["trade_date"],
            data["close"],
            color="#7C3AED",
            linewidth=2,
            marker="o",
            markersize=3,
        )
        axis.set_title("贵州茅台（600519.SH）近30日收盘价走势", fontsize=16)
        axis.set_xlabel("日期")
        axis.set_ylabel("收盘价（元）")
        axis.grid(True, linestyle="--", alpha=0.4)
        figure.autofmt_xdate()
        figure.tight_layout()
        figure.savefig(output_path, dpi=160, bbox_inches="tight")
        plt.close(figure)
    except Exception as exc:
        plt.close("all")
        raise RuntimeError(f"图表保存失败：{output_path}") from exc


def print_summary(data: pd.DataFrame, metrics: dict[str, float]) -> None:
    """在终端打印本次行情分析的简明摘要。

    Args:
        data: 已按交易日期升序排列并完成指标计算的行情数据。
        metrics: ``calculate_metrics`` 返回的汇总指标字典。
    """
    start_row = data.iloc[0]
    end_row = data.iloc[-1]

    print("\n=== 贵州茅台近 30 个交易日分析摘要 ===")
    print(
        f"数据区间：{start_row['trade_date']:%Y-%m-%d} 至 "
        f"{end_row['trade_date']:%Y-%m-%d}"
    )
    print(f"起始价格：{start_row['close']:.2f} 元")
    print(f"结束价格：{end_row['close']:.2f} 元")
    print(f"累计收益率：{metrics['cumulative_return']:.2%}")
    print(f"最大回撤：{metrics['max_drawdown']:.2%}")
    print(f"平均日成交量：{metrics['average_volume']:,.2f} 手")
    print(f"图表已保存：{OUTPUT_PATH}")


def main() -> None:
    """加载配置并依次执行数据获取、指标计算、绘图和摘要输出。"""
    env_path = PROJECT_ROOT / ".env"
    load_dotenv(env_path)
    token = os.getenv("TUSHARE_TOKEN", "").strip()

    if not token:
        raise ValueError(
            f"缺少 TUSHARE_TOKEN。请在项目根目录的 {env_path.name} 文件中配置该变量。"
        )

    data = get_stock_data(token)
    data_with_metrics, metrics = calculate_metrics(data)
    plot_closing_price(data_with_metrics)
    print_summary(data_with_metrics, metrics)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        sys.exit(1)
