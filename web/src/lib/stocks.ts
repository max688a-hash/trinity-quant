export type ScreenedStock = {
  symbol: string;
  name: string;
  category: string;
  latest_period: string;
  disclosure_date: string;
  is_admitted: boolean;
  phi_cp: number;
  omega_debt: number;
  revenue: number;
  net_profit: number;
  ocf: number;
  cash: number;
  due_1y: number;
  total_reports: number;
  veto_reasons: string[];
  gravity_val: number;
  market_cap: number;
  potential: number;
  convexity: number;
  alpha: number;
  signal: string;
};

export const STOCKS: ScreenedStock[] = [
      {
        "symbol": "600519", "name": "贵州茅台", "category": "现金流造血典范",
        "latest_period": "2026-06-30", "disclosure_date": "2026-08-28", "is_admitted": true,
        "phi_cp": 1.54, "omega_debt": 0.00, "revenue": 922.78, "net_profit": 445.17, "ocf": 706.91,
        "cash": 535.19, "due_1y": 0.00, "total_reports": 103, "veto_reasons": [],
        "gravity_val": 13342.3, "market_cap": 19500.0, "potential": -31.6, "convexity": 7.8, "alpha": 4.6, "signal": "NEUTRAL"
      },
      {
        "symbol": "002594", "name": "比亚迪", "category": "制造业造血扩张",
        "latest_period": "2026-06-30", "disclosure_date": "2026-08-28", "is_admitted": true,
        "phi_cp": 2.59, "omega_debt": 0.88, "revenue": 3724.81, "net_profit": 156.40, "ocf": 435.56,
        "cash": 948.12, "due_1y": 834.20, "total_reports": 68, "veto_reasons": [],
        "gravity_val": 2179.3, "market_cap": 8300.0, "potential": -73.7, "convexity": 6.2, "alpha": 1.4, "signal": "NEUTRAL"
      },
      {
        "symbol": "600900", "name": "长江电力", "category": "高分红防御典范",
        "latest_period": "2026-06-30", "disclosure_date": "2026-08-28", "is_admitted": false,
        "phi_cp": 1.17, "omega_debt": 2.96, "revenue": 368.10, "net_profit": 118.25, "ocf": 210.45,
        "cash": 85.30, "due_1y": 252.80, "total_reports": 96,
        "veto_reasons": ["【债务猝死否决】债务毒性 Ω_Debt=2.96 突破红线 1.20 (短期收购借款到期压顶)"],
        "gravity_val": 4128.9, "market_cap": 7100.0, "potential": -41.9, "convexity": 0.0, "alpha": 0.0, "signal": "VETO"
      },
      {
        "symbol": "000002", "name": "万科A", "category": "地产债务到期墙承压",
        "latest_period": "2026-06-30", "disclosure_date": "2026-08-28", "is_admitted": false,
        "phi_cp": 0.03, "omega_debt": 31.0, "revenue": 701.70, "net_profit": -160.20, "ocf": 5.00,
        "cash": 590.50, "due_1y": 1829.00, "total_reports": 118,
        "veto_reasons": ["【造血毒性否决】造血纯度 Φ_CP=0.03 远低于红线 0.30", "【债务猝死否决】1年内到期刚性短债 1829 亿严重压垮可用现金 590 亿"],
        "gravity_val": 820.1, "market_cap": 850.0, "potential": -3.5, "convexity": 0.0, "alpha": 0.0, "signal": "VETO"
      },
      {
        "symbol": "300104", "name": "乐视退", "category": "历史经典应收虚增与失血暴雷",
        "latest_period": "2016-12-31", "disclosure_date": "2017-04-20", "is_admitted": false,
        "phi_cp": -0.63, "omega_debt": 3.65, "revenue": 219.00, "net_profit": 5.50, "ocf": -10.60,
        "cash": 36.00, "due_1y": 97.00, "total_reports": 71,
        "veto_reasons": ["【造血毒性否决】净利润假盈5.5亿，真实经营现金流失血10.6亿，Φ_CP=-0.63", "【债务猝死否决】短期刚性到期债务 97 亿，流动现金仅 36 亿"],
        "gravity_val": 0.0, "market_cap": 15.0, "potential": -100.0, "convexity": 0.0, "alpha": 0.0, "signal": "VETO"
      },
      {
        "symbol": "600518", "name": "ST康美", "category": "历史经典存贷双高与虚假现金",
        "latest_period": "2017-12-31", "disclosure_date": "2018-04-26", "is_admitted": false,
        "phi_cp": 0.05, "omega_debt": 4.79, "revenue": 250.00, "net_profit": 35.00, "ocf": 18.00,
        "cash": 340.00, "due_1y": 230.00, "total_reports": 105,
        "veto_reasons": ["【资金虚假疑云】证监会行政查明账面 340 亿货币资金中 299 亿虚假/受限 (占比88%)"],
        "gravity_val": 62.0, "market_cap": 280.0, "potential": -77.9, "convexity": 0.0, "alpha": 0.0, "signal": "VETO"
      }
    ];
