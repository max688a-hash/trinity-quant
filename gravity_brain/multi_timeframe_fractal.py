"""
gravity_brain/multi_timeframe_fractal.py
========================================
TRINITY QUANT 多时间尺度分形共振动力学引擎。

贯彻顶级实战操盘铁律：
1. 大周期看趋势 (Macro: 日线/周线定生死与多空基调);
2. 中周期看结构 (Meso: 1小时/4小时看形态通道与洗盘回踩);
3. 小周期看触发 (Micro: 15分/5分/分时精确定位进出场买卖点);
4. 分形三位一体共振 (Fractal Resonance: 严禁逆大势操作)。
"""

from dataclasses import dataclass
from enum import Enum
from typing import Sequence


class TrendDirection(str, Enum):
    """趋势大方向"""
    BULLISH = "BULLISH"          # 多头上升期
    BEARISH = "BEARISH"          # 空头下降期
    SIDEWAYS = "SIDEWAYS"        # 宽幅震荡收敛期


class StructuralPattern(str, Enum):
    """几何中观结构形态"""
    HIGHER_HIGHS_LOWS = "HH_HL"  # 台阶式进攻 (高点抬升，低点抬升)
    LOWER_HIGHS_LOWS = "LH_LL"   # 台阶式下杀 (高点降低，破位新低)
    BOX_CONSOLIDATION = "BOX"    # 箱体收敛整理
    FALSE_PULLBACK = "FALSE_PB"  # 假回踩诱多


class ResonanceGrade(str, Enum):
    """分形共振定级"""
    FULL_BULL_RESONANCE = "FULL_BULL_RESONANCE"  # 三级全多头共振 (主升浪全力做多)
    FULL_BEAR_RESONANCE = "FULL_BEAR_RESONANCE"  # 三级全空头共振 (主跌浪清仓或做空)
    DIVERGENT_CONFLICT = "DIVERGENT_CONFLICT"    # 周期冲突背离 (大周期跌小周期涨，观望防诱多)


@dataclass(frozen=True)
class FractalResonanceVerdict:
    """多周期分形共振综合判定"""
    symbol: str
    macro_trend: TrendDirection
    meso_structure: StructuralPattern
    micro_trigger: str
    resonance_grade: ResonanceGrade
    allowed_direction: str                       # BUY / SELL / STAND_ASIDE
    confidence_multiplier: float                 # 0.0 ~ 1.0 仓位加权系数
    detailed_thesis: str


class MultiTimeframeFractalEngine:
    """多时间尺度分形动力学计算器"""

    def evaluate_fractal_resonance(
        self,
        symbol: str,
        macro_closes: Sequence[float],    # 日线历史收盘价
        meso_closes: Sequence[float],     # 1小时级别收盘价
        micro_current_price: float,       # 最新分时价格
        micro_intraday_open: float        # 当日开盘价
    ) -> FractalResonanceVerdict:
        """
        全景多时间尺度共振计算
        """
        sym = symbol.upper()
        if len(macro_closes) < 20 or len(meso_closes) < 10:
            raise ValueError("历史数据长度不足以支撑分形计算")

        # 1. 大周期 (日线) 测定大趋势: 短期均线 vs 长期均线
        ma20_macro = sum(macro_closes[-20:]) / 20.0
        ma5_macro = sum(macro_closes[-5:]) / 5.0
        if ma5_macro > ma20_macro * 1.01:
            macro_trend = TrendDirection.BULLISH
        elif ma5_macro < ma20_macro * 0.99:
            macro_trend = TrendDirection.BEARISH
        else:
            macro_trend = TrendDirection.SIDEWAYS

        # 2. 中周期 (小时线) 测定几何形态结构
        recent_meso = meso_closes[-8:]
        first_half_avg = sum(recent_meso[:4]) / 4.0
        second_half_avg = sum(recent_meso[4:]) / 4.0
        if second_half_avg > first_half_avg * 1.01:
            meso_struct = StructuralPattern.HIGHER_HIGHS_LOWS
        elif second_half_avg < first_half_avg * 0.99:
            meso_struct = StructuralPattern.LOWER_HIGHS_LOWS
        else:
            meso_struct = StructuralPattern.BOX_CONSOLIDATION

        # 3. 小周期 (分时日内) 测定触发信号
        is_intraday_up = micro_current_price >= micro_intraday_open
        micro_trigger = "INTRADAY_RALLY" if is_intraday_up else "INTRADAY_PULLBACK"

        # 4. 分形共振裁决
        # 顺大势共振：大周期涨 + 中周期结构好 + 小周期顺势触发
        if macro_trend == TrendDirection.BULLISH and meso_struct == StructuralPattern.HIGHER_HIGHS_LOWS and is_intraday_up:
            return FractalResonanceVerdict(
                symbol=sym,
                macro_trend=macro_trend,
                meso_structure=meso_struct,
                micro_trigger=micro_trigger,
                resonance_grade=ResonanceGrade.FULL_BULL_RESONANCE,
                allowed_direction="BUY",
                confidence_multiplier=1.0,
                detailed_thesis="大周期日线多头 + 中周期结构向上抬升 + 分时共振做多，主升浪三位一体确认"
            )

        # 空头顺大势：大周期跌 + 中周期破位下杀 + 小周期跌
        if macro_trend == TrendDirection.BEARISH and meso_struct == StructuralPattern.LOWER_HIGHS_LOWS and not is_intraday_up:
            return FractalResonanceVerdict(
                symbol=sym,
                macro_trend=macro_trend,
                meso_structure=meso_struct,
                micro_trigger=micro_trigger,
                resonance_grade=ResonanceGrade.FULL_BEAR_RESONANCE,
                allowed_direction="SELL",
                confidence_multiplier=1.0,
                detailed_thesis="大周期日线下降期 + 中周期结构破位 + 分时走弱，严禁抄底，顺势做空或清仓"
            )

        # 冲突背离：大周期处于下降期，但日内分时在上涨 (诱多假反弹陷阱)
        if macro_trend == TrendDirection.BEARISH and is_intraday_up:
            return FractalResonanceVerdict(
                symbol=sym,
                macro_trend=macro_trend,
                meso_structure=meso_struct,
                micro_trigger=micro_trigger,
                resonance_grade=ResonanceGrade.DIVERGENT_CONFLICT,
                allowed_direction="STAND_ASIDE",
                confidence_multiplier=0.0,
                detailed_thesis="大周期下跌且日内上涨，无量仓确认，强制观望，禁止把价格当突破证据"
            )

        # 震荡整理或其他冲突
        return FractalResonanceVerdict(
            symbol=sym,
            macro_trend=macro_trend,
            meso_structure=meso_struct,
            micro_trigger=micro_trigger,
            resonance_grade=ResonanceGrade.DIVERGENT_CONFLICT,
            allowed_direction="STAND_ASIDE",
            confidence_multiplier=0.3,
            detailed_thesis="多周期处于结构分歧态，未见高确定性共振信号，施加谨慎减仓观望"
        )
