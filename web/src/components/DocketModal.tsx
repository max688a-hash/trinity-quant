import { useEffect, useState } from "react";
import { ADMISSION_DOCKETS } from "../lib/dockets";
import { Button } from "./ui/button";
import { Dialog, DialogContent, bindModalCloser, closeModal } from "./ui/dialog";

export function openAdmissionDocketModal(sym = "600519.SH"): void {
  window.dispatchEvent(new CustomEvent("open-docket", { detail: sym }));
}

export function DocketModal() {
  const [open, setOpen] = useState(false);
  const [sym, setSym] = useState("600519.SH");
  const docket = ADMISSION_DOCKETS[sym];

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

  return (
    <div id="admissionDocketModal" className={open ? "" : "hidden"}>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent title={docket ? `${docket.name} 入池法证` : "入池档案"}>
          {docket ? (
            <div className="mt-3 space-y-2 text-[13px]">
              <p>评级 {docket.grade} · {docket.horizon}</p>
              <p>Φ_CP {docket.blood_purity} · Ω_Debt {docket.debt_toxicity}</p>
              <p>{docket.current_action_advice}</p>
              <Button variant="secondary" onClick={closeModal}>关闭深研档案</Button>
            </div>
          ) : (
            <p>未找到宗卷</p>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
