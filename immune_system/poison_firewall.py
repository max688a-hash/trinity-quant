"""
immune_system.poison_firewall
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
综合排毒防火墙流水线 (Toxic Screener & Firewall)。
执行多维一票否决制，将财务粉饰、债务炸弹与商誉虚胖标的彻底拒之门外，
仅输出具备真实现金流生命力的【纯净真值标的池】。
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any
from truth_kernel.models import CompanyFinancialRecord
from immune_system.cash_purity import CashPurityEngine, CashPurityAssessment
from immune_system.debt_wall import DebtWallEngine, DebtWallAssessment


@dataclass(frozen=True)
class FirewallAuditReport:
    """标的免疫排毒完整审计体检报告"""
    symbol: str
    period_end_date: str
    is_admitted: bool                   # 是否准入纯净真值股票池 (False = 一票否决)
    veto_reasons: List[str]             # 致命否决原因清单
    warning_reasons: List[str]          # 潜在隐患预警清单
    cash_purity: CashPurityAssessment   # 造血纯度评估体征
    debt_wall: DebtWallAssessment       # 债务毒性评估体征


class PoisonFirewall:
    """
    一票否决制免疫排毒防火墙
    四道铁血关卡：
    1. 造血纯度 Φ_CP 穿透关（防利润虚增）
    2. 债务毒性 Ω_Debt 挤兑关（防到期墙休克）
    3. 资产负债表体质关（防商誉黑洞与资产负债率爆表）
    4. 受限资金造假关（防账面有钱却无法动用之康美式假象）
    """

    def __init__(
        self,
        max_goodwill_to_equity: float = 0.30,
        max_restricted_cash_ratio: float = 0.40,
        max_debt_to_assets: float = 0.85,
        cash_purity_engine: CashPurityEngine = None,
        debt_wall_engine: DebtWallEngine = None,
    ) -> None:
        self.max_goodwill_to_equity = max_goodwill_to_equity
        self.max_restricted_cash_ratio = max_restricted_cash_ratio
        self.max_debt_to_assets = max_debt_to_assets

        self.purity_engine = cash_purity_engine or CashPurityEngine()
        self.debt_engine = debt_wall_engine or DebtWallEngine()

    def audit(self, record: CompanyFinancialRecord) -> FirewallAuditReport:
        """对单家企业执行全套排毒体检，输出详细体检审计单"""
        veto_reasons: List[str] = []
        warning_reasons: List[str] = []

        # 关卡 1：造血纯度筛查
        purity_res = self.purity_engine.evaluate(record)
        if purity_res.is_veto:
            veto_reasons.append(f"【造血毒性否决】{purity_res.diagnosis}")
        elif purity_res.is_warning:
            warning_reasons.append(f"【造血预警】{purity_res.diagnosis}")

        # 关卡 2：债务毒性筛查
        debt_res = self.debt_engine.evaluate(record)
        if debt_res.is_veto:
            veto_reasons.append(f"【债务猝死否决】{debt_res.diagnosis}")
        elif debt_res.is_warning:
            warning_reasons.append(f"【债务预警】{debt_res.diagnosis}")

        # 关卡 3：资产负债表排毒
        bs = record.balance_sheet
        if bs.goodwill_to_equity > self.max_goodwill_to_equity:
            veto_reasons.append(
                f"【商誉减值炸弹】商誉/净资产={bs.goodwill_to_equity*100:.1f}% "
                f"超过上限 {self.max_goodwill_to_equity*100:.1f}%"
            )

        if bs.debt_to_assets > self.max_debt_to_assets:
            veto_reasons.append(
                f"【杠杆过高否决】资产负债率={bs.debt_to_assets*100:.1f}% "
                f"突破警戒线 {self.max_debt_to_assets*100:.1f}%"
            )

        # 关卡 4：受限资金筛查（康美药业式存贷双高/大额受限假资金）
        if bs.cash_and_equivalents > 0:
            restricted_ratio = bs.restricted_cash / bs.cash_and_equivalents
            if restricted_ratio > self.max_restricted_cash_ratio:
                veto_reasons.append(
                    f"【资金虚假疑云】受限资金占货币资金={restricted_ratio*100:.1f}% "
                    f"超过红线 {self.max_restricted_cash_ratio*100:.1f}%"
                )

        # 最终准入判定：一票否决，清白者方能准入
        is_admitted = (len(veto_reasons) == 0)

        return FirewallAuditReport(
            symbol=record.symbol,
            period_end_date=record.period_end_date,
            is_admitted=is_admitted,
            veto_reasons=veto_reasons,
            warning_reasons=warning_reasons,
            cash_purity=purity_res,
            debt_wall=debt_res
        )

    def screen_universe(
        self,
        records: List[CompanyFinancialRecord]
    ) -> Tuple[List[CompanyFinancialRecord], List[FirewallAuditReport]]:
        """
        批量筛选股票池
        :return: (准入的洁净标的列表, 全体体检报告清单)
        """
        clean_universe: List[CompanyFinancialRecord] = []
        all_reports: List[FirewallAuditReport] = []

        for r in records:
            report = self.audit(r)
            all_reports.append(report)
            if report.is_admitted:
                clean_universe.append(r)

        return clean_universe, all_reports
