"""
gravity_brain/auto_screener_engine.py
=====================================
一键真值智能选股与微观企业商业模式深研引擎。

核心功能：
1. 自动化真值智能选股：基于造血纯度 Φ_CP、债务毒性 Ω_Debt、股东抛售与Alpha执行洁净筛选；
2. 深度穿透研报输出：主营业务骨架、商业模式去季节性分析、抗周期护城河与资本开支安全度；
3. 联动声音与变色提示：达到建仓标准时触发清脆"叮(Ping)"声与翡翠绿高亮。
"""

from dataclasses import dataclass
import logging
import math
from typing import Any, Dict, List, Optional

from gravity_brain.screener_audit_universe import load_default_screener_universe

_LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class CompanyDeepDossier:
    """企业微观商业模式深研剖析档案"""
    symbol: str
    name: str
    industry: str
    core_business: str              # 主营业务与造血骨架
    seasonality_profile: str        # 商业模式季节性穿透 (夏亏冬赚等)
    moat_rating: str                # 护城河壁垒评级 (PRICING_POWER / MONOPOLY / UTILITY)
    capex_health: str               # 自由现金流对资本开支覆盖
    anti_cycle_grade: str           # 宏观抗周期能力评级 (AAA / AA / B)
    recommended_action: str         # 策略建议 (STRONG_BUY / HOLD / AVOID)


@dataclass(frozen=True)
class AutoScreeningCandidate:
    """智能选股入选标的与综合得分"""
    symbol: str
    name: str
    phi_cp: float
    omega_debt: float
    alpha: float
    gravity_value: float
    is_qualified: bool
    audio_chime: str                # ENTRY_PING
    color_indicator: str            # emerald-glow
    deep_dossier: CompanyDeepDossier


class AutoScreenerEngine:
    """一键真值智能选股与深研处理器"""

    # 预载优质标的深研知识库
    KNOWLEDGE_BASE: Dict[str, Dict[str, str]] = {
        "600519": {
            "name": "贵州茅台",
            "industry": "高端白酒/消费品",
            "core_business": "以飞天茅台为核心的酱香白酒生产与直营销售。具有极高毛利率(92%)与现金直款预收优势。",
            "seasonality_profile": "具备明显春节/中秋双节消费脉冲，但全年中秋及四季度现金流显著走高，三季度基酒储藏去季节性波动。",
            "moat_rating": "PRICING_POWER (绝对定价权与自然地理不可复制护城河)",
            "capex_health": "极充沛：年度 OCF 超过 700 亿，对 40 亿扩产资本开支覆盖率高达 17 倍以上。",
            "anti_cycle_grade": "AAA (穿越周期之王，无惧通胀与紧缩)",
            "recommended_action": "STRONG_BUY (真值引力超跌时分批吸收)"
        },
        "002594": {
            "name": "比亚迪",
            "industry": "新能源汽车/动力电池",
            "core_business": "整车垂直一体化制造、刀片电池与车载半导体全产业链自主可控。",
            "seasonality_profile": "一季度春节淡季销量平缓，三四季度乘用车旺季销量放量，库存周转天数保持在 45 天以内。",
            "moat_rating": "SCALE_COST (全产业链垂直整合与规模成本杀手)",
            "capex_health": "良性循环：年造血 OCF 435 亿，研发与建厂资本开支虽重，但现金回流强劲。",
            "anti_cycle_grade": "AA (受大宗锂碳价格波动影响，但出海与规模对冲充分)",
            "recommended_action": "ACCUMULATE (回踩通道均线顺势跟随)"
        },
        "600900": {
            "name": "长江电力",
            "industry": "清洁水力发电/公用事业",
            "core_business": "乌东德、白鹤滩、溪洛渡、向家坝、三峡、葛洲坝六大梯级水电站巨型清洁电能运营。",
            "seasonality_profile": "二三季度汛期丰水期发电量见顶，一季度枯水期发电量偏低，但通过巨型梯级水库联合调度平滑季际波动。",
            "moat_rating": "MONOPOLY (世界最大清洁能源走廊，不可替代自然资源特许垄断)",
            "capex_health": "现金奶牛：水电机组建完后几乎无新增大资本开支，充沛自由现金流保障高股息分红。",
            "anti_cycle_grade": "AAA (防守基石，类国债永续造血属性)",
            "recommended_action": "DEFENSIVE_HOLD (大盘震荡期核心避险压舱石)"
        }
    }

    def __init__(
        self,
        min_phi_cp: float = 0.80,
        max_omega_debt: float = 1.00,
        min_alpha: float = 1.0
    ) -> None:
        self._min_phi = min_phi_cp
        self._max_omega = max_omega_debt
        self._min_alpha = min_alpha

    def run_screening(self, universe: Optional[List[dict]] = None) -> List[AutoScreeningCandidate]:
        """
        执行一键智能选股。默认宇宙来自真实财报体检/估值档案，禁止写死 Φ/Ω。
        """
        if universe is None:
            universe = load_default_screener_universe()
        results: List[AutoScreeningCandidate] = []
        for item in universe:
            candidate = self._evaluate_item(item)
            if candidate is not None:
                results.append(candidate)
        return results

    def _as_finite(self, value: Any, fallback: float) -> float:
        try:
            num = float(value)
        except (TypeError, ValueError) as exc:
            _LOG.warning("选股指标无法解析: %s", exc)
            return fallback
        if not math.isfinite(num):
            return fallback
        return num

    def _evaluate_item(self, item: dict) -> Optional[AutoScreeningCandidate]:
        if not isinstance(item, dict):
            return None
        sym = str(item.get("symbol", "")).split(".")[0].strip().upper()
        if not sym:
            return None
        name = str(item.get("name", sym))
        phi = self._as_finite(item.get("phi_cp"), 0.0)
        omega = self._as_finite(item.get("omega_debt"), 99.0)
        alpha = self._as_finite(item.get("alpha"), 0.0)
        gv = self._as_finite(item.get("gravity_val"), 0.0)
        is_ok = (phi >= self._min_phi) and (omega <= self._max_omega) and (alpha >= self._min_alpha)
        if "is_admitted" in item and not bool(item.get("is_admitted")):
            is_ok = False

        kb = self.KNOWLEDGE_BASE.get(sym, {
            "name": name,
            "industry": "未知制造业/商贸",
            "core_business": f"{name}主营业务与供应链制造。",
            "seasonality_profile": "常态季节分布，需关注行业补库与去库周期。",
            "moat_rating": "STANDARD (通用竞争格局)",
            "capex_health": "适度健康",
            "anti_cycle_grade": "A",
            "recommended_action": "WATCHLIST"
        })
        action = kb["recommended_action"] if is_ok else "VETO (法证否决，禁止当作可买)"
        dossier = CompanyDeepDossier(
            symbol=sym,
            name=kb["name"],
            industry=kb["industry"],
            core_business=kb["core_business"],
            seasonality_profile=kb["seasonality_profile"],
            moat_rating=kb["moat_rating"],
            capex_health=kb["capex_health"],
            anti_cycle_grade=kb["anti_cycle_grade"],
            recommended_action=action
        )
        return AutoScreeningCandidate(
            symbol=sym,
            name=name,
            phi_cp=phi,
            omega_debt=omega,
            alpha=alpha,
            gravity_value=gv,
            is_qualified=is_ok,
            audio_chime="ENTRY_PING" if is_ok else "NONE",
            color_indicator="badge-glow-green" if is_ok else "badge-glow-red",
            deep_dossier=dossier
        )
