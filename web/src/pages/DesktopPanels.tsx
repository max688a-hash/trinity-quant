import { useEffect, useState } from "react";
import { Card } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { fetchForensicAutopsy, fetchScreener } from "../lib/api";
import type { AutopsyCase, ScreenerCandidate } from "../lib/types";

function fmtNum(value: number | null | undefined, digits = 2): string {
  if (value == null || !Number.isFinite(value)) {
    return "DATA_UNAVAILABLE";
  }
  return value.toFixed(digits);
}

export function ValuationPanel() {
  const [rows, setRows] = useState<ScreenerCandidate[]>([]);
  const [loadState, setLoadState] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    fetchScreener()
      .then((res) => {
        setRows((res.candidates ?? []).filter((item) => item.is_qualified));
        setLoadState("ready");
      })
      .catch(() => {
        setRows([]);
        setLoadState("error");
      });
  }, []);

  return (
    <Card className="overflow-x-auto">
      <h2 className="text-[22px] font-semibold">真值引力定价 V_G 与投资决策矩阵</h2>
      <p className="mt-1 text-[13px] text-muted-foreground">
        只读 /api/screener，与排毒屏同一真源。禁止本地表另写一套 V_G。
      </p>
      {loadState === "loading" ? (
        <p className="mt-3 text-[13px] text-muted-foreground">正在读取选股引擎引力…</p>
      ) : null}
      {loadState === "error" ? (
        <p className="mt-3 text-[15px] font-semibold text-buy">DATA_UNAVAILABLE。禁止用本地表冒充可买。</p>
      ) : null}
      {loadState === "ready" && rows.length === 0 ? (
        <p className="mt-3 text-[13px] text-muted-foreground">DATA_UNAVAILABLE。空池不可买。</p>
      ) : null}
      {loadState === "ready" && rows.length > 0 ? (
        <table className="mt-3 w-full text-left text-[13px] tabular-nums">
          <thead>
            <tr className="text-muted-foreground">
              <th className="py-2">标的</th>
              <th>Φ_CP</th>
              <th>Ω_Debt</th>
              <th>V_G</th>
              <th>α</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.symbol} className="border-t border-border">
                <td className="py-2">{row.name}</td>
                <td>{fmtNum(row.phi_cp)}</td>
                <td>{fmtNum(row.omega_debt)}</td>
                <td>{fmtNum(row.gravity_value, 1)}</td>
                <td>{fmtNum(row.alpha)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </Card>
  );
}

export function AutopsyPanel() {
  const [cases, setCases] = useState<AutopsyCase[]>([]);
  const [loadState, setLoadState] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    fetchForensicAutopsy()
      .then((res) => {
        if (res.status !== "OK") {
          setCases([]);
          setLoadState("error");
          return;
        }
        setCases((res.cases ?? []).filter((item) => !item.is_buyable && !item.is_admitted));
        setLoadState("ready");
      })
      .catch(() => {
        setCases([]);
        setLoadState("error");
      });
  }, []);

  return (
    <div className="space-y-3" data-testid="autopsy-forensic-pool">
      <div>
        <h2 className="text-[22px] font-semibold">法证尸检 · 引擎未准入否决</h2>
        <p className="mt-1 text-[13px] text-muted-foreground">
          只列 /api/pool/autopsy 中选股引擎未准入的否决样本。已准入标的不得再写成债务猝死。
        </p>
      </div>
      {loadState === "loading" ? (
        <p className="text-[13px] text-muted-foreground">正在读取法证否决档案…</p>
      ) : null}
      {loadState === "error" ? (
        <Card>
          <p className="text-[15px] font-semibold text-buy">尸检接口不可达</p>
          <p className="mt-2 text-[13px] text-buy">DATA_UNAVAILABLE。禁止用本地表冒充否决。</p>
        </Card>
      ) : null}
      {loadState === "ready" && cases.length === 0 ? (
        <Card>
          <p className="text-[15px] font-semibold">引擎未准入的法证否决样本为空</p>
          <p className="mt-2 text-[13px] text-muted-foreground">DATA_UNAVAILABLE。空池不可买。</p>
        </Card>
      ) : null}
      {loadState === "ready"
        ? cases.map((item) => (
            <Card key={item.symbol}>
              <h3 className="text-[18px] font-semibold">{item.name}</h3>
              <p className="mt-1 font-mono text-[11px] text-muted-foreground">
                {item.symbol} · {item.period_end_date || "DATA_UNAVAILABLE"}
              </p>
              <p className="mt-2 text-[13px] tabular-nums">
                Φ_CP {fmtNum(item.phi_cp)} · Ω_Debt {fmtNum(item.omega_debt)}
              </p>
              {item.veto_reasons.map((reason) => (
                <p key={reason} className="mt-2 text-[13px] text-buy">{reason}</p>
              ))}
            </Card>
          ))
        : null}
    </div>
  );
}

export function PitPanel() {
  return (
    <Card>
      <h2 className="text-[22px] font-semibold">Point-in-Time 时点防未来函数时间轴</h2>
      <p className="mt-2 text-[13px] text-muted-foreground">
        物理证明：系统在任意历史交易日截面，绝无法提前窃取尚未法定披露的财报数据。茅台 2026-06-30 报告期法定披露日 2026-08-28。
      </p>
    </Card>
  );
}

export function CalculatorPanel() {
  const [phi, setPhi] = useState(1.2);
  const [omega, setOmega] = useState(0.2);
  const veto = phi < 0.3 || omega > 1.2;
  return (
    <Card className="space-y-3">
      <h2 className="text-[22px] font-semibold">实盘指标动态测算沙盒</h2>
      <label className="text-[13px]">造血纯度 Φ_CP {phi.toFixed(2)} · 红线阈值: &lt; 0.30 立即一票否决</label>
      <Input type="range" min={-1} max={3} step={0.01} value={phi} onChange={(e) => setPhi(Number(e.target.value))} />
      <label className="text-[13px]">债务毒性 Ω_Debt {omega.toFixed(2)} · 红线阈值: &gt; 1.20 立即一票否决</label>
      <Input type="range" min={0} max={4} step={0.01} value={omega} onChange={(e) => setOmega(Number(e.target.value))} />
      <p className={veto ? "text-buy" : "text-sell"}>
        {veto ? "一票否决：造血或债务越线" : "造血纯净，债务覆盖充沛，具备第一性原理生存力"}
      </p>
    </Card>
  );
}
