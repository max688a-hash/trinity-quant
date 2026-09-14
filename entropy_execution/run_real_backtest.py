"""
entropy_execution.run_real_backtest
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
对真实 A 股上市公司历史审计报表 + 真实落盘价格快照执行全仿真历史回测。

铁律：
- 价格只能来自 data/real_financials/real_price_history.json（带来源与抓取时间），缺文件直接报错；
- 财务字段缺失/为零 → 该期该标的直接剔除，严禁 1e9 / 5e8 之类常量顶替；
- 报表必须携带 disclosure_date，且只在披露日 <= 调仓日后可见（PIT）；
- 退市/长期停牌标的按最后已知收盘价强制清算，样本空间含退市股（无幸存者偏差）；
- 同步给出等权买入持有基线，策略必须与基线对照，不得孤立宣传收益。
"""

import json
import os
from datetime import date
from typing import Any, Dict, List, Optional

from entropy_execution.backtest_engine import EventDrivenBacktester
from entropy_execution.friction_engine import FrictionEngine
from truth_kernel.models import BalanceSheet, CashFlowStatement, CompanyFinancialRecord, IncomeStatement
from truth_kernel.price_history_store import (
    DEFAULT_PRICE_FILE,
    PriceSeries,
    close_on_or_before,
    is_listed_by,
    last_known_close,
    load_price_history,
)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "real_financials")
REQUIRED_POSITIVE = ("total_assets", "total_equity", "revenue")
REQUIRED_PRESENT = (
    "total_liabilities", "cash_and_equivalents", "operating_profit", "net_profit",
    "operating_cash_flow", "capex", "disclosure_date", "period_end_date",
)
QUARTER_ENDS = [
    date(y, m, d) for y in range(2018, 2024) for (m, d) in ((3, 31), (6, 30), (9, 30), (12, 31))
]


def _record_from_json(sym: str, r: Dict[str, Any]) -> Optional[CompanyFinancialRecord]:
    """字段齐全才构造记录；任何缺失/非正的必需字段 → None（剔除，不补常量）"""
    for k in REQUIRED_PRESENT:
        if r.get(k) is None:
            return None
    for k in REQUIRED_POSITIVE:
        v = r.get(k)
        if not isinstance(v, (int, float)) or v <= 0:
            return None
    bs = BalanceSheet(
        total_assets=float(r["total_assets"]), total_liabilities=float(r["total_liabilities"]),
        total_equity=float(r["total_equity"]), cash_and_equivalents=float(r["cash_and_equivalents"]),
        restricted_cash=float(r.get("restricted_cash", 0.0)), receivables=float(r.get("receivables", 0.0)),
        goodwill=float(r.get("goodwill", 0.0)), short_term_debt=float(r.get("short_term_debt", 0.0)),
        long_term_debt_due_within_1y=float(r.get("long_term_debt_due_within_1y", 0.0)),
    )
    inc = IncomeStatement(
        revenue=float(r["revenue"]), operating_profit=float(r["operating_profit"]),
        net_profit=float(r["net_profit"]), financial_expenses=float(r.get("financial_expenses", 0.0)),
    )
    cf = CashFlowStatement(operating_cash_flow=float(r["operating_cash_flow"]), capex=float(r["capex"]))
    return CompanyFinancialRecord(
        symbol=sym, period_end_date=str(r["period_end_date"]), disclosure_date=str(r["disclosure_date"]),
        balance_sheet=bs, income_statement=inc, cash_flow_statement=cf,
    )


def _latest_disclosed(records: List[Dict[str, Any]], as_of: date) -> Optional[Dict[str, Any]]:
    """截至 as_of 已披露的最新报表（按披露日 PIT，而非报告期末）"""
    visible = [r for r in records if r.get("disclosure_date") and date.fromisoformat(str(r["disclosure_date"])[:10]) <= as_of]
    if not visible:
        return None
    return max(visible, key=lambda r: str(r["period_end_date"]))


def build_pit_dataset(
    universe: Dict[str, Any], prices: Dict[str, PriceSeries], rebalance_dates: List[date]
) -> Dict[str, Any]:
    snapshots: List[Dict[str, CompanyFinancialRecord]] = []
    feeds: List[Dict[str, float]] = []
    fallback: List[Dict[str, float]] = []
    excluded = 0
    for as_of in rebalance_dates:
        snap: Dict[str, CompanyFinancialRecord] = {}
        px: Dict[str, float] = {}
        fb: Dict[str, float] = {}
        for sym, info in universe.items():
            series = prices.get(sym, [])
            if not is_listed_by(series, as_of):
                continue
            close = close_on_or_before(series, as_of)
            if close is None:
                lk = last_known_close(series, as_of)
                if lk:
                    fb[sym] = lk[1]
                continue
            px[sym] = close
            raw = _latest_disclosed(info["history"], as_of)
            rec = _record_from_json(sym, raw) if raw else None
            if rec is None:
                excluded += 1
                continue
            snap[sym] = rec
        snapshots.append(snap)
        feeds.append(px)
        fallback.append(fb)
    return {"snapshots": snapshots, "price_feeds": feeds, "last_known": fallback, "excluded_symbol_periods": excluded}


def equal_weight_buy_hold(
    price_feeds: List[Dict[str, float]], last_known: List[Dict[str, float]], initial_cash: float
) -> Dict[str, Any]:
    """等权买入持有基线（首期建仓、退市按最后已知价清算、全摩擦）"""
    fe = FrictionEngine()
    cash = initial_cash
    holdings: Dict[str, int] = {}
    curve = [initial_cash]
    if price_feeds and price_feeds[0]:
        per = initial_cash / len(price_feeds[0])
        for sym, p in price_feeds[0].items():
            n = (int(per / p) // 100) * 100
            if n > 0:
                fill = fe.execute_buy(sym, p, n)
                cash += fill.net_cash_impact
                holdings[sym] = n
    for t, px in enumerate(price_feeds):
        for sym in list(holdings):
            if sym not in px and sym in last_known[t]:
                fill = fe.execute_sell(sym, last_known[t][sym], holdings.pop(sym))
                cash += fill.net_cash_impact
        curve.append(cash + sum(n * px.get(s, 0.0) for s, n in holdings.items()))
    return {"final_equity": round(curve[-1], 2), "total_net_return": round((curve[-1] - initial_cash) / initial_cash, 4), "equity_curve": curve}


def run_full_real_backtest(price_file: str = DEFAULT_PRICE_FILE, write_summary: bool = True) -> Dict[str, Any]:
    with open(os.path.join(DATA_DIR, "real_market_universe.json"), "r", encoding="utf-8") as f:
        universe = json.load(f)
    prices = load_price_history(price_file)
    ds = build_pit_dataset(universe, prices, QUARTER_ENDS)

    initial_cash = 10_000_000.0
    report = EventDrivenBacktester(initial_cash=initial_cash).run_simulation(
        ds["snapshots"], ds["price_feeds"], periods_per_year=4,
        rebalance_dates=QUARTER_ENDS, last_known_prices=ds["last_known"],
    )
    baseline = equal_weight_buy_hold(ds["price_feeds"], ds["last_known"], initial_cash)

    payload: Dict[str, Any] = {
        "initial_cash": report.initial_cash, "final_equity": report.final_equity,
        "total_net_return": report.total_net_return, "cagr": report.cagr,
        "max_drawdown": report.max_drawdown, "total_trades": report.total_trades,
        "total_friction_cost": report.total_friction_cost,
        "calmar_ratio": report.risk_metrics.calmar_ratio, "sharpe_ratio": report.risk_metrics.sharpe_ratio,
        "volatility_drag": report.risk_metrics.volatility_drag, "equity_curve": report.equity_curve,
        "periods": ["初始 (2018-01)"] + [d.isoformat() for d in QUARTER_ENDS],
        "kelly_cold_start_periods": report.cold_start_periods,
        "kelly_empirical_periods": report.empirical_periods,
        "forced_liquidations": report.forced_liquidations,
        "pit_excluded_records": report.pit_excluded_records,
        "excluded_symbol_periods_missing_financials": ds["excluded_symbol_periods"],
        "baseline_equal_weight_buy_hold": baseline,
        "beats_baseline": report.total_net_return > baseline["total_net_return"],
        "gravity_potential_available": False,
        "universe_size": len(universe),
        "statistical_caveat": (
            f"样本仅 {len(universe)} 只、{len(QUARTER_ENDS)} 期季频，凯利实证期 {report.empirical_periods}/{len(QUARTER_ENDS)}；"
            "无股本数据故引力势能中性；结论不具备统计显著性，不得作为盈利证据。"
        ),
    }
    if write_summary:
        with open(os.path.join(DATA_DIR, "backtest_summary.json"), "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    _print_report(payload)
    return payload


def _print_report(p: Dict[str, Any]) -> None:
    print("\n=== TRINITY QUANT 真实历史 PIT 回测战报 (季频 2018-2023, 含退市股) ===")
    print(f"初始本金: {p['initial_cash']:,.2f} 元 | 终局净值: {p['final_equity']:,.2f} 元 (净收益 {p['total_net_return']*100:.2f}%)")
    print(f"CAGR: {p['cagr']*100:.2f}% | MaxDD: {p['max_drawdown']*100:.2f}% | Calmar: {p['calmar_ratio']:.2f} | Sharpe: {p['sharpe_ratio']:.2f}")
    print(f"摩擦成本: {p['total_friction_cost']:,.2f} 元 | 成交 {p['total_trades']} 笔 | 强制清算: {p['forced_liquidations']}")
    b = p["baseline_equal_weight_buy_hold"]
    print(f"等权买入持有基线: {b['total_net_return']*100:.2f}% | 跑赢基线: {p['beats_baseline']}")
    print(f"凯利冷启动期 {p['kelly_cold_start_periods']} / 实证期 {p['kelly_empirical_periods']} | PIT 剔除报表 {p['pit_excluded_records']} | 缺财务剔除 {p['excluded_symbol_periods_missing_financials']}")
    print(f"统计告示: {p['statistical_caveat']}")


if __name__ == "__main__":
    run_full_real_backtest()
