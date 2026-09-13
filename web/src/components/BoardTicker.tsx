import { useEffect, useState } from "react";
import { fetchBoardQuotes } from "../lib/api";
import { formatBoardLast, quoteToneClass, quotesBySymbol } from "../lib/boardQuotes";
import type { BoardQuote } from "../lib/types";

const BOARD_SYMBOLS = [
  "000001.SH",
  "NHCI",
  "DXY",
  "BTCUSDT",
  "600519.SH",
  "SA",
  "USDCNH",
];

const DESKTOP_SLOTS = [
  { market: "A股证券市场", label: "上证", symbol: "000001.SH" },
  { market: "国内商品期货", label: "南华", symbol: "NHCI" },
  { market: "全球外汇市场", label: "美元指数", symbol: "DXY" },
  { market: "全球加密数字资产", label: "BTC", symbol: "BTCUSDT" },
] as const;

const MOBILE_SLOTS = [
  { label: "茅台", symbol: "600519.SH" },
  { label: "纯碱", symbol: "SA" },
  { label: "USDCNH", symbol: "USDCNH" },
  { label: "BTC", symbol: "BTCUSDT" },
] as const;

export function BoardTicker() {
  const [quotes, setQuotes] = useState<Record<string, BoardQuote>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchBoardQuotes([...BOARD_SYMBOLS])
      .then((res) => {
        if (!cancelled) {
          setQuotes(quotesBySymbol(res.quotes));
          setError(null);
        }
      })
      .catch((err: Error) => {
        if (!cancelled) {
          setError(err.message);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <>
      <div id="mobileCompactTicker" className="sticky top-0 z-40 -mx-4 mb-4 border-b border-border bg-background/95 px-4 py-2 md:hidden">
        <div className="flex gap-4 overflow-x-auto text-[13px] tabular-nums no-scrollbar">
          {MOBILE_SLOTS.map((slot) => (
            <span key={slot.symbol} className={quoteToneClass(quotes[slot.symbol])}>
              {slot.label} {formatBoardLast(quotes[slot.symbol], loading)}
            </span>
          ))}
        </div>
        {error ? <p className="mt-1 text-[11px] text-buy">行情接口不可达，缺值阻断</p> : null}
      </div>
      <div id="mobilePersistentChrome" className="hidden md:block">
        <div className="mb-6 grid grid-cols-4 gap-4">
          {DESKTOP_SLOTS.map((slot) => (
            <div key={slot.symbol} className="rounded-[16px] border border-border bg-card p-4">
              <p className="text-[11px] text-muted-foreground">{slot.market}</p>
              <p className={`mt-2 text-[18px] font-semibold tabular-nums ${quoteToneClass(quotes[slot.symbol])}`}>
                {slot.label} {formatBoardLast(quotes[slot.symbol], loading)}
              </p>
            </div>
          ))}
        </div>
        {error ? <p className="mb-4 text-[13px] text-buy">行情接口不可达，看板禁止显示假点位</p> : null}
      </div>
    </>
  );
}
