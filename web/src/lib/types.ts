export type TabId =
  | "tab-backtest"
  | "tab-screener"
  | "tab-reflex"
  | "tab-paper"
  | "tab-multiasset"
  | "tab-valuation"
  | "tab-autopsy"
  | "tab-pit"
  | "tab-calculator";

export type Candle = {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  ma5?: number;
  ma20?: number;
  signal?: { type: "BUY" | "SELL"; text: string; color: string };
};

export type PaperState = {
  cash: number;
  equity: number;
  max_drawdown: number;
  positions: Array<{
    symbol: string;
    quantity: number;
    avg_cost: number;
    current_price: number;
    trailing_stop: number;
    shares_frozen_t1: number;
    pnl: number;
  }>;
  positions_count: number;
  ratchet_enabled: boolean;
  t_plus_1_enforced: boolean;
};


export type BoardQuote = {
  symbol: string;
  available: boolean;
  last: number | null;
  prev: number | null;
  change_pct: number | null;
  status: string;
};

export type AutopsyCase = {
  symbol: string;
  name: string;
  phi_cp: number | null;
  omega_debt: number | null;
  is_admitted: boolean;
  is_buyable: boolean;
  veto_reasons: string[];
  period_end_date: string;
};

export type ScreenerCandidate = {
  symbol: string;
  name: string;
  phi_cp: number;
  omega_debt: number;
  alpha: number;
  gravity_value: number;
  is_qualified: boolean;
  dossier: {
    core_business: string;
    seasonality_profile: string;
    recommended_action: string;
  };
};
