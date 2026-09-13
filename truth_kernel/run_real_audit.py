"""
truth_kernel.run_real_audit
~~~~~~~~~~~~~~~~~~~~~~~~~~~
对全量真实 A 股历史财报执行严格的免疫排毒体检。
杜绝一切模拟数据，100% 基于已审计真实财务公开报表。
输出结构化体检报告供 V0 顶级前端可视化 UI 实时消费。
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
from immune_system.cash_purity import CashPurityEngine
from immune_system.debt_wall import DebtWallEngine
from immune_system.poison_firewall import PoisonFirewall


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "real_financials")


def run_full_real_audit() -> Dict[str, Any]:
    universe_file = os.path.join(DATA_DIR, "real_market_universe.json")
    if not os.path.exists(universe_file):
        raise FileNotFoundError(f"未找到真实市场数据: {universe_file}")

    with open(universe_file, "r", encoding="utf-8") as f:
        universe_data = json.load(f)

    purity_engine = CashPurityEngine()
    debt_engine = DebtWallEngine()
    firewall = PoisonFirewall(
        cash_purity_engine=purity_engine,
        debt_wall_engine=debt_engine
    )

    results = {}
    summary_stats = {
        "total_analyzed_reports": 0,
        "total_admitted": 0,
        "total_vetoed": 0,
        "total_warnings": 0,
        "stocks": []
    }

    for symbol, info in universe_data.items():
        meta = info["metadata"]
        history = info["history"]

        stock_reports = []
        for r in history:
            bs = BalanceSheet(
                total_assets=r.get("total_assets", 0.0),
                total_liabilities=r.get("total_liabilities", 0.0),
                total_equity=r.get("total_equity", 0.0),
                cash_and_equivalents=r.get("cash_and_equivalents", 0.0),
                restricted_cash=r.get("restricted_cash", 0.0),
                receivables=r.get("receivables", 0.0),
                goodwill=r.get("goodwill", 0.0),
                short_term_debt=r.get("short_term_debt", 0.0),
                long_term_debt_due_within_1y=r.get("long_term_debt_due_within_1y", 0.0)
            )
            inc = IncomeStatement(
                revenue=r.get("revenue", 0.0),
                operating_profit=r.get("operating_profit", 0.0),
                net_profit=r.get("net_profit", 0.0),
                financial_expenses=r.get("financial_expenses", 0.0)
            )
            cf = CashFlowStatement(
                operating_cash_flow=r.get("operating_cash_flow", 0.0),
                capex=r.get("capex", 0.0)
            )
            record = CompanyFinancialRecord(
                symbol=symbol,
                period_end_date=r.get("period_end_date", ""),
                disclosure_date=r.get("disclosure_date", ""),
                balance_sheet=bs,
                income_statement=inc,
                cash_flow_statement=cf
            )

            audit_report = firewall.audit(record)

            summary_stats["total_analyzed_reports"] += 1
            if audit_report.is_admitted:
                summary_stats["total_admitted"] += 1
            else:
                summary_stats["total_vetoed"] += 1
            if audit_report.warning_reasons:
                summary_stats["total_warnings"] += 1

            stock_reports.append({
                "period_end_date": r["period_end_date"],
                "disclosure_date": r["disclosure_date"],
                "revenue": r["revenue"],
                "net_profit": r["net_profit"],
                "operating_cash_flow": r["operating_cash_flow"],
                "free_cash_flow": r["free_cash_flow"],
                "cash_and_equivalents": r["cash_and_equivalents"],
                "restricted_cash": r.get("restricted_cash", 0.0),
                "receivables": r["receivables"],
                "total_due_1y": bs.total_due_1y,
                "debt_to_assets": bs.debt_to_assets,
                "is_admitted": audit_report.is_admitted,
                "phi_cp": audit_report.cash_purity.phi_cp,
                "omega_debt": audit_report.debt_wall.omega_debt,
                "veto_reasons": audit_report.veto_reasons,
                "warning_reasons": audit_report.warning_reasons,
                "purity_diagnosis": audit_report.cash_purity.diagnosis,
                "debt_diagnosis": audit_report.debt_wall.diagnosis
            })

        latest_rep = stock_reports[-1] if stock_reports else None
        results[symbol] = {
            "metadata": meta,
            "latest_status": latest_rep,
            "timeline": stock_reports
        }
        summary_stats["stocks"].append({
            "symbol": symbol,
            "name": meta["name"],
            "category": meta["category"],
            "tag": meta.get("tag", "general"),
            "latest_period": latest_rep["period_end_date"] if latest_rep else "",
            "is_admitted": latest_rep["is_admitted"] if latest_rep else False,
            "phi_cp": latest_rep["phi_cp"] if latest_rep else 0.0,
            "omega_debt": latest_rep["omega_debt"] if latest_rep else 0.0,
            "veto_count": len(latest_rep["veto_reasons"]) if latest_rep else 0,
            "total_reports": len(stock_reports)
        })

    output_payload = {
        "summary": summary_stats,
        "details": results
    }

    out_file = os.path.join(DATA_DIR, "audit_summary.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, ensure_ascii=False, indent=2)

    print(f"[√] 全量真实数据体检完成！分析报告: {summary_stats['total_analyzed_reports']} 份")
    print(f"    - 准入洁净池: {summary_stats['total_admitted']} 份")
    print(f"    - 一票否决淘汰: {summary_stats['total_vetoed']} 份")
    return output_payload


if __name__ == "__main__":
    run_full_real_audit()
