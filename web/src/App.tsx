import { BarChart3, CandlestickChart, Globe2, Shield, Swords } from "lucide-react";
import { useEffect, useState } from "react";
import { DocketModal, openAdmissionDocketModal } from "./components/DocketModal";
import { KlineChart } from "./components/KlineChart";
import { Button } from "./components/ui/button";
import { TooltipProvider } from "./components/ui/tooltip";
import { AppShell, setMobileTab } from "./layouts";
import { AutopsyPanel, CalculatorPanel, PitPanel, ValuationPanel } from "./pages/DesktopPanels";
import { BacktestPage } from "./pages/BacktestPage";
import { MultiAssetPage } from "./pages/MultiAssetPage";
import { PaperPage } from "./pages/PaperPage";
import { ScreenerPage } from "./pages/ScreenerPage";
import type { TabId } from "./lib/types";
import { bindSwitchTab } from "./lib/viewport";

const DESKTOP: { id: TabId; label: string }[] = [
  { id: "tab-backtest", label: "净值回测" },
  { id: "tab-screener", label: "排毒大屏" },
  { id: "tab-reflex", label: "分形K线" },
  { id: "tab-paper", label: "实战与演练" },
  { id: "tab-multiasset", label: "多资产" },
  { id: "tab-valuation", label: "引力榜" },
  { id: "tab-autopsy", label: "尸检" },
  { id: "tab-pit", label: "PIT" },
  { id: "tab-calculator", label: "沙盒" },
];

export default function App() {
  const [tab, setTab] = useState<TabId>("tab-backtest");

  useEffect(() => {
    bindSwitchTab((id) => setTab(id as TabId));
  }, []);

  const dockCls = (id: TabId) =>
    `mobile-nav-item flex min-h-14 flex-col items-center justify-center gap-1 rounded-none text-[11px] ${
      tab === id ? "text-primary font-semibold" : "text-muted-foreground"
    }`;

  return (
    <TooltipProvider>
      <AppShell>
        <header className="flex flex-wrap items-center justify-between gap-4 py-4">
          <div>
            <p className="text-[11px] tracking-wide text-muted-foreground">TRINITY QUANT</p>
            <h1 className="text-[22px] font-semibold tracking-[-0.02em]">真值引力量化中枢</h1>
          </div>
          <Button variant="secondary" onClick={() => openAdmissionDocketModal("600519.SH")}>
            入池深研依据
          </Button>
        </header>
        <div id="mobileCompactTicker" className="sticky top-0 z-40 -mx-4 mb-4 border-b border-border bg-background/95 px-4 py-2 md:hidden">
          <div className="flex gap-4 overflow-x-auto text-[13px] tabular-nums no-scrollbar">
            <span>茅台 1550</span>
            <span>纯碱 1580</span>
            <span>USDCNH 7.125</span>
            <span>BTC 64200</span>
          </div>
        </div>
        <div id="mobilePersistentChrome" className="hidden md:block">
          <div className="mb-6 grid grid-cols-4 gap-4">
            <div className="rounded-[16px] border border-border bg-card p-4">
              <p className="text-[11px] text-muted-foreground">A股证券市场</p>
              <p className="mt-2 text-[18px] font-semibold tabular-nums">上证 3,042.88</p>
            </div>
            <div className="rounded-[16px] border border-border bg-card p-4">
              <p className="text-[11px] text-muted-foreground">国内商品期货</p>
              <p className="mt-2 text-[18px] font-semibold tabular-nums">南华 2,280.45</p>
            </div>
            <div className="rounded-[16px] border border-border bg-card p-4">
              <p className="text-[11px] text-muted-foreground">全球外汇市场</p>
              <p className="mt-2 text-[18px] font-semibold tabular-nums">美元指数 101.25</p>
            </div>
            <div className="rounded-[16px] border border-border bg-card p-4">
              <p className="text-[11px] text-muted-foreground">全球加密数字资产</p>
              <p className="mt-2 text-[18px] font-semibold tabular-nums">BTC 64,200</p>
            </div>
          </div>
        </div>
        <div className="hidden md:flex mb-8 gap-2 overflow-x-auto rounded-[16px] border border-border bg-background p-2">
          {/* id="btn-tab-backtest" 桌面条锚点 */}
          {DESKTOP.map((item) => (
            <Button
              key={item.id}
              id={item.id === "tab-backtest" ? "btn-tab-backtest" : `btn-${item.id}`}
              variant={tab === item.id ? "default" : "ghost"}
              onClick={() => setMobileTab(item.id)}
            >
              {item.label}
            </Button>
          ))}
        </div>
        <main>
          <div id="tab-backtest" data-testid="panel-backtest" className={tab === "tab-backtest" ? "min-h-[70vh] pb-24" : "hidden"}>
            <BacktestPage />
          </div>
          <div id="tab-screener" data-testid="panel-screener" className={tab === "tab-screener" ? "min-h-[70vh] pb-24" : "hidden"}>
            <ScreenerPage />
          </div>
          <div id="tab-reflex" data-testid="panel-reflex" className={tab === "tab-reflex" ? "min-h-[70vh] pb-24" : "hidden"}>
            <KlineChart />
          </div>
          <div id="tab-paper" data-testid="panel-paper" className={tab === "tab-paper" ? "min-h-[70vh] pb-24" : "hidden"}>
            <PaperPage />
          </div>
          <div id="tab-multiasset" data-testid="panel-multiasset" className={tab === "tab-multiasset" ? "min-h-[70vh] pb-24" : "hidden"}>
            <MultiAssetPage />
          </div>
          <div id="tab-valuation" className={tab === "tab-valuation" ? "min-h-[70vh] pb-24" : "hidden"}>
            <ValuationPanel />
          </div>
          <div id="tab-autopsy" className={tab === "tab-autopsy" ? "min-h-[70vh] pb-24" : "hidden"}>
            <AutopsyPanel />
          </div>
          <div id="tab-pit" className={tab === "tab-pit" ? "min-h-[70vh] pb-24" : "hidden"}>
            <PitPanel />
          </div>
          <div id="tab-calculator" className={tab === "tab-calculator" ? "min-h-[70vh] pb-24" : "hidden"}>
            <CalculatorPanel />
          </div>
        </main>
        <nav className="fixed inset-x-0 bottom-0 z-50 border-t border-border bg-background/95 md:hidden">
          <div className="grid grid-cols-5">
            <Button type="button" data-tab="tab-backtest" variant="ghost" className={dockCls("tab-backtest")} onClick={() => setMobileTab("tab-backtest")}>
              <BarChart3 className="h-4 w-4" />净值回测
            </Button>
            <Button type="button" data-tab="tab-screener" variant="ghost" className={dockCls("tab-screener")} onClick={() => setMobileTab("tab-screener")}>
              <Shield className="h-4 w-4" />排毒大屏
            </Button>
            <Button type="button" data-tab="tab-reflex" variant="ghost" className={dockCls("tab-reflex")} onClick={() => setMobileTab("tab-reflex")}>
              <CandlestickChart className="h-4 w-4" />分形K线
            </Button>
            <Button type="button" data-tab="tab-paper" variant="ghost" className={dockCls("tab-paper")} onClick={() => setMobileTab("tab-paper")}>
              <Swords className="h-4 w-4" />实战与演练
            </Button>
            <Button type="button" data-tab="tab-multiasset" variant="ghost" className={dockCls("tab-multiasset")} onClick={() => setMobileTab("tab-multiasset")}>
              <Globe2 className="h-4 w-4" />多资产
            </Button>
          </div>
        </nav>
        <DocketModal />
      </AppShell>
    </TooltipProvider>
  );
}
