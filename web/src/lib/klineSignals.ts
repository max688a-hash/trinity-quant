import type { Candle } from "./types";

function sma(values: number[], end: number, window: number): number | undefined {
  if (end + 1 < window) {
    return undefined;
  }
  let s = 0;
  for (let i = end - window + 1; i <= end; i += 1) {
    s += values[i];
  }
  return s / window;
}

export function attachMovingAverages(candles: Candle[]): Candle[] {
  const closes = candles.map((c) => c.close);
  return candles.map((c, i) => ({
    ...c,
    ma5: sma(closes, i, 5),
    ma20: sma(closes, i, 20),
  }));
}

export function calculateDynamicSignals(candles: Candle[]): void {
  if (!candles || candles.length < 10) {
    return;
  }
  for (let i = 5; i < candles.length; i += 1) {
    const prev = candles[i - 1];
    const curr = candles[i];
    if (!prev.ma5 || !curr.ma5 || !prev.ma20 || !curr.ma20) {
      continue;
    }
    if (prev.ma5 <= prev.ma20 && curr.ma5 > curr.ma20 && curr.close > curr.open) {
      curr.signal = { type: 'BUY', text: "🔴 均线金叉(叮)", color: "#e11d48" };
    } else if (prev.ma5 >= prev.ma20 && curr.ma5 < curr.ma20 && curr.close < curr.open) {
      curr.signal = { type: 'SELL', text: "🟢 趋势破位", color: "#10b981" };
    }
  }
}

export async function loadRealKlineData(tf: string, sym: string): Promise<Candle[]> {
  const q = new URLSearchParams({ symbol: sym, tf });
  const res = await fetch(`/api/market/kline?${q.toString()}`);
  if (!res.ok) {
    throw new Error("K线接口不可用");
  }
  const data = (await res.json()) as { candles?: Candle[] };
  const candles = attachMovingAverages(data.candles ?? []);
  calculateDynamicSignals(candles);
  return candles;
}
