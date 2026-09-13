import { useEffect, useState } from "react";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card } from "../components/ui/card";
import { Dialog, DialogContent, bindModalCloser, closeModal } from "../components/ui/dialog";
import { STOCKS } from "../lib/stocks";
import { fetchScreener } from "../lib/api";
import type { ScreenerCandidate } from "../lib/types";

export function ScreenerPage() {
  const [filter, setFilter] = useState<"all" | "admitted" | "vetoed">("all");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState<(typeof STOCKS)[0] | null>(null);
  const [remote, setRemote] = useState<ScreenerCandidate[] | null>(null);
  const [loadState, setLoadState] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    const unbind = bindModalCloser(() => setOpen(false));
    fetchScreener()
      .then((res) => {
        setRemote(res.candidates);
        setLoadState("ready");
      })
      .catch(() => setLoadState("error"));
    return () => {
      unbind();
    };
  }, []);

  const rows = STOCKS.filter((s) => {
    if (filter === "admitted") return s.is_admitted;
    if (filter === "vetoed") return !s.is_admitted;
    return true;
  });

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        <Button variant={filter === "all" ? "default" : "secondary"} onClick={() => setFilter("all")}>
          全部标的 ({STOCKS.length})
        </Button>
        <Button variant={filter === "admitted" ? "default" : "secondary"} onClick={() => setFilter("admitted")}>
          洁净准入 ({STOCKS.filter((s) => s.is_admitted).length})
        </Button>
        <Button variant={filter === "vetoed" ? "sell" : "secondary"} onClick={() => setFilter("vetoed")}>
          一票否决 ({STOCKS.filter((s) => !s.is_admitted).length})
        </Button>
      </div>
      {loadState === "loading" ? <p className="text-[13px] text-muted-foreground">正在穿透财报选股…</p> : null}
      {loadState === "error" ? (
        <p className="text-[13px] text-buy">选股接口暂时不可达，下方展示已审计本地法证池。</p>
      ) : null}
      <div id="stockCardContainer" className="grid gap-3">
        {rows.map((stock) => (
          <Card
            key={stock.symbol}
            className="cursor-pointer"
            onClick={() => {
              setActive(stock);
              setOpen(true);
            }}
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-[15px] font-semibold">{stock.name}</p>
                <p className="font-mono text-[11px] text-muted-foreground">{stock.symbol}</p>
              </div>
              <Badge tone={stock.is_admitted ? "admit" : "veto"}>
                {stock.is_admitted ? "洁净准入" : "一票否决"}
              </Badge>
            </div>
            <div className="mt-3 grid grid-cols-2 gap-2 text-[13px] tabular-nums">
              <div>
                <p className="text-muted-foreground">造血纯度 Φ_CP</p>
                <p className={stock.phi_cp >= 0.3 ? "text-sell" : "text-buy"}>{stock.phi_cp.toFixed(2)}</p>
              </div>
              <div>
                <p className="text-muted-foreground">债务毒性 Ω_Debt</p>
                <p className={stock.omega_debt <= 1.2 ? "text-sell" : "text-buy"}>{stock.omega_debt.toFixed(2)}</p>
              </div>
            </div>
          </Card>
        ))}
      </div>
      {remote && remote.length > 0 ? (
        <p className="text-[11px] text-muted-foreground">引擎另返回 {remote.length} 条动态候选。</p>
      ) : null}
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent title={active ? `${active.name} ${active.symbol}` : "详情"}>
          {active ? (
            <div className="mt-3 space-y-2 text-[13px]">
              <p>报告期 {active.latest_period} · 法定披露日 {active.disclosure_date} (PIT)</p>
              <p>营收 {active.revenue} 亿 · 经营现金流 {active.ocf} 亿</p>
              {active.veto_reasons.map((r) => (
                <p key={r} className="text-buy">{r}</p>
              ))}
              <Button variant="secondary" onClick={closeModal}>关闭</Button>
            </div>
          ) : null}
        </DialogContent>
      </Dialog>
    </div>
  );
}
