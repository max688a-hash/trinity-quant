"""
gravity_brain/institutional_turtle.py
=====================================
TRINITY QUANT 机构级全功能海龟交易系统 (Institutional Turtle Engine)。

拒绝空壳与简陋玩具：
1. 肌肉: N (ATR_20) 波动率归一化绝对风险 Unit 头寸规模算法;
2. 神经: System 1 (20日突破) + System 2 (55日突破) 双轨制,
         含机构级“上一笔盈利则跳过当前 S1 突破”的真值防假突破滤网;
3. 骨骼: 金字塔加仓法则 (+0.5N 加仓 1 Unit, 最多 4 Units) 与
         全局统一直播止损线 (最新加仓价 - 2N);
4. 灵魂: 融合 TRINITY QUANT 免疫排毒防火墙，毒性标的一票否决。
"""

import math
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Sequence


class TurtleSystemType(str, Enum):
    """海龟子系统类型"""
    SYSTEM_1 = "SYSTEM_1"  # 20日突破入场，10日反向离场 (含上一单胜负过滤)
    SYSTEM_2 = "SYSTEM_2"  # 55日突破入场，20日反向离场 (长线超级趋势保底)


class TurtleSignalType(str, Enum):
    """海龟信号类型"""
    NO_SIGNAL = "NO_SIGNAL"
    ENTRY_INIT_UNIT = "ENTRY_INIT_UNIT"      # 建立初始 1 Unit
    PYRAMID_ADD_UNIT = "PYRAMID_ADD_UNIT"    # +0.5N 金字塔加仓
    EXIT_ALL_UNITS = "EXIT_ALL_UNITS"        # 触及出场线或 2N 止损全平


@dataclass(frozen=True)
class TurtlePositionUnit:
    """单个 Unit 记录"""
    unit_index: int
    entry_price: float
    quantity: float


@dataclass(frozen=True)
class TurtleDecision:
    """海龟机构级决策"""
    symbol: str
    signal: TurtleSignalType
    system_type: TurtleSystemType
    n_volatility: float
    unit_size: float
    stop_price: float
    current_units_count: int
    reason: str


class InstitutionalTurtleEngine:
    """机构级全功能海龟交易引擎"""

    def __init__(
        self,
        risk_fraction_per_unit: float = 0.01,
        max_units_per_asset: int = 4
    ) -> None:
        if risk_fraction_per_unit <= 0 or risk_fraction_per_unit > 0.05:
            raise ValueError("单 Unit 风险敞口必须在 (0, 0.05] 之间")
        self._risk_fraction = risk_fraction_per_unit
        self._max_units = max_units_per_asset
        # 记录每个品种 System 1 上一笔交易是否盈利 (True 为盈利则跳过下一次突破)
        self._last_s1_was_win: dict[str, bool] = {}

    def calculate_n(self, highs: Sequence[float], lows: Sequence[float], closes: Sequence[float], window: int = 20) -> float:
        """计算海龟波动率参数 N = 20期 True Range 的均值"""
        n_len = len(closes)
        if n_len < window:
            raise ValueError(f"数据长度 {n_len} 低于 N 计算窗口 {window}")

        tr_list: List[float] = []
        for i in range(1, n_len):
            h = highs[i]
            l = lows[i]
            c_prev = closes[i - 1]
            tr = max(h - l, abs(h - c_prev), abs(l - c_prev))
            tr_list.append(tr)

        recent_tr = tr_list[-(window):]
        return sum(recent_tr) / float(len(recent_tr))

    def calculate_unit_size(
        self,
        equity: float,
        n_volatility: float,
        contract_multiplier: float
    ) -> float:
        """
        计算 1 个 Unit 的头寸规模:
        Dollar Volatility = N * Multiplier
        Unit = (1% * Equity) / Dollar Volatility
        """
        if equity <= 0 or n_volatility <= 0 or contract_multiplier <= 0:
            return 0.0
        dollar_volatility = n_volatility * contract_multiplier
        one_pct_risk = equity * self._risk_fraction
        unit_qty = math.floor(one_pct_risk / dollar_volatility)
        return max(1.0, float(unit_qty))

    def evaluate_signals(
        self,
        symbol: str,
        current_price: float,
        closes_history: Sequence[float],
        highs_history: Sequence[float],
        lows_history: Sequence[float],
        equity: float,
        contract_multiplier: float,
        existing_units: Sequence[TurtlePositionUnit] = (),
        is_fundamental_clean: bool = True
    ) -> TurtleDecision:
        """
        全功能海龟状态机
        """
        sym = symbol.upper()
        if not is_fundamental_clean:
            # 灵魂过滤：基本面存毒或造假，一票剥夺入场资格
            return TurtleDecision(sym, TurtleSignalType.NO_SIGNAL, TurtleSystemType.SYSTEM_1, 0.0, 0.0, 0.0, len(existing_units), "标的未通过真值排毒防火墙，海龟引擎禁止建仓")

        n_val = self.calculate_n(highs_history, lows_history, closes_history, 20)
        unit_size = self.calculate_unit_size(equity, n_val, contract_multiplier)

        # 获取历史通道边界 (不含当前根 K 线)
        prev_closes = closes_history[:-1]
        s1_high_20 = max(prev_closes[-20:]) if len(prev_closes) >= 20 else current_price * 2
        s1_low_10 = min(prev_closes[-10:]) if len(prev_closes) >= 10 else 0.0
        s2_high_55 = max(prev_closes[-55:]) if len(prev_closes) >= 55 else current_price * 2
        s2_low_20 = min(prev_closes[-20:]) if len(prev_closes) >= 20 else 0.0

        n_units = len(existing_units)

        # 1. 检查已有多头持仓的出场或止损
        if n_units > 0:
            latest_entry = existing_units[-1].entry_price
            unified_stop = latest_entry - (2.0 * n_val)

            # 触及 2N 止损或 10日低点出场
            if current_price <= unified_stop or current_price <= s1_low_10:
                was_win = current_price > existing_units[0].entry_price
                self._last_s1_was_win[sym] = was_win
                return TurtleDecision(sym, TurtleSignalType.EXIT_ALL_UNITS, TurtleSystemType.SYSTEM_1, n_val, 0.0, unified_stop, n_units, f"触及出场线 (止损价 {unified_stop:.2f} 或 10日低点 {s1_low_10:.2f})")

            # 金字塔加仓检查 (+0.5N 加仓 1 Unit)
            if n_units < self._max_units:
                next_pyramid_price = latest_entry + (0.5 * n_val)
                if current_price >= next_pyramid_price:
                    new_stop = current_price - (2.0 * n_val)
                    return TurtleDecision(sym, TurtleSignalType.PYRAMID_ADD_UNIT, TurtleSystemType.SYSTEM_1, n_val, unit_size, new_stop, n_units + 1, f"达到加仓阈值(+0.5N={next_pyramid_price:.2f})，金字塔加仓第 {n_units+1} Unit")

            return TurtleDecision(sym, TurtleSignalType.NO_SIGNAL, TurtleSystemType.SYSTEM_1, n_val, 0.0, unified_stop, n_units, "持仓健康运行中")

        # 2. 空仓状态，评估初始入场
        # System 1: 突破 20 日高点
        if current_price > s1_high_20:
            # 机构级胜负过滤：若上一单是盈利的，跳过当前 S1 突破以避开假突破震荡
            if self._last_s1_was_win.get(sym, False):
                # 检查是否突破 55 日高点 (System 2 兜底大趋势)
                if current_price > s2_high_55:
                    return TurtleDecision(sym, TurtleSignalType.ENTRY_INIT_UNIT, TurtleSystemType.SYSTEM_2, n_val, unit_size, current_price - 2*n_val, 1, "S1上次盈利过滤生效，激活 S2 突破 55 日高点超级趋势入场")
                return TurtleDecision(sym, TurtleSignalType.NO_SIGNAL, TurtleSystemType.SYSTEM_1, n_val, 0.0, 0.0, 0, "S1 突破被胜负滤网过滤 (上一单盈利，跳过本单防震荡)")
            
            return TurtleDecision(sym, TurtleSignalType.ENTRY_INIT_UNIT, TurtleSystemType.SYSTEM_1, n_val, unit_size, current_price - 2*n_val, 1, "突破 20 日高点，海龟 System 1 建立初始头寸")

        # System 2: 突破 55 日高点 (无条件入场)
        if current_price > s2_high_55:
            return TurtleDecision(sym, TurtleSignalType.ENTRY_INIT_UNIT, TurtleSystemType.SYSTEM_2, n_val, unit_size, current_price - 2*n_val, 1, "无条件突破 55 日高点，海龟 System 2 建立初始头寸")

        return TurtleDecision(sym, TurtleSignalType.NO_SIGNAL, TurtleSystemType.SYSTEM_1, n_val, 0.0, 0.0, 0, "未触及任何突破阈值")
