import { useEffect, useState } from "react";
import { fetchPoolDockets } from "../lib/api";
import type { AdmissionDocket } from "../lib/types";
import { Button } from "./ui/button";
import { Dialog, DialogContent, bindModalCloser, closeModal } from "./ui/dialog";

export function openAdmissionDocketModal(sym = "600519.SH"): void {
  window.dispatchEvent(new CustomEvent("open-docket", { detail: sym }));
}

function rootOf(symbol: string): string {
  return symbol.split(".")[0].toUpperCase();
}

export function DocketModal() {
  const [open, setOpen] = useState(false);
  const [sym, setSym] = useState("600519.SH");
  const [docket, setDocket] = useState<AdmissionDocket | null>(null);
  const [loadState, setLoadState] = useState<"idle" | "loading" | "ready" | "error">("idle");

  useEffect(() => {
    const unbind = bindModalCloser(() => setOpen(false));
    const handler = (ev: Event) => {
      const ce = ev as CustomEvent<string>;
      setSym(ce.detail || "600519.SH");
      setOpen(true);
    };
    window.addEventListener("open-docket", handler);
    return () => {
      unbind();
      window.removeEventListener("open-docket", handler);
    };
  }, []);

  useEffect(() => {
    if (!open) {
      return;
    }
    let cancelled = false;
    setLoadState("loading");
    fetchPoolDockets()
      .then((rows) => {
        if (cancelled) {
          return;
        }
        const hit =
          rows.find((row) => row.symbol === sym) ||
          rows.find((row) => rootOf(row.symbol) === rootOf(sym)) ||
          null;
        setDocket(hit);
        setLoadState("ready");
      })
      .catch(() => {
        if (cancelled) {
          return;
        }
        setDocket(null);
        setLoadState("error");
      });
    return () => {
      cancelled = true;
    };
  }, [open, sym]);

  return (
    <div id="admissionDocketModal" className={open ? "" : "hidden"}>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent title={docket ? `${docket.name} 入池法证` : "入池档案"}>
          {loadState === "loading" ? (
            <p className="mt-3 text-[13px] text-muted-foreground">正在读取 /api/pool/dockets…</p>
          ) : null}
          {loadState === "error" ? (
            <p className="mt-3 text-[13px] text-buy">DATA_UNAVAILABLE。禁止用本地可买表冒充宗卷。</p>
          ) : null}
          {loadState === "ready" && docket ? (
            <div className="mt-3 space-y-2 text-[13px]">
              <p>评级 {docket.grade} · {docket.horizon}</p>
              <p>Φ_CP {docket.blood_purity} · Ω_Debt {docket.debt_toxicity}</p>
              <p>{docket.current_action_advice}</p>
              {docket.is_buyable_now ? null : (
                <p className="text-buy">法证否决，禁止当作可买，禁止手打。</p>
              )}
              <Button variant="secondary" onClick={closeModal}>关闭深研档案</Button>
            </div>
          ) : null}
          {loadState === "ready" && !docket ? (
            <p className="mt-3 text-[13px] text-muted-foreground">未找到宗卷</p>
          ) : null}
        </DialogContent>
      </Dialog>
    </div>
  );
}
