import { useEffect, useMemo, useState } from "react";
import { Card } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger } from "../components/ui/select";
import { fetchBoardQuotes, fetchKline } from "../lib/api";
import type { Candle } from "../lib/types";

const SIM_ASSETS = [
  { code: "BTCUSDT", name: "比特币" },
  { code: "600519.SH", name: "贵州茅台" },
  { code: "SA", name: "纯碱" },
  { code: "C", name: "玉米" },
] as const;

function atrFromCandles(candles: Candle[], window = 14): number | null {
  if (candles.length < window + 1) {
    return null;
  }
  let acc = 0;
  for (let i = candles.length - window; i < candles.length; i += 1) {
    const cur = candles[i];
    const prev = candles[i - 1];
    const tr = Math.max(cur.high - cur.low, Math.abs(cur.high - prev.close), Math.abs(cur.low - prev.close));
    if (!Number.isFinite(tr) || tr <= 0) {
      return null;
    }
    acc += tr;
  }
  const atr = acc / window;
  if (!Number.isFinite(atr) || atr <= 0) {
    return null;
  }
  return atr;
}

export function MultiAssetPage() {
  const [code, setCode] = useState("BTCUSDT");
  const [z, setZ] = useState(0.18);
  const [last, setLast] = useState<number | null>(null);
  const [atr, setAtr] = useState<number | null>(null);
  const [quoteStatus, setQuoteStatus] = useState("DATA_UNAVAILABLE");

  useEffect(() => {
    let cancelled = false;
    fetchBoardQuotes([code])
      .then((quoteRes) => {
        if (cancelled) {
          return;
        }
        const quote = quoteRes.quotes?.[0];
        if (quote?.available && quote.last != null && Number.isFinite(quote.last) && quote.last > 0) {
          setLast(quote.last);
          setQuoteStatus("OK");
          return;
        }
        setLast(null);
        setQuoteStatus("DATA_UNAVAILABLE");
      })
      .catch(() => {
        if (!cancelled) {
          setLast(null);
          setQuoteStatus("DATA_UNAVAILABLE");
        }
      });
    fetchKline(code, "D")
      .then((klineRes) => {
        if (!cancelled) {
          setAtr(atrFromCandles(klineRes.candles ?? []));
        }
      })
      .catch(() => {
        if (!cancelled) {
          setAtr(null);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [code]);

  const ready = last != null && atr != null;
  const band = useMemo(() => {
    if (!ready || last == null || atr == null) {
      return null;
    }
    return [last - atr * 1.6, last + atr * 1.6] as const;
  }, [ready, last, atr]);
  const simPx = ready && last != null && atr != null ? last + z * atr : null;

  return (
    <div className="space-y-4">
      <Card>
        <h2 className="text-[22px] font-semibold">全市场多资产自适应波动空间与临界状态突变中枢</h2>
        <p className="mt-2 font-mono text-[13px] text-muted-foreground">无量纲归一化 Z = (P - μ) / σ</p>
      </Card>
      <Card className="space-y-3">
        <h3 className="text-[18px] font-semibold">标的波动与订单审核模拟器</h3>
        <p className="text-[13px] text-muted-foreground">
          μ 来自看板最后行情，σ 来自真实日K的 ATR。缺 ATR 只禁用模拟滑条，禁止因日K失败把已接到的最新价清掉。
        </p>
        <label className="text-[13px]">选择测试标的</label>
        <Select value={code} onValueChange={setCode}>
          <SelectTrigger />
          <SelectContent>
            {SIM_ASSETS.map((a) => (
              <SelectItem key={a.code} value={a.code}>
                {a.name} ({a.code})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <p className="text-[13px] tabular-nums">
          最后行情 {last != null ? last.toFixed(2) : "DATA_UNAVAILABLE"} · {quoteStatus}
        </p>
        <p className="text-[13px] tabular-nums">
          ATR {atr != null ? atr.toFixed(2) : "DATA_UNAVAILABLE"}
        </p>
        <label className="text-[13px]" htmlFor="z">模拟偏离 σ</label>
        <Input
          id="z"
          type="range"
          min={-4}
          max={4}
          step={0.01}
          value={z}
          onChange={(e) => setZ(Number(e.target.value))}
          disabled={!ready}
        />
        <p className="tabular-nums text-[15px]">
          {simPx == null ? "DATA_UNAVAILABLE" : `${simPx.toFixed(2)} （Z=${z.toFixed(2)}）`}
        </p>
        <p className="text-[13px] text-muted-foreground">
          {band == null
            ? last != null
              ? "已有最新价，但缺真实日K ATR，禁止用死带宽画波动带。"
              : "无真实行情或无真实 ATR，禁止用死基准画波动带。"
            : `假设价在 [${band[0].toFixed(2)}, ${band[1].toFixed(2)}]；ATR 由日K真实波幅计算。`}
        </p>
      </Card>
    </div>
  );
}
