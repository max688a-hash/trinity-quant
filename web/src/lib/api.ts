import type { AdmissionDocket, AutopsyCase, BoardQuote, Candle, PaperState, ScreenerCandidate } from "./types";

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`请求失败 ${res.status}: ${url}`);
  }
  return (await res.json()) as T;
}

export async function fetchScreener(): Promise<{ count: number; candidates: ScreenerCandidate[] }> {
  return getJson("/api/screener");
}

export async function fetchForensicAutopsy(): Promise<{
  status: string;
  count: number;
  cases: AutopsyCase[];
}> {
  return getJson("/api/pool/autopsy");
}


export async function fetchPoolDockets(): Promise<AdmissionDocket[]> {
  return getJson("/api/pool/dockets");
}

export async function fetchPaperState(): Promise<PaperState> {
  return getJson("/api/paper_state");
}

export async function fetchKline(symbol: string, tf: string): Promise<{ candles: Candle[]; count: number }> {
  const q = new URLSearchParams({ symbol, tf });
  return getJson(`/api/market/kline?${q.toString()}`);
}

export async function fetchBoardQuotes(
  symbols: string[],
): Promise<{ quotes: BoardQuote[]; count: number }> {
  const q = new URLSearchParams({ symbols: symbols.join(",") });
  return getJson(`/api/market/quotes?${q.toString()}`);
}

export async function postPaperTrade(payload: {
  symbol: string;
  action: "BUY" | "SELL";
  quantity: number;
  price: number;
  is_replay_mode: boolean;
}): Promise<{ success: boolean; rejection_reason?: string; friction_total?: number }> {
  const res = await fetch("/api/trade", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new Error(`报单失败 ${res.status}`);
  }
  return (await res.json()) as { success: boolean; rejection_reason?: string; friction_total?: number };
}
