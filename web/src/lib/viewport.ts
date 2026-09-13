export function bringPanelIntoMobileViewport(tabId: string): void {
  const isNarrow = window.matchMedia("(max-width: 767px)").matches;
  if (!isNarrow) {
    return;
  }
  const target = document.getElementById(tabId);
  if (!target) {
    return;
  }
  let anchor: HTMLElement = target;
  if (tabId === "tab-reflex") {
    const canvasAnchor =
      document.getElementById("klineTopTickerBar") ||
      document.getElementById("klineCanvasWrapper");
    if (canvasAnchor) {
      anchor = canvasAnchor;
    }
  }
  const header = document.querySelector("header");
  const ticker = document.getElementById("mobileCompactTicker");
  const nav = document.querySelector("nav");
  const viewH = window.innerHeight;
  const headerBottom = header ? header.getBoundingClientRect().bottom : 0;
  const tickerBox = ticker ? ticker.getBoundingClientRect() : null;
  const tickerShown = Boolean(ticker && tickerBox && getComputedStyle(ticker).display !== "none");
  const usableTop = tickerShown && tickerBox ? tickerBox.bottom : headerBottom;
  const navTop = nav ? nav.getBoundingClientRect().top : viewH;
  const navH = Math.max(72, viewH - navTop);
  target.style.paddingBottom = `${navH + 16}px`;
  const y = anchor.getBoundingClientRect().top + window.scrollY - usableTop - 8;
  window.scrollTo({ top: Math.max(0, y), behavior: "smooth" });
}

export function setMobileTab(tabId: string): void {
  switchTab(tabId);
  bringPanelIntoMobileViewport(tabId);
}

type SwitchHandler = (tabId: string) => void;
let onSwitch: SwitchHandler | null = null;

export function bindSwitchTab(handler: SwitchHandler): void {
  onSwitch = handler;
}

export function switchTab(tabId: string): void {
  const isNarrow = window.matchMedia("(max-width: 767px)").matches;
  if (!isNarrow) {
    window.scrollTo(0, 0);
  }
  if (onSwitch) {
    onSwitch(tabId);
  }
  if (tabId === "tab-reflex") {
    requestAnimationFrame(() => {
      const canvas = document.getElementById("klineCanvas") as HTMLCanvasElement | null;
      if (canvas && canvas.getBoundingClientRect().width > 0) {
        drawKlineChart();
      }
    });
  }
  if (isNarrow) {
    bringPanelIntoMobileViewport(tabId);
  }
}

export function scrollToPaperSection(secId: string): void {
  const el = document.getElementById(secId);
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

let drawImpl: () => void = () => {};
export function registerKlineDrawer(fn: () => void): void {
  drawImpl = fn;
}
export function drawKlineChart(): void {
  drawImpl();
}
