import { useEffect, useState } from "react";
import { Button } from "../components/ui/button";
import { Card } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger } from "../components/ui/select";
import { fetchPaperState, postPaperTrade } from "../lib/api";
import { scrollToPaperSection } from "../lib/viewport";
import type { PaperState } from "../lib/types";

export function PaperPage() {
  const [state, setState] = useState<PaperState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [side, setSide] = useState<"BUY" | "SELL">("BUY");
  const [msg, setMsg] = useState<string>("");

  useEffect(() => {
    fetchPaperState()
      .then(setState)
      .catch((err: Error) => setError(err.message));
  }, []);

  async function submit() {
    try {
      const res = await postPaperTrade({
        symbol: "600519.SH",
        action: side,
        quantity: 100,
        price: 1550,
        is_replay_mode: true,
      });
      setMsg(res.success ? `成交，摩擦 ${res.friction_total}` : res.rejection_reason || "被风控拦截");
      setState(await fetchPaperState());
    } catch (err) {
      setMsg(err instanceof Error ? err.message : "报单失败");
    }
  }

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
          <p className="mt-2 text-[13px]">T+1 锁仓 {state?.t_plus_1_enforced ? "已启用" : "未知"} · 单向棘轮 {state?.ratchet_enabled ? "已启用" : "未知"}</p>
        </Card>
      </section>
      <section id="sec-paper-combat" className="space-y-3">
        <Card className="space-y-3">
          <label className="text-[13px]" htmlFor="side">交易方向</label>
          <Select value={side} onValueChange={(v) => setSide(v as "BUY" | "SELL")}>
            <SelectTrigger id="side" />
            <SelectContent>
              <SelectItem value="BUY">🔴 买入 (BUY / 做多)</SelectItem>
              <SelectItem value="SELL">🟢 卖出 (SELL / 平多)</SelectItem>
            </SelectContent>
          </Select>
          <label className="text-[13px]" htmlFor="qty">数量</label>
          <Input id="qty" defaultValue={100} type="number" />
          <Button variant={side === "BUY" ? "buy" : "sell"} onClick={() => void submit()}>
            提交实战报单
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
