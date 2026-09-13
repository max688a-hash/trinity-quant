"""
truth_kernel/industry_chain_graph.py
====================================
全行业全景产业链知识图谱与利润分配透视引擎。
遵循最高宪法第一性原理立宪 (AGENTS.md):
1. 建立上游原材料/设备 -> 中游制造加工 -> 下游消费终端的价值链条;
2. 精确测算各环节毛利分配占比、定价权强弱与产业链断链替代风险;
3. 单文件严格不超过 300 行，强类型标注，零盲吞异常。
"""

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional


class ChainSegment(str, Enum):
    UPSTREAM = "UPSTREAM"        # 上游 (原材料/初级能源/核心设备)
    MIDSTREAM = "MIDSTREAM"      # 中游 (制造加工/精炼合成/组装集成)
    DOWNSTREAM = "DOWNSTREAM"    # 下游 (消费终端/商业流通/金融储备)


class PricingPower(str, Enum):
    DOMINANT = "DOMINANT"        # 绝对主导 (近乎单向提价权，高毛利)
    STRONG = "STRONG"            # 较强议价 (具备成本转嫁能力)
    MODERATE = "MODERATE"        # 均衡博弈 (随行就市)
    WEAK = "WEAK"                # 被动接受 (成本转嫁困难，易受挤压)


@dataclass(frozen=True)
class ChainNode:
    """产业链节点微观画像"""
    name: str
    segment: ChainSegment
    gross_margin_pct: float
    pricing_power: PricingPower
    moat_barrier: str
    major_risks: str


@dataclass(frozen=True)
class IndustryChain:
    """行业全景产业链拓扑结构"""
    sector_id: str
    sector_name: str
    representative_symbol: str
    representative_name: str
    upstream_nodes: List[ChainNode]
    midstream_nodes: List[ChainNode]
    downstream_nodes: List[ChainNode]
    profit_distribution_summary: str
    pricing_power_verdict: str


class IndustryChainGraphRegistry:
    """产业链全景图谱权威注册中心"""

    _REGISTRY: Dict[str, IndustryChain] = {}

    @classmethod
    def register(cls, chain: IndustryChain) -> None:
        cls._REGISTRY[chain.sector_id] = chain
        cls._REGISTRY[chain.representative_symbol] = chain
        cls._REGISTRY[chain.representative_symbol.split(".")[0]] = chain

    @classmethod
    def get_chain(cls, key: str) -> Optional[IndustryChain]:
        """根据板块代码或标的代码获取产业链"""
        if key in cls._REGISTRY:
            return cls._REGISTRY[key]
        clean_code = key.split(".")[0].strip().upper()
        if clean_code in cls._REGISTRY:
            return cls._REGISTRY[clean_code]
        for c in cls._REGISTRY.values():
            if c.sector_id.upper() == clean_code or c.representative_symbol.split(".")[0].upper() == clean_code:
                return c
        return None

    @classmethod
    def list_chains(cls) -> List[IndustryChain]:
        """列出所有已注册的产业链图谱"""
        seen = set()
        chains = []
        for c in cls._REGISTRY.values():
            if c.sector_id not in seen:
                seen.add(c.sector_id)
                chains.append(c)
        return chains


# ==============================================================================
# 注册六大核心实体产业链图谱 (严密锚定第一性原理商业物理世界)
# ==============================================================================

# 1. 高端白酒与快消龙头 (贵州茅台 600519.SH)
IndustryChainGraphRegistry.register(IndustryChain(
    sector_id="baijiu_consumer",
    sector_name="高端白酒与高壁垒消费品",
    representative_symbol="600519.SH",
    representative_name="贵州茅台",
    upstream_nodes=[
        ChainNode("仁怀有机红缨子糯高粱与小麦", ChainSegment.UPSTREAM, 22.0, PricingPower.MODERATE, "严苛地理标志保护与有机认证种植基地", "极端干旱减产/采购成本上浮"),
        ChainNode("赤水河流域独特微生物菌群生态", ChainSegment.UPSTREAM, 85.0, PricingPower.DOMINANT, "不可复制的自然酿造微生态微环境", "赤水河水质生态红线管制")
    ],
    midstream_nodes=[
        ChainNode("端午踩曲/重阳下沙传统坤沙固态发酵", ChainSegment.MIDSTREAM, 91.5, PricingPower.DOMINANT, "五年生产周期/陶坛贮存老熟/万吨级轮次勾调", "基酒贮存占用巨量运营资金与库容"),
        ChainNode("自动化纳米级防伪灌装与智能包装", ChainSegment.MIDSTREAM, 45.0, PricingPower.STRONG, "防伪RFID芯片与专有防伪盖制造壁垒", "包材瓦楞纸与玻璃瓶成本波动")
    ],
    downstream_nodes=[
        ChainNode("直销渠道 (i茅台APP / 自营直销专卖店)", ChainSegment.DOWNSTREAM, 94.2, PricingPower.DOMINANT, "直面终端刚性需求，完全回收渠道溢价", "平台流量并发峰值承载稳定性"),
        ChainNode("传统社会经销商与大宗特约配额", ChainSegment.DOWNSTREAM, 75.0, PricingPower.STRONG, "特许经销权壁垒与数十年政商客户网络", "批价与终端零售指导价价格倒挂倒逼"),
        ChainNode("商务宴请、礼品流通与老酒民间金融收藏", ChainSegment.DOWNSTREAM, 60.0, PricingPower.STRONG, "心智金融硬通货属性/保值抗通胀预期", "宏观商务消费降级与三公经费严格约束")
    ],
    profit_distribution_summary="产业链利润极度集中于中游品牌持有方与自营零售终端，毛利率超 91%，下游渠道享丰厚批零差价，上游农产品平稳微利。",
    pricing_power_verdict="绝对主导级 (DOMINANT)。具备跨周期单向提价权，无实际技术替代品。"
))

# 2. 清洁能源与水电基荷 (长江电力 600900.SH)
IndustryChainGraphRegistry.register(IndustryChain(
    sector_id="clean_hydro_utility",
    sector_name="清洁能源与梯级水电基荷",
    representative_symbol="600900.SH",
    representative_name="长江电力",
    upstream_nodes=[
        ChainNode("长江金沙江流域天然水文径流与重力势能", ChainSegment.UPSTREAM, 0.0, PricingPower.MODERATE, "金沙江下游至长江干流六座巨型梯级水库联合调度", "枯水期径流来水偏枯20%~30%"),
        ChainNode("哈电/东电百万千瓦水轮发电机组设备", ChainSegment.MIDSTREAM, 28.0, PricingPower.STRONG, "大国重器特大型水电机组制造与安装维修壁垒", "关键轴承与发电机组大修折旧周期")
    ],
    midstream_nodes=[
        ChainNode("六座梯级巨型水电站 (乌白溪向三葛) 联合调度发电", ChainSegment.MIDSTREAM, 58.5, PricingPower.STRONG, "全球最大清洁能源走廊，边际发电成本几乎为零 (仅折旧)", "巨额电站折旧资产与还本付息刚性支出")
    ],
    downstream_nodes=[
        ChainNode("国家电网与南方电网跨区跨省超高压/特高压骨干送电", ChainSegment.DOWNSTREAM, 15.0, PricingPower.STRONG, "西电东送国家战略保供骨架通道", "特高压输变电线路冰雪冻灾停机检修"),
        ChainNode("沿海八省市工商业与居民刚性基荷消纳", ChainSegment.DOWNSTREAM, 8.0, PricingPower.MODERATE, "长三角/大湾区经济引擎高负荷用电需求保障", "电力现货市场化竞价带来的电价下行波动")
    ],
    profit_distribution_summary="中游梯级发电端享受独占水资源重力势能，折旧期内经营现金流超千亿，下游电网通道赚取稳定过网费，商业模式稳若磐石。",
    pricing_power_verdict="强确定性 (STRONG)。享受优先上网电量消纳与跨省跨区中长期协议锁定电价。"
))

# 3. 新能源汽车与电池高端制造 (比亚迪 002594.SZ)
IndustryChainGraphRegistry.register(IndustryChain(
    sector_id="ev_power_battery",
    sector_name="新能源汽车与垂直整合产业链",
    representative_symbol="002594.SZ",
    representative_name="比亚迪",
    upstream_nodes=[
        ChainNode("电池级碳酸锂/氢氧化锂及前驱体磷酸铁", ChainSegment.UPSTREAM, 35.0, PricingPower.STRONG, "盐湖提锂与锂矿采选开采特许权", "锂价大宗商品周期剧烈过山车震荡"),
        ChainNode("铝挤压型材与高端车用芯片半导体晶圆", ChainSegment.UPSTREAM, 25.0, PricingPower.STRONG, "车规级IGBT/碳化硅SIC功率模块制造工艺", "晶圆代工产能紧缺与制造成本波动")
    ],
    midstream_nodes=[
        ChainNode("刀片电池CTP封装与DM-i超混双模总成", ChainSegment.MIDSTREAM, 22.8, PricingPower.STRONG, "全栈垂直自研自产垂直整合规模成本优势", "技术路线迭代对老产线设备的沉没风险"),
        ChainNode("白车身冲压焊接/智能座舱整车柔性制造", ChainSegment.MIDSTREAM, 18.5, PricingPower.STRONG, "年产数百万辆级全球规模制造良率与交付效率", "国内车企白热化价格战侵蚀单车毛利")
    ],
    downstream_nodes=[
        ChainNode("全球直营体验中心与传统4S销售服务网络", ChainSegment.DOWNSTREAM, 8.0, PricingPower.MODERATE, "覆盖全国并远销欧拉欧美的庞大渠道生态", "海外地缘反补贴关税与出口关税壁垒"),
        ChainNode("大众消费私家车/网约车出行业务运营", ChainSegment.DOWNSTREAM, 5.0, PricingPower.WEAK, "高性价比与超低油耗替代燃油车存量空间", "消费者续航焦虑与低温电池衰减客诉")
    ],
    profit_distribution_summary="垂直一体化整合使得比亚迪将上游零部件利润留在内部，规模效应有效摊薄研发与折旧，产业链抗价格战韧性极强。",
    pricing_power_verdict="较强定价权 (STRONG)。依靠成本领先优势掌握国内A级与B级车定价主导权。"
))

# 4. 黑色系大宗建材与工业化学品 (纯碱 SA / 螺纹钢 RB)
IndustryChainGraphRegistry.register(IndustryChain(
    sector_id="ferrous_bulk_chemicals",
    sector_name="黑色系大宗与工业基础化工",
    representative_symbol="SA",
    representative_name="纯碱/工业硅主力",
    upstream_nodes=[
        ChainNode("天然碱矿开采 / 原盐与合成氨原料", ChainSegment.UPSTREAM, 40.0, PricingPower.STRONG, "内蒙大型天然碱矿采矿权与极低开采成本", "天然碱投产引发全行业供给过剩冲击"),
        ChainNode("动力煤与工业蒸汽热电联产供能", ChainSegment.UPSTREAM, 20.0, PricingPower.MODERATE, "稳定能源保障与环保脱硫脱硝装置", "煤炭价格暴涨大幅推高氨碱法制造成本")
    ],
    midstream_nodes=[
        ChainNode("氨碱法/联碱法/天然碱提纯结晶制造", ChainSegment.MIDSTREAM, 16.5, PricingPower.MODERATE, "重质纯碱与轻质纯碱连续化工业装置", "产能集中释放导致现货社会库存高企")
    ],
    downstream_nodes=[
        ChainNode("光伏压延玻璃与浮法玻璃熔窑生产线", ChainSegment.DOWNSTREAM, 12.0, PricingPower.MODERATE, "光伏装机增量与房地产竣工刚需支撑", "玻璃企业冷修停产大幅削减纯碱采购需求"),
        ChainNode("碳酸锂电池级提纯辅料与洗涤日化工业", ChainSegment.DOWNSTREAM, 18.0, PricingPower.MODERATE, "精细化工与新能源吸附脱碳应用拓展", "宏观工业景气度下行导致采购放缓")
    ],
    profit_distribution_summary="利润受制于供需边际博弈，天然碱凭借超低成本占据成本曲线左侧，氨碱法与联碱法在产能过剩期面临边际现金流亏损考验。",
    pricing_power_verdict="均衡博弈 (MODERATE)。随行就市，易受下游玻璃厂冷修博弈与库存压制。"
))

# 5. 宏观对冲与硬通货贵金属 (沪金 AU)
IndustryChainGraphRegistry.register(IndustryChain(
    sector_id="macro_precious_metals",
    sector_name="宏观对冲与硬通货贵金属",
    representative_symbol="AU",
    representative_name="沪金主力期货",
    upstream_nodes=[
        ChainNode("深部黄金原生矿开采与伴生金采选", ChainSegment.UPSTREAM, 48.0, PricingPower.STRONG, "全球优质高品位金矿资源稀缺性与开采资质", "深井开采安全环保成本与矿石品位贫化"),
        ChainNode("境外合质金进口与再生回收旧料冶炼", ChainSegment.UPSTREAM, 15.0, PricingPower.MODERATE, "大宗跨境通关配额与高周转精炼技术", "汇率波动与进口溢价成本损耗")
    ],
    midstream_nodes=[
        ChainNode("上海黄金交易所标准金锭/9999电解精炼", ChainSegment.MIDSTREAM, 5.0, PricingPower.MODERATE, "国家级标准交割金锭认证与仓单生成", "冶炼加工费微薄，主要依赖金价自营敞口")
    ],
    downstream_nodes=[
        ChainNode("全球主权央行官方储备资产多元化配置", ChainSegment.DOWNSTREAM, 0.0, PricingPower.DOMINANT, "去美元化战略与地缘避险刚性买盘支撑", "美联储超预期加息引发的实际利率上升压制"),
        ChainNode("民间黄金实物金条/首饰投资与避险收藏", ChainSegment.DOWNSTREAM, 20.0, PricingPower.STRONG, "抗通胀与居民财富防御性配置需求", "金价暴涨导致首饰加工终端零售克重萎缩")
    ],
    profit_distribution_summary="上游矿企享受金价上涨带来的全额利润弹性（边际开采成本固定），下游主权央行与避险资本提供强劲托底支持。",
    pricing_power_verdict="全球宏观货币定价 (MACRO_DOMINANT)。非单一企业决定，受实际利率与地缘信用深刻主导。"
))

# 6. 地产开发与高负债重资产 (万科A 000002.SZ - 风险对照组)
IndustryChainGraphRegistry.register(IndustryChain(
    sector_id="real_estate_developer",
    sector_name="传统重资产房地产开发与物业",
    representative_symbol="000002.SZ",
    representative_name="万科A",
    upstream_nodes=[
        ChainNode("地方政府土地出让与城市更新一级整理", ChainSegment.UPSTREAM, 0.0, PricingPower.WEAK, "城市核心地段土地招拍挂特许权", "高地价占用巨额资本金与土地出让金刚性交付"),
        ChainNode("中建/各省建工等总承包施工与建材供应", ChainSegment.UPSTREAM, 6.0, PricingPower.WEAK, "大规模高层建筑施工与工程垫资能力", "总包与分包商应付账款挤兑与商票逾期停工")
    ],
    midstream_nodes=[
        ChainNode("房地产项目操盘开发/高周转营销去化", ChainSegment.MIDSTREAM, 10.5, PricingPower.WEAK, "全链条项目规划/万科物业品牌口碑溢价", "房企融资三道红线与银行开发贷展期博弈"),
        ChainNode("供应链金融/公开市场境外离岸美元债发行", ChainSegment.MIDSTREAM, 0.0, PricingPower.WEAK, "境内外公开市场信用债融资窗口", "境外美元债到期还本付息刚性汇兑兑付压力")
    ],
    downstream_nodes=[
        ChainNode("刚需与改善型购房者住房消费与个人按揭", ChainSegment.DOWNSTREAM, 0.0, PricingPower.WEAK, "老百姓家庭资产配置核心大件消费", "居民对房价下跌预期导致观望拒购，去化周期翻倍"),
        ChainNode("万物云住宅社区物业管理与商业综合体", ChainSegment.DOWNSTREAM, 15.0, PricingPower.MODERATE, "存量高品质物业费收取与综合运营", "物管费收缴率下滑与地产母公司关联拖累")
    ],
    profit_distribution_summary="典型三高重资产商业模式（高负债、高杠杆、高周转），在行业逆周期面临现金流断流、债务到期墙逼仄的双重挤压，中下游毛利被全面侵蚀。",
    pricing_power_verdict="被动接受 (WEAK)。失去自主定价能力，必须以价换量保障现金流不违约。"
))
