import type { BoardQuote } from "./types";

export function quotesBySymbol(quotes: BoardQuote[]): Record<string, BoardQuote> {
  const mapped: Record<string, BoardQuote> = {};
  for (const item of quotes) {
    mapped[item.symbol] = item;
  }
  return mapped;
}

export function formatBoardLast(quote: BoardQuote | undefined, loading: boolean): string {
  if (loading) {
    return "读取中";
  }
  if (!quote || !quote.available || quote.last == null) {
    return "DATA_UNAVAILABLE";
  }
  return quote.last.toLocaleString("zh-CN", { maximumFractionDigits: 4 });
}

export function quoteToneClass(quote: BoardQuote | undefined): string {
  if (!quote || quote.change_pct == null) {
    return "text-muted-foreground";
  }
  if (quote.change_pct > 0) {
    return "text-buy";
  }
  if (quote.change_pct < 0) {
    return "text-sell";
  }
  return "text-foreground";
}
