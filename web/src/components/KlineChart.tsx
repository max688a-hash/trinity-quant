import { useEffect, useRef, useState } from "react";
import { MARKET_SECTORS } from "../lib/markets";
import { fetchBoardQuotes } from "../lib/api";
import { formatBoardLast, quotesBySymbol } from "../lib/boardQuotes";
import { listedKlineSignals, loadRealKlineData } from "../lib/klineSignals";
import { paintKline, type KlineOverlays } from "../lib/klineCanvasDraw";
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
  const [ma5, setMa5] = useState(true);
  const [ma10, setMa10] = useState(true);
  const [ma20, setMa20] = useState(true);
  const [ma60, setMa60] = useState(true);
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
    candlesRef.current = [];
    setCandles([]);
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
      const overlays: KlineOverlays = { ma5, ma10, ma20, ma60 };
      paintKline(ctx, candlesRef.current, rect.width, 360, overlays);
    };
    registerKlineDrawer(drawKlineChart);
    requestAnimationFrame(drawKlineChart);
  }, [candles, ma5, ma10, ma20, ma60]);

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
            {last ? last.close.toFixed(2) : "DATA_UNAVAILABLE"}
          </span>
          <Button variant="secondary" onClick={() => openAdmissionDocketModal(symbol)}>
            入池深研依据
          </Button>
        </div>
        <div id="tickerMicroSpecBar" className="mt-2 text-[11px] text-muted-foreground">
          {meta.assets.find((a) => a.code === symbol)?.rule ?? "自然人客户禁止进入交割月"}
        </div>
        <p className="mt-2 text-[13px] text-muted-foreground">
          多空来自真实日K的放量通道突破；有持仓则必须增仓。不是入池与纸上成交依据，分钟线源未通则 DATA_UNAVAILABLE。
        </p>
      </Card>
      <div className="flex flex-wrap gap-2">
        {TFS.map((item) => (
          <Button key={item} variant={tf === item ? "default" : "secondary"} onClick={() => setTf(item)}>
            {TF_LABEL[item]}
          </Button>
        ))}
      </div>
      <div className="flex gap-3 text-[13px] text-muted-foreground">
        <label className="flex items-center gap-1">
          <Checkbox checked={ma5} onCheckedChange={(v) => setMa5(v === true)} /> MA5
        </label>
        <label className="flex items-center gap-1">
          <Checkbox checked={ma10} onCheckedChange={(v) => setMa10(v === true)} /> MA10
        </label>
        <label className="flex items-center gap-1">
          <Checkbox checked={ma20} onCheckedChange={(v) => setMa20(v === true)} /> MA20
        </label>
        <label className="flex items-center gap-1">
          <Checkbox checked={ma60} onCheckedChange={(v) => setMa60(v === true)} /> MA60
        </label>
      </div>
      {loading ? <p className="text-[13px] text-muted-foreground">正在拉取交易所历史K线…</p> : null}
      {error ? <p className="text-[13px] text-buy">{error}</p> : null}
      <div id="klineCanvasWrapper" className="overflow-hidden rounded-[16px] border border-border">
        <canvas id="klineCanvas" ref={canvasRef} className="h-[360px] w-full" />
      </div>
      <div id="klineSignalList" className="space-y-1 text-[13px]">
        <p className="text-muted-foreground">最近多空（画布外，不挡蜡烛）</p>
        {listedKlineSignals(candles).length === 0 && !loading ? (
          <p>无放量增仓突破，禁止把均线当进场</p>
        ) : (
          listedKlineSignals(candles).map((row) => (
            <p key={`${row.date}-${row.signal?.type}`} className={row.signal?.type === 'BUY' ? "text-buy" : "text-sell"}>
              {row.date} {row.signal?.text}
            </p>
          ))
        )}
      </div>
      <div id="klineTooltip" className="hidden text-[11px]" />
    </div>
  );
}
