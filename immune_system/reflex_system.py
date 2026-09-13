"""
immune_system/reflex_system.py
==============================
TRINITY QUANT 仿生神经反射与多层认知控制中枢。

仿生人类中枢与自主神经系统：
1. 原始反射 (Spinal Primitive Reflex): 脊髓级零延迟本能脱险 (触火缩手，黑天鹅毫秒级熔断);
2. 条件/自主反射 (Autonomic Reflex): 随波动率呼吸的自适应调节 (内稳态维持);
3. 大脑皮层认知体系 (Cognitive System): 深度微观财务尸检、商业模式与宏观周期透视;
4. 前馈与闭环反馈控制 (Feedforward & Feedback Loop): 前瞻预警与误差动态纠偏。
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ReflexLevel(str, Enum):
    """反射控制分级"""
    PRIMITIVE_SPINAL = "PRIMITIVE_SPINAL"      # 脊髓原始本能反射 (零思考，生死瞬间)
    AUTONOMIC_HOMEO = "AUTONOMIC_HOMEO"        # 自主神经内稳态调节 (动态呼吸，平滑调节)
    CORTICAL_COGNITIVE = "CORTICAL_COGNITIVE"  # 大脑皮层高级认知决策 (深度博弈，周期推演)


@dataclass(frozen=True)
class BioReflexCommand:
    """仿生反射输出指令"""
    level: ReflexLevel
    symbol: str
    action_type: str
    bypass_deliberation: bool                  # 是否越过思考中枢强制执行
    response_latency_budget_ms: float          # 允许响应耗时预算 (毫秒)
    action_payload: str


class BioReflexCentral:
    """仿生神经反射控制中枢"""

    def __init__(self, panic_gap_threshold: float = 0.07) -> None:
        if panic_gap_threshold <= 0:
            raise ValueError("恐慌跳空阈值必须大于0")
        self._panic_gap = panic_gap_threshold

    def evaluate_primitive_reflex(
        self,
        symbol: str,
        instant_price_drop_pct: float,
        is_limit_down_locked: bool,
        is_data_corrupted: bool
    ) -> Optional[BioReflexCommand]:
        """
        【原始反射 / 脊髓弧】零思考、零延迟的生物生存本能
        正如手触碰到烙铁，脊髓弧在痛觉信号到达大脑皮层前 15 毫秒已强制肌肉缩回！
        """
        sym = symbol.upper()

        # 1. 致命数据静默污染 -> 瞬间切断报单，冻结通道
        if is_data_corrupted:
            return BioReflexCommand(
                level=ReflexLevel.PRIMITIVE_SPINAL,
                symbol=sym,
                action_type="EMERGENCY_FREEZE_GATE",
                bypass_deliberation=True,
                response_latency_budget_ms=1.0,
                action_payload="数据源突发物理级污染，脊髓原始反射瞬间切断下单网关"
            )

        # 2. 闪崩或跳空暴跌击穿阈值 -> 原始反射清仓避险
        if instant_price_drop_pct <= -self._panic_gap:
            return BioReflexCommand(
                level=ReflexLevel.PRIMITIVE_SPINAL,
                symbol=sym,
                action_type="PANIC_EMERGENCY_EXIT",
                bypass_deliberation=True,
                response_latency_budget_ms=2.0,
                action_payload=f"瞬时闪崩暴跌 {instant_price_drop_pct*100:.1f}% 触发脊髓避险反射，绕过认知中枢强制市价全平！"
            )

        return None

    def evaluate_autonomic_reflex(
        self,
        symbol: str,
        current_volatility_z: float,
        profit_drawdown_from_peak: float
    ) -> BioReflexCommand:
        """
        【自主神经 / 条件反射】交感与副交感神经的动态内稳态维持
        根据外部市场波动率呼吸，自动收缩或扩张风险敞口。
        """
        sym = symbol.upper()

        # 利润高位大幅回撤 -> 条件反射锁利
        if profit_drawdown_from_peak >= 0.08:
            return BioReflexCommand(
                level=ReflexLevel.AUTONOMIC_HOMEO,
                symbol=sym,
                action_type="RATCHET_LOCK_PROFIT",
                bypass_deliberation=False,
                response_latency_budget_ms=10.0,
                action_payload="利润回撤突破内稳态警戒线(8%)，自主神经触发阶梯平仓锁利"
            )

        # 波动率异常发散 -> 自主神经下压杠杆
        if abs(current_volatility_z) > 2.2:
            return BioReflexCommand(
                level=ReflexLevel.AUTONOMIC_HOMEO,
                symbol=sym,
                action_type="SCALE_DOWN_EXPOSURE",
                bypass_deliberation=False,
                response_latency_budget_ms=20.0,
                action_payload="市场进入高波发散态，自主神经自动压低持仓敞口以平抑心跳"
            )

        return BioReflexCommand(
            level=ReflexLevel.AUTONOMIC_HOMEO,
            symbol=sym,
            action_type="EQUILIBRIUM_MAINTAINED",
            bypass_deliberation=False,
            response_latency_budget_ms=50.0,
            action_payload="内稳态生理平衡正常"
        )
