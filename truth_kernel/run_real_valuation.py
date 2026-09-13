"""
truth_kernel.run_real_valuation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
对 100% 真实 A 股已审计财报标的池执行真值引力估值与 Alpha 决策全量推演。
输出结构化评估报告，全面升级 V0 监控大屏。
"""

import os
import json
from typing import Dict, List, Any
from truth_kernel.models import (
    BalanceSheet,
    IncomeStatement,
    CashFlowStatement,
    CompanyFinancialRecord
)
from immune_system.poison_firewall import PoisonFirewall
from gravity_brain.dcf_gravity import GravityValuationEngine
from gravity_brain.asymmetric_pricing import AsymmetricPricingEngine
from gravity_brain.alpha_engine import GravityAlphaEngine


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "real_financials")

# 真实 A 股市值参考基准（单位：元）
REAL_MARKET_CAPS = {
    "600519": 1.95e12,   # 贵州茅台 ~ 1.95 万亿
    "600900": 7.10e11,   # 长江电力 ~ 7100 亿
    "002594": 8.30e11,   # 比亚迪 ~ 8300 亿
    "000002": 8.50e10,   # 万科A ~ 850 亿
    "300104": 1.50e9,    # 乐视退 ~ 15 亿
    "600518": 2.80e10    # ST康美 ~ 280 亿
}


def run_valuation_pipeline() -> Dict[str, Any]:
    universe_file = os.path.join(DATA_DIR, "real_market_universe.json")
    with open(universe_file, "r", encoding="utf-8") as f:
        universe = json.load(f)

    alpha_engine = GravityAlphaEngine()
    val_engine = GravityValuationEngine()

    candidates = []
    detailed_results = {}

    for sym, info in universe.items():
        meta = info["metadata"]
        history = info["history"]
        if not history:
            continue

        latest = history[-1]
        bs = BalanceSheet(
            total_assets=latest.get("total_assets", 0.0),
            total_liabilities=latest.get("total_liabilities", 0.0),
            total_equity=latest.get("total_equity", 0.0),
            cash_and_equivalents=latest.get("cash_and_equivalents", 0.0),
            restricted_cash=latest.get("restricted_cash", 0.0),
            receivables=latest.get("receivables", 0.0),
            goodwill=latest.get("goodwill", 0.0),
            short_term_debt=latest.get("short_term_debt", 0.0),
            long_term_debt_due_within_1y=latest.get("long_term_debt_due_within_1y", 0.0)
        )
        inc = IncomeStatement(
            revenue=latest.get("revenue", 0.0),
            operating_profit=latest.get("operating_profit", 0.0),
            net_profit=latest.get("net_profit", 0.0),
            financial_expenses=latest.get("financial_expenses", 0.0)
        )
        cf = CashFlowStatement(
            operating_cash_flow=latest.get("operating_cash_flow", 0.0),
            capex=latest.get("capex", 0.0)
        )
        rec = CompanyFinancialRecord(
            symbol=sym,
            period_end_date=latest["period_end_date"],
            disclosure_date=latest["disclosure_date"],
            balance_sheet=bs,
            income_statement=inc,
            cash_flow_statement=cf
        )

        cap = REAL_MARKET_CAPS.get(sym, 1e11)
        val = val_engine.compute_intrinsic_value(rec, market_cap=cap)
        candidate = alpha_engine.evaluate_candidate(rec, market_cap=cap)

        detailed_results[sym] = {
            "name": meta["name"],
            "category": meta["category"],
            "period_end_date": latest["period_end_date"],
            "market_cap": cap,
            "gravity_value": val.gravity_value,
            "tangible_nav_floor": val.tangible_nav_floor,
            "discounted_fcf_sum": val.discounted_fcf_sum,
            "gravity_potential": val.gravity_potential,
            "margin_of_safety": val.margin_of_safety,
            "is_undervalued": val.is_undervalued,
            "alpha_score": candidate.alpha_score,
            "signal": candidate.signal,
            "phi_cp": candidate.phi_cp,
            "omega_debt": candidate.omega_debt,
            "convexity_score": candidate.convexity_score,
            "is_firewall_admitted": candidate.is_firewall_admitted
        }
        candidates.append(detailed_results[sym])

    # 排序
    candidates.sort(key=lambda x: x["alpha_score"], reverse=True)

    output_path = os.path.join(DATA_DIR, "valuation_summary.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(detailed_results, f, ensure_ascii=False, indent=2)

    print("\n=== TRINITY QUANT 真实市场真值引力定价与 Alpha 决策榜 ===")
    for rank, c in enumerate(candidates, 1):
        status = "准入" if c["is_firewall_admitted"] else "否决"
        print(f"#{rank} {c['name']} ({status}) | 信号: {c['signal']:<10} | Alpha: {c['alpha_score']:>6.1f} | 真值 V_G: {c['gravity_value']/1e8:>8.1f}亿 | 市值: {c['market_cap']/1e8:>8.1f}亿 | 势能差: {((c['gravity_potential'] or 0)*100):>6.1f}%")

    return detailed_results


if __name__ == "__main__":
    run_valuation_pipeline()
