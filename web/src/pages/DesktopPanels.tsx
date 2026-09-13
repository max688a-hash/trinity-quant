import { useState } from "react";
import { Card } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { STOCKS } from "../lib/stocks";

export function ValuationPanel() {
  return (
    <Card className="overflow-x-auto">
      <h2 className="text-[22px] font-semibold">真值引力定价 V_G 与投资决策矩阵</h2>
      <table className="mt-3 w-full text-left text-[13px] tabular-nums">
        <thead>
          <tr className="text-muted-foreground">
            <th className="py-2">标的</th>
            <th>V_G</th>
            <th>市值</th>
            <th>α</th>
          </tr>
        </thead>
        <tbody>
          {STOCKS.map((s) => (
            <tr key={s.symbol} className="border-t border-border">
              <td className="py-2">{s.name}</td>
              <td>{s.gravity_val.toFixed(1)}</td>
              <td>{s.market_cap.toFixed(1)}</td>
              <td>{s.alpha.toFixed(1)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}

export function AutopsyPanel() {
  return (
    <div className="space-y-3">
      {STOCKS.filter((s) => !s.is_admitted).map((s) => (
        <Card key={s.symbol}>
          <h3 className="text-[18px] font-semibold">{s.name}</h3>
          {s.veto_reasons.map((r) => (
            <p key={r} className="mt-2 text-[13px] text-buy">{r}</p>
          ))}
        </Card>
      ))}
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
