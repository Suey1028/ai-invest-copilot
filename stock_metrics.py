"""计算单只股票在指定日期范围内的关键金融指标。"""

from __future__ import annotations

import functools
import math
import os
import time
from collections.abc import Callable
from datetime import datetime
from typing import ParamSpec, TypeVar

import pandas as pd
import tushare as ts
from dotenv import load_dotenv


load_dotenv()
pro = ts.pro_api(os.getenv("TUSHARE_TOKEN"))

P = ParamSpec("P")
R = TypeVar("R")


def timer(func: Callable[P, R]) -> Callable[P, R]:
    """计时装饰器，打印被装饰函数的执行耗时。

    Args:
        func: 需要统计耗时的可调用对象。

    Returns:
        包装后的函数，返回值与原函数一致。
    """

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:#内部函数，加了计时器的新做法
        started_at = time.perf_counter()
        try:
            return func(*args, **kwargs)#执行原函数，看要多久
        finally:
            elapsed_seconds = time.perf_counter() - started_at
            print(f"[{func.__name__}] 耗时: {elapsed_seconds:.4f}秒")

    return wrapper#把新做法返回


def _parse_date(date_text: str, field_name: str) -> datetime:#把字符串时间转为时间格式
    """将 YYYY-MM-DD 字符串解析为 datetime。

    Args:
        date_text: 待解析的日期字符串。
        field_name: 字段名，用于错误提示。

    Returns:
        解析后的 datetime。

    Raises:
        ValueError: 当日期格式不符合 YYYY-MM-DD 时抛出。
    """
    try:
        return datetime.strptime(date_text, "%Y-%m-%d")#必须以这个格式进行输入%Y-%m-%d，否则就会报格式错误
    except ValueError as exc:
        raise ValueError(
            f"{field_name} 格式错误，应为 YYYY-MM-DD，实际为 {date_text!r}"
        ) from exc


def _to_tushare_code(stock_code: str) -> str:#把股票代码转为带有交易所后缀的代码
    """把 6 位股票代码转成 Tushare 带交易所后缀的代码。"""
    if stock_code.startswith("6"):
        return f"{stock_code}.SH"
    return f"{stock_code}.SZ"


@timer
def calculate_stock_metrics(#传入股票代码以及时间范围，返回字典形式的各个指标
    stock_code: str,
    start_date: str,
    end_date: str,
) -> dict[str, float | int]:
    """计算单只股票在给定区间内的累计收益、回撤、夏普、胜率和交易天数。

    Args:
        stock_code: 6 位股票代码，如 "600519"。
        start_date: 开始日期，格式 YYYY-MM-DD。
        end_date: 结束日期，格式 YYYY-MM-DD。

    Returns:
        包含 cumulative_return、max_drawdown、sharpe_ratio、win_rate、
        trading_days 的指标字典。

    Raises:
        ValueError: 日期格式错误，或开始日期晚于结束日期。
        RuntimeError: Tushare 接口失败，或区间内无行情数据。
    """
    parsed_start = _parse_date(start_date, "start_date")#用之前写的函数转化为时间格式
    parsed_end = _parse_date(end_date, "end_date")

    # 校验日期先后顺序
    if parsed_start > parsed_end:
        date_order_error = ValueError(
            f"开始日期 {start_date} 晚于结束日期 {end_date}"
        )
        raise ValueError(str(date_order_error)) from date_order_error

    ts_code = _to_tushare_code(stock_code)#从第三方获取数据
    tushare_start = parsed_start.strftime("%Y%m%d")
    tushare_end = parsed_end.strftime("%Y%m%d")

    # 拉取区间内日线行情
    try:
        daily_data = pro.daily(
            ts_code=ts_code,
            start_date=tushare_start,
            end_date=tushare_end,
        )
    except Exception as exc:
        raise RuntimeError(
            f"Tushare API 调用失败：{stock_code} {start_date}~{end_date}"
        ) from exc

    if daily_data is None or daily_data.empty:
        empty_data_error = RuntimeError(
            f"股票代码不存在或日期范围内无数据：{stock_code} {start_date}~{end_date}"
        )
        raise RuntimeError(str(empty_data_error)) from empty_data_error

    daily_data = daily_data.sort_values("trade_date").reset_index(drop=True)#获得该股票的日线数据，并根据交易日期重新排序
    close_prices = pd.to_numeric(daily_data["close"], errors="coerce").dropna()#获得该股票的收盘价数据，并删除缺失值
    if close_prices.empty:
        empty_price_error = RuntimeError(
            f"股票代码不存在或日期范围内无数据：{stock_code} {start_date}~{end_date}"
        )
        raise RuntimeError(str(empty_price_error)) from empty_price_error

    trading_days = len(daily_data)#一共有多少个交易日数据
    first_close = float(close_prices.iloc[0])#第一个交易日的收盘价数据
    last_close = float(close_prices.iloc[-1])#最后一个交易日的收盘价数据

    # 累计收益率：(期末 / 期初) - 1
    # 业务含义：整个区间赚了多少百分比，正值涨、负值跌
    cumulative_return = last_close / first_close - 1

    # 最大回撤：相对历史高点的最大跌幅
    # 业务含义：期间最坏情况下账户浮亏了多少，衡量下行风险
    max_drawdown = float((close_prices / close_prices.cummax()).min() - 1)

# 日收益率序列（后面计算夏普和胜率都要用）
    daily_returns = close_prices.pct_change(fill_method=None)#当天收益率 = (当天收盘价 - 前一天收盘价) / 前一天收盘价
    daily_std = float(daily_returns.std())# 波动率（标准差）
    daily_mean = float(daily_returns.mean()) # 平均日收益率

    # 年化夏普：无风险利率按 0，波动率为 0 时视为 0
    # 业务含义：每承担一单位风险能赚多少收益，衡量投资性价比。>1 不错，>2 优秀
    if daily_std == 0 or math.isnan(daily_std):
        sharpe_ratio = 0.0
    else:
        sharpe_ratio = (daily_mean * 252) / (daily_std * math.sqrt(252))

    # 胜率：上涨天数 / 总交易天数（第一天无收益率，不计入分子）
    # 业务含义：这段时间赚钱的天数占比，反映趋势强度
    win_rate = float((daily_returns > 0).sum() / trading_days)

    return {
        "cumulative_return": float(cumulative_return),
        "max_drawdown": max_drawdown,
        "sharpe_ratio": float(sharpe_ratio),
        "win_rate": win_rate,
        "trading_days": int(trading_days),
    }


def _print_metrics(title: str, metrics: dict[str, float | int]) -> None:
    """按指定格式打印指标结果。"""
    print(f"\n{title}")
    print(f"  累计收益率: {metrics['cumulative_return']:.2%}")
    print(f"  最大回撤: {metrics['max_drawdown']:.2%}")
    print(f"  夏普比率: {metrics['sharpe_ratio']:.2f}")
    print(f"  胜率: {metrics['win_rate']:.2%}")
    print(f"  交易天数: {metrics['trading_days']:d}")

#在main函数里调用计算金融指标的函数
def main() -> None:
    """演示正常沪市、深市样本以及错误日期格式的异常处理。"""
    cases: list[tuple[str, str, str, str]] = [
        ("贵州茅台", "600519", "2026-06-01", "2026-09-01"),
        ("宁德时代", "300750", "2026-06-01", "2026-09-01"),
        ("错误日期格式", "600519", "2026/01/01", "2026-09-01"),
    ]

    for name, stock_code, start_date, end_date in cases:
        print(f"\n=== {name} {stock_code} {start_date} ~ {end_date} ===")
        try:
            metrics = calculate_stock_metrics(stock_code, start_date, end_date)
            _print_metrics("指标结果", metrics)
        except Exception as error:
            print(f"程序捕获异常：{type(error).__name__}: {error}")


if __name__ == "__main__":
    main()
