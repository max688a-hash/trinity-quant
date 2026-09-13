"""
immune_system/insider_dump_monitor.py
=====================================
大股东与高管集中减持抛售、股权质押暴雷危机监测引擎。

核心物理金融逻辑：
1. 减持抛售压力比 (Dumping Pressure Ratio): 大股东减持量占标的过去20日日均成交量(ADV)的比重；
2. 大宗交易折价率 (Block Discount Rate): 股东通过大宗折价甩卖套现对二级市场的抽水冲击；
3. 股权质押爆仓风险 (Pledge Liquidation Risk): 控股股东高质押率下股价逼近平仓线的踩踏风险；
4. 联动输出 Web Audio 声音告警代码与 UI 频闪变色主题。
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class AlertSeverity(str, Enum):
    """预警危急等级"""
    NORMAL = "NORMAL"          # 正常健康
    CAUTION = "CAUTION"        # 提示谨慎
    CRITICAL_DUMP = "CRITICAL" # 危险抛售，一票否决


class AudioAlertTone(str, Enum):
    """声音提示物理振荡器类型"""
    NONE = "NONE"
    ENTRY_PING = "ENTRY_PING"      # 880Hz 清脆"叮"声 (建仓/止盈信号)
    CRISIS_ALARM = "CRISIS_ALARM"  # 220Hz 低频双蜂鸣 (大股东抛售/熔断)
    CAUTION_BEEP = "CAUTION_BEEP"  # 440Hz 短促提示音


@dataclass(frozen=True)
class InsiderAlertVerdict:
    """大股东减持与危机综合裁决"""
    symbol: str
    severity: AlertSeverity
    is_vetoed: bool
    dumping_ratio: float           # 减持占日均成交比
    pledge_ratio: float            # 股权质押比率
    discount_pct: float            # 大宗折价幅度
    audio_tone: AudioAlertTone     # 触发声音提示
    ui_theme_class: str            # 前端变色主题
    warning_message: str           # 预警通知文本


class InsiderDumpMonitor:
    """大股东减持抛售与质押危机探针"""

    def __init__(
        self,
        max_dumping_ratio: float = 0.05,
        max_pledge_ratio: float = 0.50,
        max_discount_pct: float = 0.08
    ) -> None:
        if max_dumping_ratio <= 0 or max_pledge_ratio <= 0 or max_discount_pct <= 0:
            raise ValueError("风控阈值参数必须大于0")
        self._max_dumping = max_dumping_ratio
        self._max_pledge = max_pledge_ratio
        self._max_discount = max_discount_pct

    def evaluate_insider_risk(
        self,
        symbol: str,
        insider_sell_volume: float,
        adv_20: float,
        pledged_shares_ratio: float,
        block_discount_pct: float = 0.0
    ) -> InsiderAlertVerdict:
        """
        评估大股东抛售与质押挤兑风险
        """
        sym = symbol.strip().upper()
        if adv_20 <= 0:
            return InsiderAlertVerdict(
                symbol=sym,
                severity=AlertSeverity.CRITICAL_DUMP,
                is_vetoed=True,
                dumping_ratio=1.0,
                pledge_ratio=pledged_shares_ratio,
                discount_pct=block_discount_pct,
                audio_tone=AudioAlertTone.CRISIS_ALARM,
                ui_theme_class="badge-glow-red",
                warning_message=f"[{sym}] ADV成交量归零或为负，流动性完全枯竭！"
            )

        dump_ratio = max(0.0, insider_sell_volume / adv_20)
        pledge = max(0.0, min(1.0, pledged_shares_ratio))
        discount = max(0.0, block_discount_pct)

        # 1. 致命级危机触发一票否决
        if dump_ratio >= 0.15 or pledge >= 0.70 or (dump_ratio >= self._max_dumping and discount >= self._max_discount):
            msg = (
                f"[{sym}] 触发大股东疯狂甩卖危机！减持抛售占ADV比例达 {dump_ratio*100:.1f}%，"
                f"大宗折价 {discount*100:.1f}%，质押率 {pledge*100:.1f}%。一票否决！"
            )
            return InsiderAlertVerdict(
                symbol=sym,
                severity=AlertSeverity.CRITICAL_DUMP,
                is_vetoed=True,
                dumping_ratio=dump_ratio,
                pledge_ratio=pledge,
                discount_pct=discount,
                audio_tone=AudioAlertTone.CRISIS_ALARM,
                ui_theme_class="badge-glow-red",
                warning_message=msg
            )

        # 2. 谨慎级预警
        if dump_ratio >= self._max_dumping or pledge >= self._max_pledge:
            msg = (
                f"[{sym}] 出现异动抛售苗头：减持占ADV {dump_ratio*100:.1f}%，"
                f"质押率 {pledge*100:.1f}%。系统施加50%仓位惩罚。"
            )
            return InsiderAlertVerdict(
                symbol=sym,
                severity=AlertSeverity.CAUTION,
                is_vetoed=False,
                dumping_ratio=dump_ratio,
                pledge_ratio=pledge,
                discount_pct=discount,
                audio_tone=AudioAlertTone.CAUTION_BEEP,
                ui_theme_class="badge-glow-amber",
                warning_message=msg
            )

        # 3. 正常健康状态
        return InsiderAlertVerdict(
            symbol=sym,
            severity=AlertSeverity.NORMAL,
            is_vetoed=False,
            dumping_ratio=dump_ratio,
            pledge_ratio=pledge,
            discount_pct=discount,
            audio_tone=AudioAlertTone.NONE,
            ui_theme_class="badge-glow-green",
            warning_message=f"[{sym}] 股东持股结构稳固，无异常减持与质押爆仓风险。"
        )
