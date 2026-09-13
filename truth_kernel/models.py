"""
truth_kernel.models
~~~~~~~~~~~~~~~~~~~
定义严格强类型的底层企业财务数据结构与点时（Point-in-Time）记录。
所有字段均具备类型注解与防御性数值合法性检验。
"""

from dataclasses import dataclass, field
from typing import Optional
import math


@dataclass(frozen=True)
class BalanceSheet:
    """资产负债表核心项（单位：元）"""
    total_assets: float
    total_liabilities: float
    total_equity: float
    cash_and_equivalents: float
    restricted_cash: float = 0.0
    receivables: float = 0.0
    inventory: float = 0.0
    goodwill: float = 0.0
    short_term_debt: float = 0.0
    long_term_debt_due_within_1y: float = 0.0
    commercial_paper: float = 0.0

    def __post_init__(self) -> None:
        if self.total_assets < 0:
            raise ValueError(f"总资产不能为负: {self.total_assets}")
        if self.cash_and_equivalents < 0:
            raise ValueError(f"货币资金不能为负: {self.cash_and_equivalents}")
        if self.restricted_cash < 0 or self.restricted_cash > self.cash_and_equivalents:
            raise ValueError(f"受限资金数值异常: 受限={self.restricted_cash}, 总货币={self.cash_and_equivalents}")

    @property
    def total_due_1y(self) -> float:
        """未来 12 个月内硬性刚性到期债务总额"""
        return self.short_term_debt + self.long_term_debt_due_within_1y + self.commercial_paper

    @property
    def real_liquid_cash(self) -> float:
        """可自由动用的真实流动性资金（扣除质押与受限资金）"""
        return max(0.0, self.cash_and_equivalents - self.restricted_cash)

    @property
    def debt_to_assets(self) -> float:
        """资产负债率"""
        return self.total_liabilities / max(1.0, self.total_assets)

    @property
    def goodwill_to_equity(self) -> float:
        """商誉占股东权益比"""
        if self.total_equity <= 0:
            return 1.0  # 资不抵债，毒性直接拉满
        return max(0.0, self.goodwill / self.total_equity)


@dataclass(frozen=True)
class IncomeStatement:
    """利润表核心项（单位：元）"""
    revenue: float
    operating_profit: float
    net_profit: float
    financial_expenses: float = 0.0
    ebitda: Optional[float] = None

    def __post_init__(self) -> None:
        if self.revenue < 0:
            raise ValueError(f"营业收入不能为负: {self.revenue}")

    @property
    def computed_ebitda(self) -> float:
        """若未显式提供 EBITDA，则使用营业利润 + 财务费用保守近似"""
        if self.ebitda is not None and not math.isnan(self.ebitda):
            return self.ebitda
        return max(0.0, self.operating_profit + max(0.0, self.financial_expenses))


@dataclass(frozen=True)
class CashFlowStatement:
    """现金流量表核心项（单位：元，造血核心）"""
    operating_cash_flow: float  # 经营活动现金流量净额 (OCF)
    capex: float                # 购建固定资产等支付的资本开支
    working_capital_change: float = 0.0  # 营运资本变动
    depreciation_amortization: float = 0.0  # 折旧与摊销

    @property
    def free_cash_flow(self) -> float:
        """自由现金流 (FCF = OCF - CapEx)"""
        return self.operating_cash_flow - self.capex


@dataclass(frozen=True)
class CompanyFinancialRecord:
    """
    点时（Point-in-Time）公司财务全景记录
    严格绑定实际披露日，抹除一切先知未来函数。
    """
    symbol: str
    period_end_date: str     # 会计报告期截止日 (如 2023-12-31)
    disclosure_date: str     # 真实法定披露日期 (如 2024-04-25)
    balance_sheet: BalanceSheet
    income_statement: IncomeStatement
    cash_flow_statement: CashFlowStatement

    def __post_init__(self) -> None:
        if not self.symbol:
            raise ValueError("股票代码不能为空")
        if self.disclosure_date < self.period_end_date:
            raise ValueError(
                f"时点逻辑悖论：披露日 ({self.disclosure_date}) 不得早于报告期截止日 ({self.period_end_date})"
            )
