"""
entropy_execution/profit_integrity_guard.py
=============================================
最高宪法第24条：盈利真实性守恒与单向棘轮风控守卫中枢。

核心第一性原理：
1. 单向棘轮风控守恒：风控参数只准从严，绝不允许因追求盈利而从宽；
2. 戴着镣铐起舞：真实盈利必须扣除全额摩擦并在严酷风控约束下达成；
3. 婴幼儿毒蘑菇绝对阻断：对造血造假、债务压顶的毒资产行使一票否决权！
严格恪守单文件不超过 300 行，强类型注解，零伪 Mock。
"""

from dataclasses import dataclass
from enum import Enum
import math
from typing import Any, Dict, List, Optional, Tuple


class RiskRelaxationForbiddenError(Exception):
    """严禁为迎合盈利而放宽风控异常"""
    pass


class ToxicMushroomViolationError(Exception):
    """外行毒蘑菇资产强行上桌违宪异常"""
    pass


class IntegrityVerdict(str, Enum):
    """盈利真实性审核结论"""
    VERIFIED_AUTHENTIC = "VERIFIED_AUTHENTIC"
    REJECT_ZERO_FRICTION = "REJECT_ZERO_FRICTION"
    REJECT_RISK_RELAXATION = "REJECT_RISK_RELAXATION"
    REJECT_TOXIC_MUSHROOM = "REJECT_TOXIC_MUSHROOM"
    REJECT_MOVING_STOP_LOSS = "REJECT_MOVING_STOP_LOSS"
    REJECT_TAIL_MASKING = "REJECT_TAIL_MASKING"


@dataclass(frozen=True)
class ProfitAuditReport:
    """策略盈利真实性审计证书"""
    is_approved: bool
    verdict: IntegrityVerdict
    explanation: str
    net_profit_after_friction: float
    total_friction_paid: float
    max_drawdown_observed: float
    toddler_warning: str


class ProfitIntegrityGuard:
    """盈利真实性与单向棘轮风控刚性守卫"""

    # 宪法级不可逾越之风控基准底线（单向棘轮基准）
    BASELINE_LIMITS: Dict[str, float] = {
        "max_daily_drawdown": 0.02,        # 单日最大亏损熔断：不得大于 2%
        "max_single_stock_ratio": 0.30,    # 单标的持仓集中度：不得大于 30%
        "max_single_loss_stop": 0.05,      # 单笔硬止损红线：不得大于 5%
        "min_blood_purity": 0.30,          # 造血纯度 Φ_CP 底线：不得低于 0.30
        "max_debt_toxicity": 0.40,         # 债务毒性 Ω_Debt 上限：不得高于 0.40
        "min_stamp_tax": 0.0005,           # 印花税率底线：不得低于 0.05%
        "min_commission": 0.0002,          # 双边佣金底线：不得低于 0.02%
        "min_slippage": 0.0010,            # 冲击滑点底线：不得低于 0.10%
    }

    @classmethod
    def validate_parameter_update(
        cls, param_name: str, current_val: float, proposed_val: float
    ) -> bool:
        """
        单向棘轮风控校验：只准从严，绝不准从宽！
        若试图为了追求盈利而放宽风控参数，立刻抛出异常并物理拦截！
        """
        if param_name not in cls.BASELINE_LIMITS:
            return True

        # 上限型参数（越小越严格）：proposed 绝不能大于 current，更不能大于 BASELINE
        if param_name in ("max_daily_drawdown", "max_single_stock_ratio", "max_single_loss_stop", "max_debt_toxicity"):
            if proposed_val > current_val or proposed_val > cls.BASELINE_LIMITS[param_name]:
                raise RiskRelaxationForbiddenError(
                    f"【宪法物理拦截】严禁为了表面盈利放宽风控参数 `{param_name}`！"
                    f"当前设定: {current_val}, 试图放宽至: {proposed_val} (宪法基准上限: {cls.BASELINE_LIMITS[param_name]})。"
                    "风控参数只准从严（调小），绝不准从宽！"
                )

        # 下限型参数（越大越严格）：proposed 绝不能小于 current，更不能小于 BASELINE
        if param_name in ("min_blood_purity", "min_stamp_tax", "min_commission", "min_slippage"):
            if proposed_val < current_val or proposed_val < cls.BASELINE_LIMITS[param_name]:
                raise RiskRelaxationForbiddenError(
                    f"【宪法物理拦截】严禁为了虚假盈利降低合规门槛 `{param_name}`！"
                    f"当前设定: {current_val}, 试图降门槛至: {proposed_val} (宪法基准下限: {cls.BASELINE_LIMITS[param_name]})。"
                    "门槛与摩擦只准从严（调大），绝不准从宽！"
                )

        return True

    @classmethod
    def inspect_toddler_mushroom_safety(
        cls,
        symbol: str,
        blood_purity: float,
        debt_toxicity: float,
        pledge_ratio: float = 0.0
    ) -> Tuple[bool, str]:
        """
        婴幼儿毒蘑菇绝对阻断测试：
        外行用户无法分辨企业造假，系统必须充当绝对不可腐蚀的物理守门人。
        """
        reasons: List[str] = []
        if blood_purity < cls.BASELINE_LIMITS["min_blood_purity"]:
            reasons.append(f"经营现金流造血纯度仅 {blood_purity:.2f} (低于安全线 0.30)，属借钱补贴假造血")
        if debt_toxicity > cls.BASELINE_LIMITS["max_debt_toxicity"]:
            reasons.append(f"短债流动性毒性达 {debt_toxicity:.2f} (高于警戒线 0.40)，随时面临债务违约猝死")
        if pledge_ratio > 0.50:
            reasons.append(f"大股东股权质押比例达 {pledge_ratio*100:.1f}%，存在平仓踩踏爆仓风险")

        if reasons:
            warn = f"🍄【剧毒蘑菇绝对拦截】标的 {symbol} 存在致命毒素：" + "；".join(reasons) + "！系统一票否决，绝不端上桌！"
            return False, warn

        return True, f"🟢 标的 {symbol} 造血纯净，无毒无害，通过婴幼儿安全防线。"

    @classmethod
    def audit_profit_claim(
        cls,
        gross_profit: float,
        friction_paid: float,
        trades_count: int,
        max_drawdown: float,
        has_toxic_assets: bool = False,
        stop_loss_loosened: bool = False
    ) -> ProfitAuditReport:
        """
        综合审计策略收益真实性：
        杜绝通过零摩擦、放宽止损、引入有毒标的换取的“假盈利”。
        """
        # 1. 检验有毒资产掺杂
        if has_toxic_assets:
            return ProfitAuditReport(
                is_approved=False,
                verdict=IntegrityVerdict.REJECT_TOXIC_MUSHROOM,
                explanation="策略中掺杂了未通过免疫系统的剧毒蘑菇标的，试图用高风险重组博取虚假年化！",
                net_profit_after_friction=gross_profit - friction_paid,
                total_friction_paid=friction_paid,
                max_drawdown_observed=max_drawdown,
                toddler_warning="有毒标的可能导致本金永久归零，一票否决！"
            )

        # 2. 检验止损移动作弊
        if stop_loss_loosened:
            return ProfitAuditReport(
                is_approved=False,
                verdict=IntegrityVerdict.REJECT_MOVING_STOP_LOSS,
                explanation="策略在浮亏过程中擅自推迟止损线（坐等回本欺骗），属于恶意操纵账面胜率！",
                net_profit_after_friction=gross_profit - friction_paid,
                total_friction_paid=friction_paid,
                max_drawdown_observed=max_drawdown,
                toddler_warning="推迟止损是巨亏爆仓的罪魁祸首，当场熔断！"
            )

        # 3. 检验摩擦成本计提
        if trades_count > 0 and friction_paid <= 0:
            return ProfitAuditReport(
                is_approved=False,
                verdict=IntegrityVerdict.REJECT_ZERO_FRICTION,
                explanation="策略产生真实交易却计提 0 元摩擦，属于无摩擦数字炼金术！",
                net_profit_after_friction=gross_profit,
                total_friction_paid=0.0,
                max_drawdown_observed=max_drawdown,
                toddler_warning="零摩擦策略在实盘中必因手续费和滑点亏光本金！"
            )

        net_profit = gross_profit - friction_paid
        if net_profit <= 0:
            return ProfitAuditReport(
                is_approved=False,
                verdict=IntegrityVerdict.REJECT_TAIL_MASKING,
                explanation=f"毛利 {gross_profit:.2f} 扣除真实摩擦 {friction_paid:.2f} 后实际净亏损 {net_profit:.2f}，属于虚假繁荣！",
                net_profit_after_friction=net_profit,
                total_friction_paid=friction_paid,
                max_drawdown_observed=max_drawdown,
                toddler_warning="扣除税费后本金受损，不能端给用户！"
            )

        # 4. 真实合规盈利
        return ProfitAuditReport(
            is_approved=True,
            verdict=IntegrityVerdict.VERIFIED_AUTHENTIC,
            explanation=f"策略在全摩擦（已付 {friction_paid:.2f} 元）与严酷风控下获得真实净利 {net_profit:.2f} 元，真实生存！",
            net_profit_after_friction=net_profit,
            total_friction_paid=friction_paid,
            max_drawdown_observed=max_drawdown,
            toddler_warning="✅ 经对抗审计与毒蘑菇排查，该收益为真实物理期望收益，安全放心。"
        )
