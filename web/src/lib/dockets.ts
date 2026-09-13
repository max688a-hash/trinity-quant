export type AdmissionDocket = {
  name: string;
  symbol: string;
  grade: string;
  horizon: string;
  blood_purity: number;
  debt_toxicity: number;
  intrinsic_value: number;
  safety_margin_pct: number;
  admission_reasons: string[];
  expulsion_triggers: string[];
  current_action_advice: string;
  is_buyable_now: boolean;
};

export const ADMISSION_DOCKETS: Record<string, AdmissionDocket> = {
      '600519.SH': {
        name: '贵州茅台', symbol: '600519.SH', grade: 'AAA', horizon: '长期价值堡垒 (1~3年)',
        blood_purity: 0.88, debt_toxicity: 0.03, intrinsic_value: 1850.0, safety_margin_pct: 16.2,
        admission_reasons: [
          '主营造血极纯：经营现金流/净利润比值持续保持在 1.15 以上，全市场排名前 0.1%',
          '负债结构无毒：几乎无有息负债，货币资金充沛，完全免疫债务到期墙风险',
          '永续定价壁垒：品牌心智护城河深厚，自由现金流抗通胀与抗通缩能力极强'
        ],
        expulsion_triggers: [
          '微观造血纯度 Φ_CP 连续两季滑落至 0.30 以下',
          '大股东或核心关联方进行集中竞价折价大宗抛售甩卖',
          '发生系统性食品安全事故或企业治理法证造假违规'
        ],
        current_action_advice: '处于引力价值安全边际区间 (+16.2%)，造血强劲，适合长期底仓低吸',
        is_buyable_now: true
      },
      '300750.SZ': {
        name: '宁德时代', symbol: '300750.SZ', grade: 'AA', horizon: '中期反转套利 (3~12月)',
        blood_purity: 0.65, debt_toxicity: 0.22, intrinsic_value: 235.0, safety_margin_pct: 17.0,
        admission_reasons: [
          '动力电池全球市占率超36%，海外产能扩张驱动第二增长曲线现金回流',
          '研发费用转化效率高，单位Wh制造成本行业最低，具备深度成本护城河',
          '经营性现金流覆盖全部资本开支，摆脱早期高负债扩张的失血依赖'
        ],
        expulsion_triggers: [
          '碳酸锂等上游原料出现恶性价格战导致毛利率跌破 15% 警戒线',
          '欧美地缘政治壁垒导致海外出海订单出现单季超过 40% 闪崩',
          '微观债务毒性 Ω_Debt 突破 0.40 硬性排毒阈值'
        ],
        current_action_advice: '估值位于中枢下方，海外扩产进入利润兑现期，适合周期建仓',
        is_buyable_now: true
      },
      '600900.SH': {
        name: '长江电力', symbol: '600900.SH', grade: 'AAA', horizon: '长期价值堡垒 (1~3年)',
        blood_purity: 0.92, debt_toxicity: 0.28, intrinsic_value: 33.5, safety_margin_pct: 11.0,
        admission_reasons: [
          '全球最大水电清洁能源走廊，六库联调带来无可替代的水电永续造血',
          '资本开支高峰已过，未来10年进入纯现金分红收割期，股息率稳健',
          '宏观弱周期下的绝对防御定海神针，抗系统性经济波动属性极强'
        ],
        expulsion_triggers: [
          '长江流域遭遇百年未有特大干旱导致来水连续三年偏枯超 30%',
          '公司分红政策重大恶化，现金分红比例低于 60% 法定承诺',
          '现价大幅透支未来现金流，安全边际转负（折价率 < -20%）'
        ],
        current_action_advice: '高股息防御底仓，引力中枢向上，适合熊市及震荡市长期配置',
        is_buyable_now: true
      },
      '002594.SZ': {
        name: '比亚迪', symbol: '002594.SZ', grade: 'AA', horizon: '中期反转套利 (3~12月)',
        blood_purity: 0.58, debt_toxicity: 0.31, intrinsic_value: 310.0, safety_margin_pct: 13.5,
        admission_reasons: [
          '全产业链垂直整合（电池、IGBT芯片、整车），规模效应与成本控制极强',
          '高端仰望/腾势系列与出海高毛利车型逐步放量，单车净利润中枢抬升',
          '应收账款周转天数优于整车行业均值，营运资金造血稳定'
        ],
        expulsion_triggers: [
          '国内价格战再度白热化导致整车单车利润跌破 ¥3,000 元生死线',
          '资产负债率上升且债务毒性突破 0.40 警戒线',
          '月度交付销量出现连续三个月同比负增长'
        ],
        current_action_advice: '出海放量支撑估值，安全边际 13.5%，适合逢回调中期介入',
        is_buyable_now: true
      },
      '600036.SH': {
        name: '招商银行', symbol: '600036.SH', grade: 'AAA', horizon: '长期价值堡垒 (1~3年)',
        blood_purity: 0.72, debt_toxicity: 0.18, intrinsic_value: 42.0, safety_margin_pct: 17.8,
        admission_reasons: [
          '零售之王活期存款占比全行业领先，负债端综合资金成本极低',
          '不良贷款拨备覆盖率超过 430%，真实资产质量远高于行业报表',
          '非息财富管理中收长期空间广阔，ROE稳居上市银行第一梯队'
        ],
        expulsion_triggers: [
          '房地产与地方城投不良暴露导致拨备覆盖率跌破 250% 安全线',
          '净息差 (NIM) 持续恶化跌破 1.40% 导致微观造血严重失血',
          '管理层发生重大违规违法法证事件导致信誉折价'
        ],
        current_action_advice: '估值处于历史 15% 分位极值低点，股息率 > 5%，适合长期配置',
        is_buyable_now: true
      },
      '601318.SH': {
        name: '中国平安', symbol: '601318.SH', grade: 'AA', horizon: '中期反转套利 (3~12月)',
        blood_purity: 0.55, debt_toxicity: 0.25, intrinsic_value: 55.0, safety_margin_pct: 17.8,
        admission_reasons: [
          '寿险改革成效显现，代理人人均新业务价值 (NBV) 持续双位数反弹',
          '不动产资产风险拨备已大部分出清，资产负债表潜在雷区基本排空',
          '综合金融+医疗健康生态协同，客户客均合同数与客均利润逐年递增'
        ],
        expulsion_triggers: [
          '长端国债利率持续跌破 1.8% 触发严重的利差损风险',
          '不动产投资再爆单笔超百亿计提亏损引发信任危机',
          '新业务价值增速连续两季重回负增长通道'
        ],
        current_action_advice: '安全边际近 18%，利差损担忧已被过度计价，具备中期反弹弹性',
        is_buyable_now: true
      },
      '000858.SZ': {
        name: '五粮液', symbol: '000858.SZ', grade: 'AAA', horizon: '长期价值堡垒 (1~3年)',
        blood_purity: 0.78, debt_toxicity: 0.08, intrinsic_value: 162.0, safety_margin_pct: 18.5,
        admission_reasons: [
          '浓香白酒超级龙头，千元价格带第一核心品牌，渠道库存去化良好',
          '分红比例提升至 70% 承诺，自由现金流丰沛，零有息负债',
          '传统窖池微生物群落不可复制，具备极深的核心物理护城河'
        ],
        expulsion_triggers: [
          '普五批价跌破 ¥900 元导致渠道出现严重倒挂和恶性倾销',
          '经营现金流净额跌破净利润的 50% 显露压货失真风险',
          '消费税改革超预期加重且企业无法向下游转移成本'
        ],
        current_action_advice: '安全边际超 18%，估值仅 13 倍 PE，处于严重低估状态，适合长线布局',
        is_buyable_now: true
      },
      '601899.SH': {
        name: '紫金矿业', symbol: '601899.SH', grade: 'A', horizon: '短期高弹动量 (数周)',
        blood_purity: 0.52, debt_toxicity: 0.34, intrinsic_value: 18.8, safety_margin_pct: 10.6,
        admission_reasons: [
          '全球逆周期低成本并购金铜核心矿山，铜矿产量三年复合增速超 15%',
          '主权避险与去美元化推升黄金中枢，全球电气化与AI算力拉动铜刚需',
          '矿产资源自主储量巨大，综合克金成本与吨铜成本处于全球前 25%'
        ],
        expulsion_triggers: [
          '海外矿山遭遇严重地缘政治收归国有或矿权恶性吊销',
          '全球流动性紧缩导致大宗商品铜价暴跌超 25%',
          '债务杠杆率快速攀升导致利息支出侵蚀主营利润超 30%'
        ],
        current_action_advice: '金铜共振景气度高，但注意周期性波动，适合顺势动量操作与严格止损',
        is_buyable_now: true
      }
    };
