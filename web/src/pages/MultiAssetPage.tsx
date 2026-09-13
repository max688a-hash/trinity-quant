import { useMemo, useState } from "react";
import { Card } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger } from "../components/ui/select";
import { MARKET_SECTORS } from "../lib/markets";

export function MultiAssetPage() {
  const corn = MARKET_SECTORS.futures.assets.find((a) => a.code === "C");
  const [code, setCode] = useState("C");
  const [z, setZ] = useState(0.18);
  const asset = MARKET_SECTORS.futures.assets.find((a) => a.code === code) ?? corn;
  const mid = asset?.base ?? 2400;
  const atr = 22.5;
  const band = useMemo(() => [mid - atr * 1.6, mid + atr * 1.6] as const, [mid, atr]);

  return (
    <div className="space-y-4">
      <Card>
        <h2 className="text-[22px] font-semibold">全市场多资产自适应波动空间与临界状态突变中枢</h2>
        <p className="mt-2 font-mono text-[13px] text-muted-foreground">无量纲归一化 Z = (P - μ) / σ</p>
      </Card>
      <Card className="space-y-3">
        <h3 className="text-[18px] font-semibold">标的波动与订单审核模拟器</h3>
        <label className="text-[13px]">选择测试标的</label>
        <Select value={code} onValueChange={setCode}>
          <SelectTrigger />
          <SelectContent>
            {MARKET_SECTORS.futures.assets.map((a) => (
              <SelectItem key={a.code} value={a.code}>
                {a.name} ({a.code}) · 基准 {a.base}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <label className="text-[13px]" htmlFor="z">模拟偏离 σ</label>
        <Input
          id="z"
          type="range"
          min={-4}
          max={4}
          step={0.01}
          value={z}
          onChange={(e) => setZ(Number(e.target.value))}
        />
        <p className="tabular-nums text-[15px]">
          {(mid + z * atr).toFixed(1)} 元/吨 （Z={z.toFixed(2)}）
        </p>
        <p className="text-[13px] text-muted-foreground">
          标的价格在 [{band[0].toFixed(0)}, {band[1].toFixed(0)}] 常态空间内振荡。ATR {atr}
        </p>
      </Card>
    </div>
  );
}
