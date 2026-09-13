"""
immune_system.cash_purity
~~~~~~~~~~~~~~~~~~~~~~~~~
实现造血纯度 Φ_CP (Cash Purity Index) 计算引擎。
穿透权责发生制粉饰，严密测量净利润背后的真实物理现金流转化效率。
"""

from dataclasses import dataclass
from typing import Optional
from truth_kernel.models import CompanyFinancialRecord


@dataclass(frozen=True)
class CashPurityAssessment:
    """造血纯度评估审计结果"""
    symbol: str
    period_end_date: str
    phi_cp: float                     # 综合造血纯度指数 Φ_CP
    cash_conversion_ratio: float      # 现金转化乘数 (OCF - ΔWC) / (NetProfit + D&A)
    receivables_burden_ratio: float   # 应收账款占营收比
    is_veto: bool                     # 是否触发一票否决红线
    is_warning: bool                  # 是否触发预警黄线
    diagnosis: str                    # 审计诊断明细报告


class CashPurityEngine:
    """
    造血纯度核算与假账识别引擎
    数学公式：
    Φ_CP = [(OCF - ΔWC) / (max(1, |NetProfit|) + DeprAmort)] * [1 - min(Rev, Rec) / max(1, Rev)]
    """

    def __init__(
        self,
        veto_threshold: float = 0.30,
        warning_threshold: float = 0.60,
        max_receivables_ratio: float = 0.50
    ) -> None:
        self.veto_threshold = veto_threshold
        self.warning_threshold = warning_threshold
        self.max_receivables_ratio = max_receivables_ratio

    def evaluate(self, record: CompanyFinancialRecord) -> CashPurityAssessment:
        """对单期财报执行造血纯度穿透测试"""
        bs = record.balance_sheet
        inc = record.income_statement
        cf = record.cash_flow_statement

        # 1. 提取核心指标并进行防御性兜底
        ocf = cf.operating_cash_flow
        delta_wc = cf.working_capital_change
        net_profit = inc.net_profit
        depr_amort = max(0.0, cf.depreciation_amortization)
        revenue = max(0.0, inc.revenue)
        receivables = max(0.0, bs.receivables)

        # 真实自主经营造血现金 = OCF - 营运资本变动（排除存货与账面往来虚增）
        clean_ocf = ocf - delta_wc

        # 2. 计算基准分母：利润基数 + 折旧摊销
        denominator = max(1.0, abs(net_profit)) + depr_amort

        # 3. 现金转化乘数
        if net_profit < 0 and clean_ocf < 0:
            # 利润与现金双双亏损，造血能力为负
            cash_conversion_ratio = clean_ocf / denominator
        elif net_profit > 0 and clean_ocf <= 0:
            # 典型造假特征：账面繁荣盈利，实则失血
            cash_conversion_ratio = clean_ocf / denominator
        else:
            cash_conversion_ratio = clean_ocf / denominator

        # 4. 应收账款拖累项 (Receivables Burden)
        if revenue > 0:
            receivables_ratio = min(1.0, receivables / revenue)
        else:
            # 零收入却有应收账款，拖累拉满
            receivables_ratio = 1.0 if receivables > 0 else 0.0

        purity_multiplier = max(0.0, 1.0 - receivables_ratio)

        # 5. 计算综合造血纯度 Φ_CP
        phi_cp = cash_conversion_ratio * purity_multiplier

        # 6. 判定否决与预警条件
        is_veto = False
        is_warning = False
        reasons = []

        if phi_cp < self.veto_threshold:
            is_veto = True
            reasons.append(f"造血纯度 Φ_CP={phi_cp:.3f} 低于红线 {self.veto_threshold:.2f}")

        if receivables_ratio > self.max_receivables_ratio:
            is_veto = True
            reasons.append(
                f"应收账款占营收比={receivables_ratio*100:.1f}% 超过警戒红线 "
                f"{self.max_receivables_ratio*100:.1f}% (资金严重滞留欠条)"
            )

        if not is_veto and phi_cp < self.warning_threshold:
            is_warning = True
            reasons.append(f"造血纯度 Φ_CP={phi_cp:.3f} 进入观察预警区间 [{self.veto_threshold:.2f}, {self.warning_threshold:.2f}]")

        diagnosis = " | ".join(reasons) if reasons else "造血能力纯净健全，现金流含金量高。"

        return CashPurityAssessment(
            symbol=record.symbol,
            period_end_date=record.period_end_date,
            phi_cp=round(phi_cp, 4),
            cash_conversion_ratio=round(cash_conversion_ratio, 4),
            receivables_burden_ratio=round(receivables_ratio, 4),
            is_veto=is_veto,
            is_warning=is_warning,
            diagnosis=diagnosis
        )
