"""
truth_kernel/asset_taxonomy.py
==============================
TRINITY QUANT 全资产全市场分类学与微观结构规范库。

严格定义权益（A股/港股/美股）、大宗与金融期货、外汇及加密资产的
结算周期、合约乘数、最小变动价位、税费模型与交割约束。
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


class AssetClass(str, Enum):
    """资产大类定义"""
    EQUITY = "EQUITY"
    COMMODITY_FUTURE = "COMMODITY_FUTURE"
    FINANCIAL_FUTURE = "FINANCIAL_FUTURE"
    FOREX = "FOREX"
    CRYPTO = "CRYPTO"


class MarketVenue(str, Enum):
    """交易法区与市场子集"""
    CN_EQUITY = "CN_EQUITY"          # A股 (上交所/深交所/北交所)
    HK_EQUITY = "HK_EQUITY"          # 港交所股票
    US_EQUITY = "US_EQUITY"          # 美股 (NYSE/NASDAQ)
    CN_FUTURE = "CN_FUTURE"          # 国内五大期交所 (SHFE/DCE/CZCE/CFFEX/GFEX)
    GLOBAL_FUTURE = "GLOBAL_FUTURE"  # 国际期货 (CME/ICE/HKEX)
    FOREX_OTC = "FOREX_OTC"          # 银行间/外汇做市商
    CRYPTO = "CRYPTO"                # 链上/交易所数字资产


class SettlementType(str, Enum):
    """结算与交割周期"""
    T_PLUS_0 = "T+0"
    T_PLUS_1 = "T+1"


class CommissionType(str, Enum):
    """佣金费率计提模式"""
    PERCENTAGE = "PERCENTAGE"       # 按成交金额比例 (如万分之三)
    PER_CONTRACT = "PER_CONTRACT"   # 按手/张固定金额 (如每手3元)


@dataclass(frozen=True)
class InstrumentSpecification:
    """
    标的微观结构规格说明书
    
    数学与物理属性：
    - contract_multiplier: 合约价值换算乘数 (如玉米10吨/手, IF 300元/点)
    - price_tick: 最小物理价格步长
    - lot_size: 最小成交手数 (如A股100股/手)
    - initial_margin_ratio: 初始保证金比例 (现货为1.0, 期货杠杆依据此计算)
    """
    symbol: str
    name: str
    asset_class: AssetClass
    venue: MarketVenue
    settlement: SettlementType
    contract_multiplier: float
    price_tick: float
    lot_size: int
    stamp_duty_buy: float
    stamp_duty_sell: float
    commission_rate: float
    commission_type: CommissionType
    initial_margin_ratio: float
    price_limit_ratio: Optional[float] = None
    allow_retail_delivery: bool = True

    def __post_init__(self) -> None:
        if self.contract_multiplier <= 0:
            raise ValueError(f"合约乘数必须大于0: {self.contract_multiplier}")
        if self.price_tick <= 0:
            raise ValueError(f"最小变动价位必须大于0: {self.price_tick}")
        if self.lot_size <= 0:
            raise ValueError(f"最小交易单位必须大于0: {self.lot_size}")
        if self.initial_margin_ratio <= 0 or self.initial_margin_ratio > 1.0:
            raise ValueError(f"保证金比例必须在 (0, 1.0] 内: {self.initial_margin_ratio}")
        if self.stamp_duty_buy < 0 or self.stamp_duty_sell < 0:
            raise ValueError("印花税率不得为负数")


class TaxonomyRegistry:
    """全资产规格注册表与工厂"""
    
    _registry: Dict[str, InstrumentSpecification] = {}

    @classmethod
    def register(cls, spec: InstrumentSpecification) -> None:
        """注册标的规范"""
        if not spec.symbol:
            raise ValueError("标的代码不得为空")
        cls._registry[spec.symbol.upper()] = spec

    @classmethod
    def get(cls, symbol: str) -> InstrumentSpecification:
        """检索标的规范 (支持前缀解析与全域商品/金融期货真实物理契约回退)"""
        key = symbol.strip().upper()
        if key in cls._registry:
            return cls._registry[key]
        prefix = "".join(filter(str.isalpha, key))
        if prefix in cls._registry:
            return cls._registry[prefix]
        # 黑色系建材/炉料 (螺纹钢RB, 热卷HC, 铁矿石I, 焦炭J, 焦煤JM)
        if prefix in ("RB", "HC", "I", "J", "JM", "SF", "SM", "WR"):
            return InstrumentSpecification(
                symbol=prefix, name=f"{prefix}黑色期货",
                asset_class=AssetClass.COMMODITY_FUTURE, venue=MarketVenue.CN_FUTURE,
                settlement=SettlementType.T_PLUS_0, contract_multiplier=10.0,
                price_tick=1.0, lot_size=1, stamp_duty_buy=0.0, stamp_duty_sell=0.0,
                commission_rate=0.0001, commission_type=CommissionType.PERCENTAGE,
                initial_margin_ratio=0.10, price_limit_ratio=0.08, allow_retail_delivery=False
            )
        # 有色/贵金属/新能源 (铜CU, 铝AL, 锌ZN, 镍NI, 黄金AU, 白银AG, 锂LC)
        if prefix in ("CU", "AL", "ZN", "PB", "NI", "SN", "AU", "AG", "LC", "SI"):
            return InstrumentSpecification(
                symbol=prefix, name=f"{prefix}有色/新能源期货",
                asset_class=AssetClass.COMMODITY_FUTURE, venue=MarketVenue.CN_FUTURE,
                settlement=SettlementType.T_PLUS_0, contract_multiplier=5.0,
                price_tick=1.0, lot_size=1, stamp_duty_buy=0.0, stamp_duty_sell=0.0,
                commission_rate=0.00005, commission_type=CommissionType.PERCENTAGE,
                initial_margin_ratio=0.12, price_limit_ratio=0.08, allow_retail_delivery=False
            )
        # 能化能源 (原油SC, 纯碱SA, 玻璃FG, 甲醇MA, PTA, 聚丙烯PP, 沥青BU, 燃油FU)
        if prefix in ("SC", "FU", "LU", "BU", "MA", "TA", "PP", "EB", "EG", "V", "UR"):
            return InstrumentSpecification(
                symbol=prefix, name=f"{prefix}能化期货",
                asset_class=AssetClass.COMMODITY_FUTURE, venue=MarketVenue.CN_FUTURE,
                settlement=SettlementType.T_PLUS_0, contract_multiplier=10.0,
                price_tick=1.0, lot_size=1, stamp_duty_buy=0.0, stamp_duty_sell=0.0,
                commission_rate=0.0001, commission_type=CommissionType.PERCENTAGE,
                initial_margin_ratio=0.11, price_limit_ratio=0.08, allow_retail_delivery=False
            )
        # 农产品与软商品 (玉米C, 豆粕M, 棕榈油P, 豆油Y, 白糖SR, 棉花CF, 生猪LH, 苹果AP)
        if prefix in ("M", "Y", "P", "OI", "RM", "CF", "SR", "AP", "CJ", "LH", "PK", "JD"):
            return InstrumentSpecification(
                symbol=prefix, name=f"{prefix}农产品期货",
                asset_class=AssetClass.COMMODITY_FUTURE, venue=MarketVenue.CN_FUTURE,
                settlement=SettlementType.T_PLUS_0, contract_multiplier=10.0,
                price_tick=1.0, lot_size=1, stamp_duty_buy=0.0, stamp_duty_sell=0.0,
                commission_rate=2.0, commission_type=CommissionType.PER_CONTRACT,
                initial_margin_ratio=0.08, price_limit_ratio=0.06, allow_retail_delivery=False
            )
        # 中金所金融股指与国债期货 (IF, IC, IM, IH, T, TF, TS, TL)
        if prefix in ("IC", "IM", "IH", "T", "TF", "TS", "TL"):
            is_bond = prefix in ("T", "TF", "TS", "TL")
            return InstrumentSpecification(
                symbol=prefix, name=f"{prefix}金融期指",
                asset_class=AssetClass.FINANCIAL_FUTURE, venue=MarketVenue.CN_FUTURE,
                settlement=SettlementType.T_PLUS_0,
                contract_multiplier=10000.0 if is_bond else 200.0,
                price_tick=0.005 if is_bond else 0.2, lot_size=1,
                stamp_duty_buy=0.0, stamp_duty_sell=0.0,
                commission_rate=3.0 if is_bond else 0.000023,
                commission_type=CommissionType.PER_CONTRACT if is_bond else CommissionType.PERCENTAGE,
                initial_margin_ratio=0.03 if is_bond else 0.12,
                price_limit_ratio=0.02 if is_bond else 0.10,
                allow_retail_delivery=True
            )
        raise KeyError(f"标的未注册规格: {symbol}")

    @classmethod
    def list_symbols(cls) -> list[str]:
        """列出所有已注册标的"""
        return sorted(list(cls._registry.keys()))


# ==============================================================================
# 注册全市场基准标的 (严格对应真实物理市场规则)
# ==============================================================================

# 1. 大商所玉米 (C) - 10吨/手, 1元/吨, 8%保证金, 自然人禁止交割
TaxonomyRegistry.register(InstrumentSpecification(
    symbol="C", name="大连大豆/玉米期货", asset_class=AssetClass.COMMODITY_FUTURE,
    venue=MarketVenue.CN_FUTURE, settlement=SettlementType.T_PLUS_0,
    contract_multiplier=10.0, price_tick=1.0, lot_size=1, stamp_duty_buy=0.0,
    stamp_duty_sell=0.0, commission_rate=1.20, commission_type=CommissionType.PER_CONTRACT,
    initial_margin_ratio=0.08, price_limit_ratio=0.06, allow_retail_delivery=False
))

# 2. 郑商所纯碱 (SA) - 20吨/手, 1元/吨, 9%保证金, 自然人禁止交割
TaxonomyRegistry.register(InstrumentSpecification(
    symbol="SA", name="郑州纯碱期货", asset_class=AssetClass.COMMODITY_FUTURE,
    venue=MarketVenue.CN_FUTURE, settlement=SettlementType.T_PLUS_0,
    contract_multiplier=20.0, price_tick=1.0, lot_size=1, stamp_duty_buy=0.0,
    stamp_duty_sell=0.0, commission_rate=3.50, commission_type=CommissionType.PER_CONTRACT,
    initial_margin_ratio=0.09, price_limit_ratio=0.08, allow_retail_delivery=False
))

# 3. 上期所白银 (AG) - 15千克/手, 1元/千克, 10%保证金, 自然人禁止交割
TaxonomyRegistry.register(InstrumentSpecification(
    symbol="AG", name="上海白银期货", asset_class=AssetClass.COMMODITY_FUTURE,
    venue=MarketVenue.CN_FUTURE, settlement=SettlementType.T_PLUS_0,
    contract_multiplier=15.0, price_tick=1.0, lot_size=1, stamp_duty_buy=0.0,
    stamp_duty_sell=0.0, commission_rate=0.00005, commission_type=CommissionType.PERCENTAGE,
    initial_margin_ratio=0.10, price_limit_ratio=0.09, allow_retail_delivery=False
))

# 4. 中金所沪深300期指 (IF) - 300元/点, 0.2点, 12%保证金, 现金交割
TaxonomyRegistry.register(InstrumentSpecification(
    symbol="IF", name="中金所沪深300期指", asset_class=AssetClass.FINANCIAL_FUTURE,
    venue=MarketVenue.CN_FUTURE, settlement=SettlementType.T_PLUS_0,
    contract_multiplier=300.0, price_tick=0.2, lot_size=1, stamp_duty_buy=0.0,
    stamp_duty_sell=0.0, commission_rate=0.000023, commission_type=CommissionType.PERCENTAGE,
    initial_margin_ratio=0.12, price_limit_ratio=0.10, allow_retail_delivery=True
))

# 5. 中国 A 股: 贵州茅台 (600519.SH) - T+1, 卖方0.05%印花税, 100股/手
TaxonomyRegistry.register(InstrumentSpecification(
    symbol="600519.SH", name="贵州茅台", asset_class=AssetClass.EQUITY,
    venue=MarketVenue.CN_EQUITY, settlement=SettlementType.T_PLUS_1,
    contract_multiplier=1.0, price_tick=0.01, lot_size=100, stamp_duty_buy=0.0,
    stamp_duty_sell=0.0005, commission_rate=0.00025, commission_type=CommissionType.PERCENTAGE,
    initial_margin_ratio=1.0, price_limit_ratio=0.10, allow_retail_delivery=True
))

# 6. 香港港股: 腾讯控股 (0700.HK) - T+0, 双边0.10%印花税, 100股/手
TaxonomyRegistry.register(InstrumentSpecification(
    symbol="0700.HK",
    name="腾讯控股",
    asset_class=AssetClass.EQUITY,
    venue=MarketVenue.HK_EQUITY,
    settlement=SettlementType.T_PLUS_0,
    contract_multiplier=1.0,
    price_tick=0.20,
    lot_size=100,
    stamp_duty_buy=0.0010,
    stamp_duty_sell=0.0010,
    commission_rate=0.0003,
    commission_type=CommissionType.PERCENTAGE,
    initial_margin_ratio=1.0,
    price_limit_ratio=None,
    allow_retail_delivery=True
))

# 7. 美国美股: 苹果公司 (AAPL.US) - T+0, 0印花税, 1股/手
TaxonomyRegistry.register(InstrumentSpecification(
    symbol="AAPL.US", name="Apple Inc.", asset_class=AssetClass.EQUITY,
    venue=MarketVenue.US_EQUITY, settlement=SettlementType.T_PLUS_0,
    contract_multiplier=1.0, price_tick=0.01, lot_size=1, stamp_duty_buy=0.0,
    stamp_duty_sell=0.0, commission_rate=0.0001, commission_type=CommissionType.PERCENTAGE,
    initial_margin_ratio=1.0, price_limit_ratio=None, allow_retail_delivery=True
))

# 8. 全球外汇: 美元/离岸人民币 (USDCNH) - T+0, 0印花税, 10万基准货币
TaxonomyRegistry.register(InstrumentSpecification(
    symbol="USDCNH", name="美元/离岸人民币", asset_class=AssetClass.FOREX,
    venue=MarketVenue.FOREX_OTC, settlement=SettlementType.T_PLUS_0,
    contract_multiplier=100000.0, price_tick=0.0001, lot_size=1, stamp_duty_buy=0.0,
    stamp_duty_sell=0.0, commission_rate=0.00002, commission_type=CommissionType.PERCENTAGE,
    initial_margin_ratio=0.02, price_limit_ratio=None, allow_retail_delivery=True
))

# 9. 全球加密资产: 比特币永续 (BTCUSDT) - 7x24x365 实盘开市, T+0, 0印花税
TaxonomyRegistry.register(InstrumentSpecification(
    symbol="BTCUSDT", name="比特币永续合约", asset_class=AssetClass.CRYPTO,
    venue=MarketVenue.CRYPTO, settlement=SettlementType.T_PLUS_0,
    contract_multiplier=1.0, price_tick=0.1, lot_size=1, stamp_duty_buy=0.0,
    stamp_duty_sell=0.0, commission_rate=0.0004, commission_type=CommissionType.PERCENTAGE,
    initial_margin_ratio=0.05, price_limit_ratio=None, allow_retail_delivery=True
))
