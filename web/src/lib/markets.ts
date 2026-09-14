/* 六大市场板块与期货宇宙，从原仪表盘迁入类型化模块，禁止正弦波伪造行情。 */
export type SectorKey = "ashare" | "futures" | "hkstock" | "usstock" | "forex" | "crypto";

export const MARKET_SECTORS = {
      ashare: {
        name: 'A股市场',
        icon: '🇨🇳',
        benchmarks: [
          { code: '000001.SH', name: '上证指数', digits: 2, exchange: '上交所 (SSE)', mult: '综合点位指数', tick: '0.01点', margin: '100%', hours: '09:30-15:00', rule: 'A股主板宏观晴雨表' },
          { code: '000300.SH', name: '沪深300', digits: 2, exchange: '中证指数 (CSI)', mult: '蓝筹核心宽基', tick: '0.01点', margin: '100%', hours: '09:30-15:00', rule: '沪深核心资产大盘基准' },
          { code: '399006.SZ', name: '创业板指', digits: 2, exchange: '深交所 (SZSE)', mult: '成长科技指数', tick: '0.01点', margin: '100%', hours: '09:30-15:00', rule: '高成长创新创业企业指数' }
        ],
        assets: [
          { code: '600519.SH', name: '贵州茅台', digits: 2, unit: '元', tag: '白酒龙头', exchange: '上交所主板 (SSE)', mult: '100股/手 (股票)', tick: '0.01元', margin: '100% (无杠杆)', hours: '09:30-11:30, 13:00-15:00', rule: 'A股T+1现货交收 · 卖出计提0.05%印花税 · 10%跌停硬熔断' },
          { code: '300750.SZ', name: '宁德时代', digits: 2, unit: '元', tag: '动力电池', exchange: '深交所创业板 (SZSE)', mult: '100股/手 (股票)', tick: '0.01元', margin: '100% (无杠杆)', hours: '09:30-11:30, 13:00-15:00', rule: '创业板T+1交收 · 涨跌幅20%限制 · 需2年交易经验开通' },
          { code: '601318.SH', name: '中国平安', digits: 2, unit: '元', tag: '综合金融', exchange: '上交所主板 (SSE)', mult: '100股/手 (股票)', tick: '0.01元', margin: '100% (无杠杆)', hours: '09:30-11:30, 13:00-15:00', rule: 'A股T+1现货交收 · 卖出计提0.05%印花税 · 金融核心资产' },
          { code: '002594.SZ', name: '比亚迪', digits: 2, unit: '元', tag: '新能源车', exchange: '深交所主板 (SZSE)', mult: '100股/手 (股票)', tick: '0.01元', margin: '100% (无杠杆)', hours: '09:30-11:30, 13:00-15:00', rule: 'A股T+1现货交收 · 卖出计提0.05%印花税 · 新能源汽车整车龙头' },
          { code: '600036.SH', name: '招商银行', digits: 2, unit: '元', tag: '零售银行', exchange: '上交所主板 (SSE)', mult: '100股/手 (股票)', tick: '0.01元', margin: '100% (无杠杆)', hours: '09:30-11:30, 13:00-15:00', rule: 'A股T+1现货交收 · 零售之王 · 高ROE护城河资产' },
          { code: '600900.SH', name: '长江电力', digits: 2, unit: '元', tag: '高股息现金牛', exchange: '上交所主板 (SSE)', mult: '100股/手 (股票)', tick: '0.01元', margin: '100% (无杠杆)', hours: '09:30-11:30, 13:00-15:00', rule: 'A股T+1现货交收 · 大水电永续现金流 · 防御定海神针' },
          { code: '000858.SZ', name: '五粮液', digits: 2, unit: '元', tag: '高端浓香', exchange: '深交所主板 (SZSE)', mult: '100股/手 (股票)', tick: '0.01元', margin: '100% (无杠杆)', hours: '09:30-11:30, 13:00-15:00', rule: 'A股T+1现货交收 · 卖出计提0.05%印花税 · 浓香白酒龙头' },
          { code: '601899.SH', name: '紫金矿业', digits: 2, unit: '元', tag: '金铜资源', exchange: '上交所主板 (SSE)', mult: '100股/手 (股票)', tick: '0.01元', margin: '100% (无杠杆)', hours: '09:30-11:30, 13:00-15:00', rule: 'A股T+1现货交收 · 全球金铜矿业巨头 · 周期对冲资产' }
        ]
      },
      futures: {
        name: '国内期货',
        icon: '🌾',
        categories: [
          { id: 'all', name: '全部 (34)' },
          { id: 'financial', name: '🏛️ 金融国债 (6)' },
          { id: 'metals', name: '🏗️ 黑色建材 (5)' },
          { id: 'nonferrous', name: '🥇 有色新能源 (7)' },
          { id: 'energy', name: '🛢️ 能化能源 (8)' },
          { id: 'agriculture', name: '🌾 农产品软商品 (8)' }
        ],
        benchmarks: [
          { code: 'NHCI', name: '南华商品综合指数', digits: 2, exchange: '南华期货研究所', mult: '商品综合基准', tick: '0.01点', margin: '100%', hours: '09:00-15:00', rule: '大宗商品整体周期风向标' },
          { code: 'IF00', name: '沪深300期指主力', digits: 1, exchange: '中金所 (CFFEX)', mult: '300元/点', tick: '0.2点', margin: '12%', hours: '09:30-15:00', rule: '现金交割·自然人可参与·股指主力' }
        ],
        assets: [
          // 🏛️ 金融国债 (CFFEX 中金所 - 6只)
          { code: 'IF', name: '沪深300期指', cat: 'financial', digits: 1, unit: '点', tag: '中金所·蓝筹', exchange: '中金所 (CFFEX)', mult: '300元/点 (波动0.2点=¥60)', tick: '0.2点', margin: '12% (8.3倍)', hours: '09:30-11:30, 13:00-15:00', rule: '现金交割·允许个人投资者交割结算·双向T+0' },
          { code: 'IC', name: '中证500期指', cat: 'financial', digits: 1, unit: '点', tag: '中金所·成长', exchange: '中金所 (CFFEX)', mult: '200元/点 (波动0.2点=¥40)', tick: '0.2点', margin: '12% (8.3倍)', hours: '09:30-11:30, 13:00-15:00', rule: '现金交割·中盘成长股对冲核心·双向T+0' },
          { code: 'IM', name: '中证1000期指', cat: 'financial', digits: 1, unit: '点', tag: '中金所·微盘', exchange: '中金所 (CFFEX)', mult: '200元/点 (波动0.2点=¥40)', tick: '0.2点', margin: '12% (8.3倍)', hours: '09:30-11:30, 13:00-15:00', rule: '现金交割·小微盘创新对冲利器·双向T+0' },
          { code: 'IH', name: '上证50期指', cat: 'financial', digits: 1, unit: '点', tag: '中金所·超大盘', exchange: '中金所 (CFFEX)', mult: '300元/点 (波动0.2点=¥60)', tick: '0.2点', margin: '12% (8.3倍)', hours: '09:30-11:30, 13:00-15:00', rule: '现金交割·银行/高股息大权重对冲·双向T+0' },
          { code: 'T', name: '十年国债期指', cat: 'financial', digits: 3, unit: '元', tag: '中金所·利率基准', exchange: '中金所 (CFFEX)', mult: '100万元/张 (波动0.005=¥50)', tick: '0.005元', margin: '3% (33倍)', hours: '09:15-11:30, 13:00-15:15', rule: '实物交割·宏观无风险利率定海神针·无夜盘' },
          { code: 'TL', name: '三十年国债期指', cat: 'financial', digits: 3, unit: '元', tag: '中金所·超长久期', exchange: '中金所 (CFFEX)', mult: '100万元/张 (波动0.01=¥100)', tick: '0.01元', margin: '3.5% (28倍)', hours: '09:15-11:30, 13:00-15:15', rule: '实物交割·超长久期高弹性资产·无夜盘' },

          // 🏗️ 黑色建材 (SHFE 上期所 / DCE 大商所 - 5只)
          { code: 'RB', name: '螺纹钢期货', cat: 'metals', digits: 0, unit: '元/吨', tag: '上期所·建材', exchange: '上期所 (SHFE)', mult: '10吨/手 (波动1点=¥10)', tick: '1.0元/吨', margin: '10% (10倍)', hours: '09:00-11:30, 13:30-15:00, 21:00-23:00', rule: '⚠️ 自然人客户禁止进入交割月！到期前必须强制平仓' },
          { code: 'HC', name: '热轧卷板期货', cat: 'metals', digits: 0, unit: '元/吨', tag: '上期所·工业板材', exchange: '上期所 (SHFE)', mult: '10吨/手 (波动1点=¥10)', tick: '1.0元/吨', margin: '10% (10倍)', hours: '09:00-11:30, 13:30-15:00, 21:00-23:00', rule: '⚠️ 自然人客户禁止进入交割月！工业用钢主力' },
          { code: 'I', name: '铁矿石期货', cat: 'metals', digits: 1, unit: '元/吨', tag: '大商所·冶炼原料', exchange: '大商所 (DCE)', mult: '100吨/手 (波动0.5点=¥50)', tick: '0.5元/吨', margin: '13% (7.7倍)', hours: '09:00-11:30, 13:30-15:00, 21:00-23:00', rule: '特定品种·保税交割·自然人客户禁止交割' },
          { code: 'J', name: '焦炭期货', cat: 'metals', digits: 1, unit: '元/吨', tag: '大商所·高弹性炉料', exchange: '大商所 (DCE)', mult: '100吨/手 (波动0.5点=¥50)', tick: '0.5元/吨', margin: '15% (6.7倍)', hours: '09:00-11:30, 13:30-15:00, 21:00-23:00', rule: '⚠️ 自然人客户禁止进入交割月！波动极大强平防爆' },
          { code: 'JM', name: '焦煤期货', cat: 'metals', digits: 1, unit: '元/吨', tag: '大商所·炼焦母煤', exchange: '大商所 (DCE)', mult: '60吨/手 (波动0.5点=¥30)', tick: '0.5元/吨', margin: '15% (6.7倍)', hours: '09:00-11:30, 13:30-15:00, 21:00-23:00', rule: '⚠️ 自然人客户禁止进入交割月！母焦煤保供核心' },

          // 🥇 有色与新能源金属 (SHFE 上期所 / GFEX 广期所 - 7只)
          { code: 'CU', name: '沪铜期货', cat: 'nonferrous', digits: 0, unit: '元/吨', tag: '上期所·铜博士', exchange: '上期所 (SHFE)', mult: '5吨/手 (波动10点=¥50)', tick: '10元/吨', margin: '12% (8.3倍)', hours: '09:00-11:30, 13:30-15:00, 21:00-01:00', rule: '宏观经济晴雨表·铜博士·自然人客户禁止交割' },
          { code: 'AL', name: '沪铝期货', cat: 'nonferrous', digits: 0, unit: '元/吨', tag: '上期所·轻量工业', exchange: '上期所 (SHFE)', mult: '5吨/手 (波动5点=¥25)', tick: '5元/吨', margin: '10% (10倍)', hours: '09:00-11:30, 13:30-15:00, 21:00-23:00', rule: '电解铝能耗双控·自然人客户禁止交割' },
          { code: 'ZN', name: '沪锌期货', cat: 'nonferrous', digits: 0, unit: '元/吨', tag: '上期所·镀锌基石', exchange: '上期所 (SHFE)', mult: '5吨/手 (波动5点=¥25)', tick: '5元/吨', margin: '10% (10倍)', hours: '09:00-11:30, 13:30-15:00, 21:00-23:00', rule: '镀锌防腐工业母材·自然人客户禁止交割' },
          { code: 'NI', name: '沪镍期货', cat: 'nonferrous', digits: 0, unit: '元/吨', tag: '上期所·高烈度有色', exchange: '上期所 (SHFE)', mult: '1吨/手 (波动10点=¥10)', tick: '10元/吨', margin: '14% (7.1倍)', hours: '09:00-11:30, 13:30-15:00, 21:00-01:00', rule: '不锈钢与三元动力电池原料·自然人客户禁止交割' },
          { code: 'AU', name: '沪金期货', cat: 'nonferrous', digits: 2, unit: '元/克', tag: '上期所·主权避险', exchange: '上期所 (SHFE)', mult: '1000克/手 (波动0.02=¥20)', tick: '0.02元/克', margin: '10% (10倍)', hours: '09:00-11:30, 13:30-15:00, 21:00-02:30', rule: '全球硬通货避险·自然人客户禁止进入交割月' },
          { code: 'AG', name: '沪银期货', cat: 'nonferrous', digits: 0, unit: '元/千克', tag: '上期所·高弹贵金', exchange: '上期所 (SHFE)', mult: '15千克/手 (波动1点=¥15)', tick: '1元/千克', margin: '12% (8.3倍)', hours: '09:00-11:30, 13:30-15:00, 21:00-02:30', rule: '工业光伏与金融双重属性·自然人客户禁止交割' },
          { code: 'LC', name: '碳酸锂期货', cat: 'nonferrous', digits: 0, unit: '元/吨', tag: '广期所·白色石油', exchange: '广期所 (GFEX)', mult: '1吨/手 (波动50点=¥50)', tick: '50元/吨', margin: '14% (7.1倍)', hours: '09:00-11:30, 13:30-15:00', rule: '锂电储能新能源命脉·无夜盘·自然人禁止交割' },

          // 🛢️ 能化能源 (INE 能源中心 / CZCE 郑商所 / DCE 大商所 / SHFE 上期所 - 8只)
          { code: 'SC', name: '原油期货', cat: 'energy', digits: 1, unit: '元/桶', tag: '上期能源·大宗之王', exchange: '上海国际能源交易中心 (INE)', mult: '1000桶/手 (波动0.1=¥100)', tick: '0.1元/桶', margin: '12% (8.3倍)', hours: '09:00-11:30, 13:30-15:00, 21:00-02:30', rule: '国际特定品种·保税实物交割·自然人客户禁止交割' },
          { code: 'SA', name: '纯碱期货', cat: 'energy', digits: 0, unit: '元/吨', tag: '郑商所·化工龙头', exchange: '郑商所 (CZCE)', mult: '20吨/手 (波动1点=¥20)', tick: '1元/吨', margin: '12% (8.3倍)', hours: '09:00-11:30, 13:30-15:00, 21:00-23:00', rule: '浮法玻璃与光伏组件原料·自然人客户禁止交割' },
          { code: 'FG', name: '玻璃期货', cat: 'energy', digits: 0, unit: '元/吨', tag: '郑商所·建材能化', exchange: '郑商所 (CZCE)', mult: '20吨/手 (波动1点=¥20)', tick: '1元/吨', margin: '12% (8.3倍)', hours: '09:00-11:30, 13:30-15:00, 21:00-23:00', rule: '房地产竣工链主力·自然人客户禁止进入交割月' },
          { code: 'MA', name: '甲醇期货', cat: 'energy', digits: 0, unit: '元/吨', tag: '郑商所·煤化工', exchange: '郑商所 (CZCE)', mult: '10吨/手 (波动1点=¥10)', tick: '1元/吨', margin: '10% (10倍)', hours: '09:00-11:30, 13:30-15:00, 21:00-23:00', rule: '煤制烯烃MTO原料·自然人客户禁止进入交割月' },
          { code: 'TA', name: 'PTA期货', cat: 'energy', digits: 0, unit: '元/吨', tag: '郑商所·化纤织造', exchange: '郑商所 (CZCE)', mult: '5吨/手 (波动2点=¥10)', tick: '2元/吨', margin: '10% (10倍)', hours: '09:00-11:30, 13:30-15:00, 21:00-23:00', rule: '特定品种·涤纶化纤服装原料·自然人禁止交割' },
          { code: 'PP', name: '聚丙烯期货', cat: 'energy', digits: 0, unit: '元/吨', tag: '大商所·塑料包材', exchange: '大商所 (DCE)', mult: '5吨/手 (波动1点=¥5)', tick: '1元/吨', margin: '10% (10倍)', hours: '09:00-11:30, 13:30-15:00, 21:00-23:00', rule: '医疗防护与日用包装注塑·自然人禁止交割' },
          { code: 'BU', name: '沥青期货', cat: 'energy', digits: 0, unit: '元/吨', tag: '上期所·基建道路', exchange: '上期所 (SHFE)', mult: '10吨/手 (波动2点=¥20)', tick: '2元/吨', margin: '11% (9.1倍)', hours: '09:00-11:30, 13:30-15:00, 21:00-23:00', rule: '公路市政沥青铺设·自然人客户禁止交割' },
          { code: 'FU', name: '燃料油期货', cat: 'energy', digits: 0, unit: '元/吨', tag: '上期所·航运动力', exchange: '上期所 (SHFE)', mult: '10吨/手 (波动1点=¥10)', tick: '1元/吨', margin: '12% (8.3倍)', hours: '09:00-11:30, 13:30-15:00, 21:00-23:00', rule: '远洋国际船舶动力重油·自然人客户禁止交割' },

          // 🌾 农产品与软商品 (DCE 大商所 / CZCE 郑商所 - 8只)
          { code: 'C', name: '玉米期货', cat: 'agriculture', digits: 0, unit: '元/吨', tag: '大商所·谷物之王', exchange: '大商所 (DCE)', mult: '10吨/手 (波动1点=¥10)', tick: '1元/吨', margin: '8% (12.5倍)', hours: '09:00-11:30, 13:30-15:00, 21:00-23:00', rule: '国家粮食安全饲料主粮·自然人客户禁止交割' },
          { code: 'M', name: '豆粕期货', cat: 'agriculture', digits: 0, unit: '元/吨', tag: '大商所·蛋白饲料', exchange: '大商所 (DCE)', mult: '10吨/手 (波动1点=¥10)', tick: '1元/吨', margin: '8% (12.5倍)', hours: '09:00-11:30, 13:30-15:00, 21:00-23:00', rule: '生猪养殖压榨蛋白原料·自然人客户禁止交割' },
          { code: 'P', name: '棕榈油期货', cat: 'agriculture', digits: 0, unit: '元/吨', tag: '大商所·进口油脂', exchange: '大商所 (DCE)', mult: '10吨/手 (波动2点=¥20)', tick: '2元/吨', margin: '10% (10倍)', hours: '09:00-11:30, 13:30-15:00, 21:00-23:00', rule: '特定品种·生柴与食用油脂·自然人禁止交割' },
          { code: 'Y', name: '豆油期货', cat: 'agriculture', digits: 0, unit: '元/吨', tag: '大商所·家庭食用', exchange: '大商所 (DCE)', mult: '10吨/手 (波动2点=¥20)', tick: '2元/吨', margin: '8% (12.5倍)', hours: '09:00-11:30, 13:30-15:00, 21:00-23:00', rule: '大豆压榨主要食用油·自然人客户禁止交割' },
          { code: 'SR', name: '白糖期货', cat: 'agriculture', digits: 0, unit: '元/吨', tag: '郑商所·软商品', exchange: '郑商所 (CZCE)', mult: '10吨/手 (波动1点=¥10)', tick: '1元/吨', margin: '9% (11.1倍)', hours: '09:00-11:30, 13:30-15:00, 21:00-23:00', rule: '甜菜与甘蔗产销榨季周期·自然人禁止交割' },
          { code: 'CF', name: '棉花期货', cat: 'agriculture', digits: 0, unit: '元/吨', tag: '郑商所·纺织原料', exchange: '郑商所 (CZCE)', mult: '5吨/手 (波动5点=¥25)', tick: '5元/吨', margin: '9% (11.1倍)', hours: '09:00-11:30, 13:30-15:00, 21:00-23:00', rule: '新疆与全球棉纺保供·自然人客户禁止交割' },
          { code: 'LH', name: '生猪期货', cat: 'agriculture', digits: 0, unit: '元/吨', tag: '大商所·二师兄', exchange: '大商所 (DCE)', mult: '16吨/手 (波动5点=¥80)', tick: '5元/吨', margin: '12% (8.3倍)', hours: '09:00-11:30, 13:30-15:00', rule: '活体生猪实物交割·个人禁止交割·无夜盘' },
          { code: 'AP', name: '苹果期货', cat: 'agriculture', digits: 0, unit: '元/吨', tag: '郑商所·生鲜特产', exchange: '郑商所 (CZCE)', mult: '10吨/手 (波动1点=¥10)', tick: '1元/吨', margin: '11% (9.1倍)', hours: '09:00-11:30, 13:30-15:00', rule: '红富士冷库现货交割·自然人客户禁止交割' }
        ]
      },
      hkstock: {
        name: '港股市场',
        icon: '🇭🇰',
        benchmarks: [
          { code: 'HSI', name: '恒生指数', digits: 2, exchange: '香港交易所 (HKEX)', mult: '恒指基准点位', tick: '0.01点', margin: '100%', hours: '09:30-16:00', rule: '港股核心资产指数' },
          { code: 'HSTECH', name: '恒生科技指数', digits: 2, exchange: '香港交易所 (HKEX)', mult: '科技旗舰指数', tick: '0.01点', margin: '100%', hours: '09:30-16:00', rule: '中国科技互联网三十强' }
        ],
        assets: [
          { code: '0700.HK', name: '腾讯控股', digits: 2, unit: 'HKD', tag: '社交与游戏', exchange: '港交所主板 (HKEX)', mult: '100股/手', tick: '0.20 HKD', margin: '100% (无杠杆)', hours: '09:30-12:00, 13:00-16:00', rule: '港股T+0回转交易 · 双边0.10%印花税 · 无涨跌幅限制' },
          { code: '9988.HK', name: '阿里巴巴', digits: 2, unit: 'HKD', tag: '电商与云计算', exchange: '港交所主板 (HKEX)', mult: '100股/手', tick: '0.05 HKD', margin: '100% (无杠杆)', hours: '09:30-12:00, 13:00-16:00', rule: '港股T+0回转交易 · 双边0.10%印花税 · 双重主要上市' },
          { code: '3690.HK', name: '美团-W', digits: 2, unit: 'HKD', tag: '本地生活', exchange: '港交所主板 (HKEX)', mult: '100股/手', tick: '0.10 HKD', margin: '100% (无杠杆)', hours: '09:30-12:00, 13:00-16:00', rule: '港股T+0回转交易 · 双边0.10%印花税 · 同股不同权(W)' },
          { code: '1810.HK', name: '小米集团', digits: 2, unit: 'HKD', tag: '人车家生态', exchange: '港交所主板 (HKEX)', mult: '200股/手', tick: '0.02 HKD', margin: '100% (无杠杆)', hours: '09:30-12:00, 13:00-16:00', rule: '港股T+0回转交易 · 双边0.10%印花税 · 消费电子龙头' },
          { code: '1024.HK', name: '快手-W', digits: 2, unit: 'HKD', tag: '短视频生态', exchange: '港交所主板 (HKEX)', mult: '100股/手', tick: '0.05 HKD', margin: '100% (无杠杆)', hours: '09:30-12:00, 13:00-16:00', rule: '港股T+0回转交易 · 双边0.10%印花税 · 短视频与直播电商' }
        ]
      },
      usstock: {
        name: '美股市场',
        icon: '🇺🇸',
        benchmarks: [
          { code: 'SPX', name: '标普500指数', digits: 2, exchange: 'CBOE / S&P', mult: '大盘代表', tick: '0.01点', margin: '100%', hours: '21:30-04:00 (夏令)', rule: '全球资本市场锚' },
          { code: 'NDX', name: '纳斯达克100', digits: 2, exchange: 'NASDAQ', mult: '科技旗舰', tick: '0.01点', margin: '100%', hours: '21:30-04:00 (夏令)', rule: '全球科技创新龙头基准' }
        ],
        assets: [
          { code: 'NVDA', name: '英伟达 (NVIDIA)', digits: 2, unit: 'USD', tag: 'AI计算基座', exchange: 'NASDAQ', mult: '1股/手', tick: '0.01 USD', margin: '100% (无杠杆)', hours: '21:30-04:00 (夏令时)', rule: '美股T+1清算 · 0印花税 · 无涨跌幅限制 · 盘前盘后交易' },
          { code: 'AAPL', name: '苹果 (Apple)', digits: 2, unit: 'USD', tag: '全球消费电子', exchange: 'NASDAQ', mult: '1股/手', tick: '0.01 USD', margin: '100% (无杠杆)', hours: '21:30-04:00 (夏令时)', rule: '美股T+1清算 · 0印花税 · 极致现金流与回购典范' },
          { code: 'TSLA', name: '特斯拉 (Tesla)', digits: 2, unit: 'USD', tag: '智驾与储能', exchange: 'NASDAQ', mult: '1股/手', tick: '0.01 USD', margin: '100% (无杠杆)', hours: '21:30-04:00 (夏令时)', rule: '美股T+1清算 · 0印花税 · 自动驾驶与机器人' },
          { code: 'MSFT', name: '微软 (Microsoft)', digits: 2, unit: 'USD', tag: '企业云与AI', exchange: 'NASDAQ', mult: '1股/手', tick: '0.01 USD', margin: '100% (无杠杆)', hours: '21:30-04:00 (夏令时)', rule: '美股T+1清算 · 0印花税 · 全球企业生产力与云计算基石' },
          { code: 'GOOGL', name: '谷歌 (Alphabet)', digits: 2, unit: 'USD', tag: '搜索与模型', exchange: 'NASDAQ', mult: '1股/手', tick: '0.01 USD', margin: '100% (无杠杆)', hours: '21:30-04:00 (夏令时)', rule: '美股T+1清算 · 0印花税 · 全球搜索与前沿AI生态' }
        ]
      },
      forex: {
        name: '全球外汇',
        icon: '💱',
        benchmarks: [
          { code: 'DXY', name: '美元指数', digits: 2, exchange: 'ICE', mult: '货币篮子指数', tick: '0.01点', margin: '100%', hours: '24小时连续', rule: '全球主要货币汇率定海神针' }
        ],
        assets: [
          { code: 'USDCNH', name: '美元/离岸人民币', digits: 4, unit: '汇率', tag: '中美经贸锚', exchange: '场外银行间市场 (OTC)', mult: '100,000基准货币/手', tick: '0.0001 (1点=10 USD)', margin: '2% (50倍杠杆)', hours: '周一早05:00至周六早05:00 (24h)', rule: 'T+0双向交易 · 0印花税 · 隔夜计提利息Swaps' },
          { code: 'EURUSD', name: '欧元/美元', digits: 4, unit: '汇率', tag: '全球最大货币对', exchange: '场外银行间市场 (OTC)', mult: '100,000 EUR/手', tick: '0.0001 (1点=10 USD)', margin: '2% (50倍杠杆)', hours: '周一早05:00至周六早05:00 (24h)', rule: 'T+0双向交易 · 全球流动性之巅 · 极低点差' },
          { code: 'USDJPY', name: '美元/日元', digits: 2, unit: '汇率', tag: '套息交易枢纽', exchange: '场外银行间市场 (OTC)', mult: '100,000 USD/手', tick: '0.01 (1点=1000 JPY)', margin: '2% (50倍杠杆)', hours: '周一早05:00至周六早05:00 (24h)', rule: 'T+0双向交易 · 全球利差套利Carry Trade风暴眼' },
          { code: 'GBPUSD', name: '英镑/美元', digits: 4, unit: '汇率', tag: '高波动欧系币', exchange: '场外银行间市场 (OTC)', mult: '100,000 GBP/手', tick: '0.0001 (1点=10 USD)', margin: '2% (50倍杠杆)', hours: '周一早05:00至周六早05:00 (24h)', rule: 'T+0双向交易 · 伦敦外汇交易中心主力品种' }
        ]
      },
      crypto: {
        name: '加密资产(24/7)',
        icon: '🪙',
        benchmarks: [
          { code: 'TOTAL', name: '全球加密总市值', digits: 2, exchange: '链上清算聚合', mult: '市值指数', tick: '0.01B', margin: '100%', hours: '7x24x365永续', rule: '全天候无间断加密市场' }
        ],
        assets: [
          { code: 'BTCUSDT', name: '比特币 (BTC)', digits: 1, unit: 'USDT', tag: '数字黄金', exchange: 'Binance / OKX', mult: '1 BTC / 永续合约', tick: '0.1 USDT', margin: '5% (20倍杠杆)', hours: '7x24x365 全天候永续', rule: '永续合约资金费率每8小时结算 · 零印花税' },
          { code: 'ETHUSDT', name: '以太坊 (ETH)', digits: 2, unit: 'USDT', tag: '世界计算机', exchange: 'Binance / OKX', mult: '1 ETH / 永续合约', tick: '0.01 USDT', margin: '5% (20倍杠杆)', hours: '7x24x365 全天候永续', rule: '智能合约公链燃料 · 资金费率机制 · 7x24连续' },
          { code: 'SOLUSDT', name: '索拉纳 (SOL)', digits: 2, unit: 'USDT', tag: '高频公链', exchange: 'Binance / OKX', mult: '1 SOL / 永续合约', tick: '0.01 USDT', margin: '10% (10倍杠杆)', hours: '7x24x365 全天候永续', rule: '高TPS去中心化公链 · 永续清算 · 7x24连续' },
          { code: 'BNBUSDT', name: '币安币 (BNB)', digits: 1, unit: 'USDT', tag: '平台生态', exchange: 'Binance', mult: '1 BNB / 永续合约', tick: '0.01 USDT', margin: '10% (10倍杠杆)', hours: '7x24x365 全天候永续', rule: '平台通缩销毁机制 · 手续费折扣 · 7x24连续' }
        ]
      }
    } as const;
