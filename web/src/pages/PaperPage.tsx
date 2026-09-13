import { useEffect, useMemo, useState } from "react";
import { Button } from "../components/ui/button";
import { Card } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger } from "../components/ui/select";
import { fetchBoardQuotes, fetchPaperState, fetchPoolDockets, fetchScreener, postPaperTrade } from "../lib/api";
import { toListedSymbol } from "../lib/listedSymbol";
import { scrollToPaperSection } from "../lib/viewport";
import type { AdmissionDocket, PaperState, ScreenerCandidate } from "../lib/types";

export function PaperPage() {
  const [state, setState] = useState<PaperState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [side, setSide] = useState<"BUY" | "SELL">("BUY");
  const [msg, setMsg] = useState<string>("");
  const [qty, setQty] = useState("100");
  const [pool, setPool] = useState<ScreenerCandidate[]>([]);
  const [poolState, setPoolState] = useState<"loading" | "ready" | "error">("loading");
  const [symbol, setSymbol] = useState("");
  const [last, setLast] = useState<number | null>(null);
  const [quoteStatus, setQuoteStatus] = useState("DATA_UNAVAILABLE");
  const [dockets, setDockets] = useState<AdmissionDocket[]>([]);

  const vetoRoots = useMemo(
    () => new Set(
      dockets
        .filter((row) => !row.is_buyable_now)
        .map((row) => row.symbol.split(".")[0].toUpperCase()),
    ),
    [dockets],
  );
  const qualified = useMemo(
    () => pool.filter((row) => row.is_qualified && !vetoRoots.has(row.symbol.split(".")[0].toUpperCase())),
    [pool, vetoRoots],
  );
  const listed = symbol ? toListedSymbol(symbol) : "";

  useEffect(() => {
    if (symbol || qualified.length === 0) {
      return;
    }
    setSymbol(qualified[0].symbol);
  }, [symbol, qualified]);

  useEffect(() => {
    fetchPaperState()
      .then(setState)
      .catch((err: Error) => setError(err.message));
    fetchPoolDockets()
      .then(setDockets)
      .catch(() => setDockets([]));
    fetchScreener()
      .then((res) => {
        const rows = res.candidates ?? [];
        setPool(rows);
        setPoolState("ready");
      })
      .catch(() => {
        setPool([]);
        setPoolState("error");
      });
  }, []);

  useEffect(() => {
    if (!listed) {
      setLast(null);
      setQuoteStatus("DATA_UNAVAILABLE");
      return;
    }
    let cancelled = false;
    fetchBoardQuotes([listed])
      .then((res) => {
        if (cancelled) {
          return;
        }
        const quote = (res.quotes ?? []).find((row) => row.symbol === listed) ?? res.quotes?.[0];
        if (quote?.available && quote.last != null && Number.isFinite(quote.last) && quote.last > 0) {
          setLast(quote.last);
          setQuoteStatus("OK");
          return;
        }
        setLast(null);
        setQuoteStatus("DATA_UNAVAILABLE");
      })
      .catch(() => {
        if (cancelled) {
          return;
        }
        setLast(null);
        setQuoteStatus("DATA_UNAVAILABLE");
      });
    return () => {
      cancelled = true;
    };
  }, [listed]);

  const [isReplayMode, setIsReplayMode] = useState(false);

  async function submit() {
    const quantity = Number(qty);
    if (!listed || last == null || !Number.isFinite(quantity) || quantity <= 0) {
      setMsg("DATA_UNAVAILABLE。禁止默用 1550，无行情价不得成交。");
      return;
    }
    try {
      const res = await postPaperTrade({
        symbol: listed,
        action: side,
        quantity,
        price: last,
        is_replay_mode: isReplayMode,
      });
      setMsg(res.success ? `成交，摩擦 ${res.friction_total}` : res.rejection_reason || "被风控拦截");
      setState(await fetchPaperState());
    } catch (err) {
      setMsg(err instanceof Error ? err.message : "报单失败");
    }
  }

  const canSubmit = Boolean(listed && last != null && Number(qty) > 0);

  return (
    <div className="space-y-4">
      <div className="flex gap-2 overflow-x-auto">
        <Button variant="secondary" onClick={() => scrollToPaperSection("sec-paper-sim")}>模拟海龟</Button>
        <Button variant="secondary" onClick={() => scrollToPaperSection("sec-paper-combat")}>真金实战</Button>
        <Button variant="secondary" onClick={() => scrollToPaperSection("sec-paper-daemon")}>影子巡航</Button>
        <Button variant="secondary" onClick={() => scrollToPaperSection("sec-paper-stress")}>黑天鹅压测</Button>
      </div>
      {error ? <p className="text-[13px] text-buy">{error}</p> : null}
      {!state && !error ? <p className="text-[13px] text-muted-foreground">读取模拟盘资金…</p> : null}
      <section id="sec-paper-sim" className="space-y-3">
        <Card>
          <p className="text-[13px] text-muted-foreground">可用现金</p>
          <p className="text-[22px] font-semibold tabular-nums">¥{state ? state.cash.toLocaleString("zh-CN") : "—"}</p>
          <p className="mt-2 text-[13px] text-muted-foreground">总权益</p>
          <p className="text-[18px] font-medium tabular-nums">¥{state ? state.equity.toLocaleString("zh-CN") : "—"}</p>
          <p className="mt-2 text-[13px] text-muted-foreground">最大回撤</p>
          <p className="text-[15px] tabular-nums">{state ? `${(state.max_drawdown * 100).toFixed(2)}%` : "—"}</p>
          <p className="mt-2 text-[13px]">T+1 锁仓 {state?.t_plus_1_enforced ? "已启用" : "未知"} · 单向棘轮 {state?.ratchet_enabled ? "已启用" : "未知"}</p>
          <p className="mt-3 text-[13px] text-muted-foreground">
            纸上成交按最后行情价计提印花税、佣金、滑点。权益变红变绿是账本结果，禁止为绿而放宽风控。纸上亏，真金更不能当成已经会赚。
          </p>
        </Card>
      </section>
      <section id="sec-paper-combat" className="space-y-3">
        <Card className="space-y-3">
          <label className="text-[13px]" htmlFor="paper-symbol">准入标的</label>
          {poolState === "loading" ? (
            <p className="text-[13px] text-muted-foreground">正在读取 /api/screener…</p>
          ) : null}
          {poolState === "error" ? (
            <p className="text-[13px] text-buy">DATA_UNAVAILABLE。选股接口不可达，禁止成交。</p>
          ) : null}
          {poolState === "ready" && qualified.length === 0 ? (
            <p className="text-[13px] text-buy">DATA_UNAVAILABLE。洁净池为空，禁止纸上买入。</p>
          ) : null}
          {poolState === "ready" && qualified.length > 0 ? (
            <Select value={symbol} onValueChange={setSymbol}>
              <SelectTrigger id="paper-symbol" />
              <SelectContent>
                {qualified.map((row) => (
                  <SelectItem key={row.symbol} value={row.symbol}>
                    {row.name} {toListedSymbol(row.symbol)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : null}
          <p className="text-[13px] tabular-nums">
            最后行情价 {last != null ? last.toFixed(2) : "DATA_UNAVAILABLE"} · {quoteStatus}
          </p>
          <label className="text-[13px]" htmlFor="side">交易方向</label>
          <Select value={side} onValueChange={(v) => setSide(v as "BUY" | "SELL")}>
            <SelectTrigger id="side" />
            <SelectContent>
              <SelectItem value="BUY">🔴 买入 (BUY / 做多)</SelectItem>
              <SelectItem value="SELL">🟢 卖出 (SELL / 平多)</SelectItem>
            </SelectContent>
          </Select>
          <label className="text-[13px]" htmlFor="qty">数量</label>
          <Input id="qty" value={qty} onChange={(ev) => setQty(ev.target.value)} type="number" min={1} />
          <label className="flex items-center gap-2 text-[12px] text-muted-foreground select-none cursor-pointer" htmlFor="paper-replay">
            <input
              id="paper-replay"
              type="checkbox"
              checked={isReplayMode}
              onChange={(ev) => setIsReplayMode(ev.target.checked)}
              className="rounded border-slate-700 bg-slate-900 text-rose-500 focus:ring-0"
            />
            <span>历史回放测试（休市默认禁止成交，勾选后才允许纸上练习）</span>
          </label>
          <Button variant={side === "BUY" ? "buy" : "sell"} disabled={!canSubmit} onClick={() => void submit()}>
            提交纸上工单
          </Button>
          {msg ? <p className="text-[13px]">{msg}</p> : null}
        </Card>
      </section>
      <section id="sec-paper-daemon">
        <Card>
          <h3 className="text-[18px] font-semibold">影子巡航</h3>
          <p className="mt-2 text-[13px] text-muted-foreground">系统自主学习实验室：逐笔复盘归因，不是手动买卖游戏。</p>
        </Card>
      </section>
      <section id="sec-paper-stress">
        <Card>
          <h3 className="text-[18px] font-semibold">黑天鹅压测</h3>
          <p className="mt-2 text-[13px] text-muted-foreground">2008 / 2015 / 2020 情景已在后端压力矩阵落地，前端只展示受控回撤。</p>
        </Card>
      </section>
    </div>
  );
}
