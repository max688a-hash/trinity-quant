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

function holdOf(candle: Candle): number {
  const raw = (candle as Candle & { hold?: number }).hold;
  return typeof raw === "number" && Number.isFinite(raw) ? raw : 0;
}

export function attachMovingAverages(candles: Candle[]): Candle[] {
  const closes = candles.map((c) => c.close);
  return candles.map((c, i) => ({
    ...c,
    ma5: sma(closes, i, 5),
    ma20: sma(closes, i, 20),
  }));
}

export function calculateDynamicSignals(candles: Candle[], allowShort = true): void {
  const window = 20;
  if (!candles || candles.length < window + 1) {
    return;
  }
  for (let i = window; i < candles.length; i += 1) {
    const prev = candles.slice(i - window, i);
    const avgVol = prev.reduce((s, row) => s + row.volume, 0) / prev.length;
    const curr = candles[i];
    if (avgVol <= 0 || curr.volume < avgVol || curr.close <= 0) {
      continue;
    }
    const priorHigh = Math.max(...prev.map((row) => row.high));
    const priorLow = Math.min(...prev.map((row) => row.low));
    const holdNow = holdOf(curr);
    const holdWas = holdOf(candles[i - 1]);
    const oiKnown = holdNow > 0 && holdWas > 0;
    const oiUp = oiKnown ? holdNow > holdWas : null;
    if (oiUp === false) {
      continue;
    }
    if (curr.close > priorHigh) {
      const tagged = oiUp === true;
      curr.signal = {
        type: 'BUY',
        text: allowShort
          ? (tagged ? "🔴 放量增仓做多" : "🔴 放量突破做多")
          : (tagged ? "🔴 放量增仓买入" : "🔴 放量突破买入"),
        color: "#e11d48",
      };
    } else if (curr.close < priorLow) {
      curr.signal = {
        type: 'SELL',
        text: allowShort
          ? (oiUp === true ? "🟢 放量增仓做空" : "🟢 放量破位做空")
          : "🟢 放量破位卖出",
        color: "#10b981",
      };
    }
  }
}

export function listedKlineSignals(candles: Candle[]): Candle[] {
  return candles.filter((row) => row.signal?.type === 'BUY' || row.signal?.type === 'SELL');
}

export async function loadRealKlineData(tf: string, sym: string): Promise<Candle[]> {
  const q = new URLSearchParams({ symbol: sym, tf });
  const res = await fetch(`/api/market/kline?${q.toString()}`);
  if (!res.ok) {
    throw new Error("K线接口不可用");
  }
  const data = (await res.json()) as { candles?: Candle[] };
  const candles = attachMovingAverages(data.candles ?? []);
  const allowShort = !/\.(SH|SZ)$/i.test(sym);
  calculateDynamicSignals(candles, allowShort);
  return candles;
}
