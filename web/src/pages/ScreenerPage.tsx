import { useEffect, useMemo, useState } from "react";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card } from "../components/ui/card";
import { Dialog, DialogContent, bindModalCloser, closeModal } from "../components/ui/dialog";
import { fetchScreener } from "../lib/api";
import type { ScreenerCandidate } from "../lib/types";

export function ScreenerPage() {
  const [filter, setFilter] = useState<"all" | "admitted" | "vetoed">("all");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState<ScreenerCandidate | null>(null);
  const [pool, setPool] = useState<ScreenerCandidate[]>([]);
  const [loadState, setLoadState] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    const unbind = bindModalCloser(() => setOpen(false));
    fetchScreener()
      .then((res) => {
        setPool(res.candidates ?? []);
        setLoadState("ready");
      })
      .catch(() => {
        setPool([]);
        setLoadState("error");
      });
    return () => {
      unbind();
    };
  }, []);

  const admitted = useMemo(() => pool.filter((s) => s.is_qualified), [pool]);
  const vetoed = useMemo(() => pool.filter((s) => !s.is_qualified), [pool]);
  const visible = filter === "admitted" ? admitted : filter === "vetoed" ? vetoed : pool;
  const blocked = loadState !== "ready";

  return (
    <div className="space-y-3" data-testid="screener-engine-pool">
      <div>
        <h2 className="text-[22px] font-semibold tracking-[-0.01em]">排毒选股 · 引擎真值池</h2>
        <p className="mt-1 text-[13px] text-muted-foreground">
          只展示 /api/screener 穿透结果。本地静态表不得当作可买。
        </p>
      </div>
      <div className="flex flex-wrap gap-2">
        <Button variant={filter === "all" ? "default" : "secondary"} onClick={() => setFilter("all")}>
          全部标的 ({blocked ? "—" : pool.length})
        </Button>
        <Button variant={filter === "admitted" ? "default" : "secondary"} onClick={() => setFilter("admitted")}>
          洁净准入 ({blocked ? "—" : admitted.length})
        </Button>
        <Button variant={filter === "vetoed" ? "sell" : "secondary"} onClick={() => setFilter("vetoed")}>
          一票否决 ({blocked ? "—" : vetoed.length})
        </Button>
      </div>
      {loadState === "loading" ? (
        <p className="text-[13px] text-muted-foreground">正在穿透财报选股…</p>
      ) : null}
      {loadState === "error" ? (
        <Card>
          <p className="text-[15px] font-semibold text-buy">选股接口不可达</p>
          <p className="mt-2 text-[13px] text-buy">DATA_UNAVAILABLE。禁止用本地表冒充可买。</p>
        </Card>
      ) : null}
      {loadState === "ready" && visible.length === 0 ? (
        <Card>
          <p className="text-[15px] font-semibold">引擎未返回该筛选项下的标的</p>
          <p className="mt-2 text-[13px] text-muted-foreground">DATA_UNAVAILABLE。空池不可买。</p>
        </Card>
      ) : null}
      <div id="stockCardContainer" className="grid gap-3">
        {loadState === "ready"
          ? visible.map((stock) => (
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
                  <Badge tone={stock.is_qualified ? "admit" : "veto"}>
                    {stock.is_qualified ? "洁净准入" : "一票否决"}
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
            ))
          : null}
      </div>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent title={active ? `${active.name} ${active.symbol}` : "入池深研"}>
          {active ? (
            <div className="mt-3 space-y-2 text-[13px]">
              <p>Φ_CP {active.phi_cp.toFixed(2)} · Ω_Debt {active.omega_debt.toFixed(2)} · α {active.alpha.toFixed(2)}</p>
              <p>{active.dossier.core_business}</p>
              <p className="text-muted-foreground">{active.dossier.seasonality_profile}</p>
              <p>{active.dossier.recommended_action}</p>
              {!active.is_qualified ? (
                <p className="text-buy">一票否决，禁止当作可买。</p>
              ) : null}
              <Button variant="secondary" onClick={closeModal}>关闭</Button>
            </div>
          ) : null}
        </DialogContent>
      </Dialog>
    </div>
  );
}
