import { useEffect, useRef, useState } from "react";
import { MARKET_SECTORS } from "../lib/markets";
import { fetchBoardQuotes } from "../lib/api";
import { formatBoardLast, quotesBySymbol } from "../lib/boardQuotes";
import { loadRealKlineData } from "../lib/klineSignals";
import { registerKlineDrawer } from "../lib/viewport";
import { openAdmissionDocketModal } from "./DocketModal";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { Checkbox } from "./ui/checkbox";
import type { BoardQuote, Candle } from "../lib/types";

const TFS = ["D", "1H", "15M", "5M", "Tick"] as const;
const TF_LABEL: Record<string, string> = {
  D: "日线 (D)",
  "1H": "1小时 (1H)",
  "15M": "15分 (15M)",
  "5M": "5分 (5M)",
  Tick: "分时 (Tick)",
};

export function switchMarketSector(sector: string): void {
  const el = document.getElementById(`sector-${sector}`);
  if (el) {
    el.classList.add("ring-cyan-400", "ring-2");
    el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

const SECTOR_JUMP = {
  ashare: () => switchMarketSector('ashare'),
  futures: () => switchMarketSector('futures'),
  hkstock: () => switchMarketSector('hkstock'),
  usstock: () => switchMarketSector('usstock'),
  forex: () => switchMarketSector('forex'),
  crypto: () => switchMarketSector('crypto'),
} as const;

export function KlineChart() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [sector, setSector] = useState<keyof typeof MARKET_SECTORS>("ashare");
  const [symbol, setSymbol] = useState("600519.SH");
  const [tf, setTf] = useState<(typeof TFS)[number]>("D");
  const [candles, setCandles] = useState<Candle[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [boardQuotes, setBoardQuotes] = useState<Record<string, BoardQuote>>({});
  const [boardLoading, setBoardLoading] = useState(true);
  const candlesRef = useRef<Candle[]>([]);
  const tooltipDismissTimer = useRef<number | null>(null);
  let touchStartX = 0;
  let touchStartY = 0;


  useEffect(() => {
    let cancelled = false;
    const codes = MARKET_SECTORS[sector].benchmarks.map((bm) => bm.code);
    setBoardLoading(true);
    fetchBoardQuotes(codes)
      .then((res) => {
        if (!cancelled) {
          setBoardQuotes(quotesBySymbol(res.quotes));
        }
      })
      .catch(() => {
        if (!cancelled) {
          setBoardQuotes({});
        }
      })
      .finally(() => {
        if (!cancelled) {
          setBoardLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [sector]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    loadRealKlineData(tf, symbol)
      .then((rows) => {
        if (!cancelled) {
          candlesRef.current = rows;
          setCandles(rows);
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
  }, [symbol, tf]);

  useEffect(() => {
    const drawKlineChart = () => {
      const canvas = canvasRef.current;
      if (!canvas) {
        return;
      }
      const rect = canvas.getBoundingClientRect();
      if (rect.width <= 0) {
        return;
      }
      const dpr = window.devicePixelRatio || 1;
      canvas.width = Math.floor(rect.width * dpr);
      canvas.height = Math.floor(360 * dpr);
      const ctx = canvas.getContext("2d");
      if (!ctx) {
        return;
      }
      ctx.scale(dpr, dpr);
      const rows = candlesRef.current;
      ctx.fillStyle = "#121a24";
      ctx.fillRect(0, 0, rect.width, 360);
      if (rows.length < 2) {
        ctx.fillStyle = "#9fb0c0";
        ctx.fillText("暂无K线", 16, 24);
        return;
      }
      const highs = rows.map((c) => c.high);
      const lows = rows.map((c) => c.low);
      const maxH = Math.max(...highs);
      const minL = Math.min(...lows);
      const span = Math.max(0.01, maxH - minL);
      const w = rect.width / rows.length;
      rows.forEach((c, i) => {
        const x = i * w + w * 0.2;
        const yHigh = 20 + ((maxH - c.high) / span) * 300;
        const yLow = 20 + ((maxH - c.low) / span) * 300;
        const yO = 20 + ((maxH - c.open) / span) * 300;
        const yC = 20 + ((maxH - c.close) / span) * 300;
        const up = c.close >= c.open;
        ctx.strokeStyle = up ? "#be4a40" : "#2f9a6c";
        ctx.fillStyle = up ? "#be4a40" : "#2f9a6c";
        ctx.beginPath();
        ctx.moveTo(x + w * 0.3, yHigh);
        ctx.lineTo(x + w * 0.3, yLow);
        ctx.stroke();
        const top = Math.min(yO, yC);
        const h = Math.max(1, Math.abs(yC - yO));
        ctx.fillRect(x, top, w * 0.6, h);
        if (c.signal) {
          ctx.fillStyle = c.signal.color;
          ctx.fillText(c.signal.text, x, top - 6);
        }
      });
    };
    registerKlineDrawer(drawKlineChart);
    requestAnimationFrame(drawKlineChart);
  }, [candles]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) {
      return;
    }
    const onStart = (e: TouchEvent) => {
      if (tooltipDismissTimer.current) {
        window.clearTimeout(tooltipDismissTimer.current);
      }
      if (e.touches.length === 1) {
        touchStartX = e.touches[0].clientX;
        touchStartY = e.touches[0].clientY;
      }
    };
    const onMove = (e: TouchEvent) => {
      if (e.touches.length !== 1) {
        return;
      }
      const curX = e.touches[0].clientX;
      const curY = e.touches[0].clientY;
      const deltaY = curY - touchStartY;
      if (Math.abs(deltaY) > Math.abs(curX - touchStartX) && Math.abs(deltaY) > 8) {
        return;
      }
      e.preventDefault();
    };
    const onEnd = () => {
      if (tooltipDismissTimer.current) {
        window.clearTimeout(tooltipDismissTimer.current);
      }
      tooltipDismissTimer.current = window.setTimeout(() => {
        const tip = document.getElementById("klineTooltip");
        if (tip) {
          tip.classList.add("hidden");
        }
      }, 2500);
    };
    canvas.addEventListener("touchstart", onStart, { passive: false });
    canvas.addEventListener("touchmove", onMove, { passive: false });
    canvas.addEventListener("touchend", onEnd);
    return () => {
      canvas.removeEventListener("touchstart", onStart);
      canvas.removeEventListener("touchmove", onMove);
      canvas.removeEventListener("touchend", onEnd);
    };
  }, []);

  const meta = MARKET_SECTORS[sector];
  const last = candles[candles.length - 1];

  return (
    <div className="space-y-4">
      <div className="flex gap-2 overflow-x-auto no-scrollbar">
        {(Object.keys(MARKET_SECTORS) as Array<keyof typeof MARKET_SECTORS>).map((key) => (
          <Button
            key={key}
            id={`sector-${key}`}
            variant={sector === key ? "default" : "secondary"}
            className="shrink-0"
            onClick={() => {
              setSector(key);
              SECTOR_JUMP[key]();
              const first = MARKET_SECTORS[key].assets[0];
              if (first) {
                setSymbol(first.code);
              }
            }}
          >
            {MARKET_SECTORS[key].name}
          </Button>
        ))}
      </div>
      <Card>
        <div className="flex flex-wrap gap-2">
          {meta.benchmarks.map((bm) => (
            <Button
              key={bm.code}
              type="button"
              variant="secondary"
              className="shrink-0"
              onClick={() => setSymbol(bm.code)}
            >
              {bm.name} {formatBoardLast(boardQuotes[bm.code], boardLoading)}
            </Button>
          ))}
        </div>
        <div className="mt-3 flex gap-2 overflow-x-auto">
          {meta.assets.map((asset) => (
            <Button
              key={asset.code}
              type="button"
              variant="secondary"
              className="shrink-0"
              onClick={() => {
                setSymbol(asset.code);
                document.getElementById("tickerMicroSpecBar")?.scrollIntoView({ behavior: 'smooth', block: 'start' });
              }}
            >
              {asset.name} {asset.code} {asset.tag}
            </Button>
          ))}
        </div>
      </Card>
      <Card id="klineTopTickerBar">
        <div className="flex flex-wrap items-center gap-2 text-[13px]">
          <span id="tickerSymbolTag" className="font-semibold tabular-nums">
            {symbol}
          </span>
          <span id="tickerChangeTag" className={last && last.close >= last.open ? "text-buy" : "text-sell"}>
            {last ? last.close.toFixed(2) : "—"}
          </span>
          <Button variant="secondary" onClick={() => openAdmissionDocketModal(symbol)}>
            入池深研依据
          </Button>
        </div>
        <div id="tickerMicroSpecBar" className="mt-2 text-[11px] text-muted-foreground">
          {meta.assets.find((a) => a.code === symbol)?.rule ?? "自然人客户禁止进入交割月"}
        </div>
      </Card>
      <div className="flex flex-wrap gap-2">
        {TFS.map((item) => (
          <Button key={item} variant={tf === item ? "default" : "secondary"} onClick={() => setTf(item)}>
            {TF_LABEL[item]}
          </Button>
        ))}
      </div>
      <div className="flex gap-3 text-[13px] text-muted-foreground">
        <label className="flex items-center gap-1"><Checkbox defaultChecked /> MA5</label>
        <label className="flex items-center gap-1"><Checkbox defaultChecked /> MA10</label>
        <label className="flex items-center gap-1"><Checkbox defaultChecked /> MA20</label>
        <label className="flex items-center gap-1"><Checkbox defaultChecked /> MA60</label>
      </div>
      {loading ? <p className="text-[13px] text-muted-foreground">正在拉取交易所历史K线…</p> : null}
      {error ? <p className="text-[13px] text-buy">{error}</p> : null}
      <div id="klineCanvasWrapper" className="overflow-hidden rounded-[16px] border border-border">
        <canvas id="klineCanvas" ref={canvasRef} className="h-[360px] w-full" />
      </div>
      <div id="klineTooltip" className="hidden text-[11px]" />
    </div>
  );
}
