import type { ReactNode } from "react";

export { bringPanelIntoMobileViewport, setMobileTab, switchTab } from "./lib/viewport";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="mx-auto min-h-screen max-w-[1400px] px-4 md:px-6">
      {children}
    </div>
  );
}
