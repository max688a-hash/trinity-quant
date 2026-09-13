"""
entropy_execution/capital_scale_morpher.py
==========================================
TRINITY QUANT 资金体量动态形态演进中枢 (Scale-Adaptive Capital Morphing Engine)。
打破“机构繁重合规硬套个人小资金”的荒谬教条：
1. 阶梯 1: 游击狙击型 (MICRO_GUERRILLA) [¥10,000 ~ ¥100,000]:
   - 目标：极高灵活性、集中优势火力、严禁细碎拆单避免 5 元最低佣金惩罚；
2. 阶梯 2: 巡航突击型 (TACTICAL_CRUISER) [¥100,000 ~ ¥1,000,000]:
   - 目标：攻守平衡、配置 3~5 只标的、半凯利方差压制；
3. 阶梯 3: 重装战舰型 (DREADNOUGHT_FLEET) [¥1,000,000 ~ ¥5,000,000]:
   - 目标：平滑资金曲线、轻量级冰山隐匿单、多市场跨期对冲；
4. 阶梯 4: 航母巨鲸型 (WHALE_CARRIER) [¥5,000,000 以上]:
   - 目标：流动性容量优先、Almgren-Chriss 冲击最小化、严格日内硬风控。
严格遵循最高宪法：单文件不超过 300 行，强类型契约，无伪 Mock。
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict


class CapitalScaleTier(str, Enum):
    """资金体量演进阶梯"""
    MICRO_GUERRILLA = "MICRO_GUERRILLA"      # 游击狙击型 (1万~10万)
    TACTICAL_CRUISER = "TACTICAL_CRUISER"    # 巡航突击型 (10万~100万)
    DREADNOUGHT_FLEET = "DREADNOUGHT_FLEET"  # 重装战舰型 (100万~500万)
    WHALE_CARRIER = "WHALE_CARRIER"          # 航母巨鲸型 (500万以上)


@dataclass(frozen=True)
class ScaleAdaptiveProfile:
    """资金体量自适应运行画像"""
    tier: CapitalScaleTier
    current_equity: float
    max_concentration_ratio: float           # 单标的最大持仓占比 (小资金高集中度，大资金分散)
    max_single_notional: float               # 单笔委托金额上限
    enable_algorithmic_slicing: bool         # 是否开启算法拆单 (小资金严禁拆单防吃5元低佣惩罚)
    min_commission_defense: bool             # 5元最低佣金防夹伤保护
    target_asset_count: int                  # 目标配置标的数 (小资金1~3只，大资金10~25只)
    daily_drawdown_circuit_breaker_pct: float# 日内最大回撤熔断阈值
    display_title: str
    battle_philosophy: str


class CapitalScaleMorpher:
    """资金体量自适应形态变形器"""

    @staticmethod
    def resolve_profile(equity: float) -> ScaleAdaptiveProfile:
        """根据真实账户净值，自适应推导最佳战术形态参数"""
        eq = max(1_000.0, float(equity))

        # 1. 游击狙击型: 1万 ~ 10万 (专注个人小资金)
        if eq < 100_000.0:
            return ScaleAdaptiveProfile(
                tier=CapitalScaleTier.MICRO_GUERRILLA,
                current_equity=eq,
                max_concentration_ratio=0.60,       # 允许集中火力持有1~2只真金好资产
                max_single_notional=eq * 0.60,      # 单笔上限随资金自适应
                enable_algorithmic_slicing=False,   # 严禁细碎拆单！防止每一笔都被收5元保底佣金
                min_commission_defense=True,        # 开启小资金防佣金夹伤
                target_asset_count=2,               # 集中配置 1~2 只核心龙头或1手期货
                daily_drawdown_circuit_breaker_pct=0.04,  # 小资金适当放宽日内波动容忍度至4%
                display_title="游击狙击形态 (Guerrilla Sniper)",
                battle_philosophy="集中优势兵力，零拆单防佣金磨损，打得赢就打，打不赢就跑"
            )

        # 2. 巡航突击型: 10万 ~ 100万 (个人成长与大户进阶)
        elif eq < 1_000_000.0:
            return ScaleAdaptiveProfile(
                tier=CapitalScaleTier.TACTICAL_CRUISER,
                current_equity=eq,
                max_concentration_ratio=0.35,       # 单票最高35%，持仓3~4只
                max_single_notional=min(300_000.0, eq * 0.35),
                enable_algorithmic_slicing=False,   # 普通限价挂单即可
                min_commission_defense=True,
                target_asset_count=4,
                daily_drawdown_circuit_breaker_pct=0.03,
                display_title="巡航突击形态 (Tactical Cruiser)",
                battle_philosophy="攻守兼备，动态凯利仓位配比，兼顾高弹性收益与回撤保护"
            )

        # 3. 重装战舰型: 100万 ~ 500万 (高净值与准机构)
        elif eq < 5_000_000.0:
            return ScaleAdaptiveProfile(
                tier=CapitalScaleTier.DREADNOUGHT_FLEET,
                current_equity=eq,
                max_concentration_ratio=0.20,       # 单票上限20%，配置5~8只
                max_single_notional=500_000.0,
                enable_algorithmic_slicing=True,    # 开启轻量级冰山拆单隐匿意图
                min_commission_defense=False,       # 资金体量已跨过保底佣金门槛
                target_asset_count=7,
                daily_drawdown_circuit_breaker_pct=0.02,  # 严格日内2%硬风控
                display_title="重装战舰形态 (Dreadnought Fleet)",
                battle_philosophy="跨市场多品种资产配置，以方差拖累压制驱动长期复利"
            )

        # 4. 航母巨鲸型: 500万以上 (机构级大资金与私募规模)
        else:
            return ScaleAdaptiveProfile(
                tier=CapitalScaleTier.WHALE_CARRIER,
                current_equity=eq,
                max_concentration_ratio=0.12,       # 单票上限12%，持仓10~25只防流动性黑天鹅
                max_single_notional=1_000_000.0,
                enable_algorithmic_slicing=True,    # 全量开启 TWAP/VWAP 与 Almgren-Chriss 冲击优化
                min_commission_defense=False,
                target_asset_count=15,
                daily_drawdown_circuit_breaker_pct=0.015, # 极严日内 1.5% 拔插头熔断
                display_title="航母巨鲸形态 (Whale Carrier)",
                battle_philosophy="流动性容量第一，冲击滑点最小化，机构级硬性防穿透"
            )
