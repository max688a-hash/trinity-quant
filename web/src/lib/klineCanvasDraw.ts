import type { Candle } from "./types";

export type KlineOverlays = {
  ma5: boolean;
  ma10: boolean;
  ma20: boolean;
  ma60: boolean;
};

const DEFAULT_OVERLAYS: KlineOverlays = {
  ma5: true,
  ma10: true,
  ma20: true,
  ma60: true,
};

const MA_COLORS: Array<{ key: keyof KlineOverlays; field: keyof Candle; color: string }> = [
  { key: "ma5", field: "ma5", color: "#38bdf8" },
  { key: "ma10", field: "ma10", color: "#a78bfa" },
  { key: "ma20", field: "ma20", color: "#fbbf24" },
  { key: "ma60", field: "ma60", color: "#94a3b8" },
];

function paintMark(
  ctx: CanvasRenderingContext2D,
  mid: number,
  yHigh: number,
  yLow: number,
  side: "BUY" | "SELL",
  color: string,
): void {
  ctx.fillStyle = color;
  ctx.beginPath();
  if (side === "BUY") {
    const y = Math.min(258, yLow + 10);
    ctx.moveTo(mid, y);
    ctx.lineTo(mid - 5, y + 8);
    ctx.lineTo(mid + 5, y + 8);
  } else {
    const y = Math.max(8, yHigh - 10);
    ctx.moveTo(mid, y);
    ctx.lineTo(mid - 5, y - 8);
    ctx.lineTo(mid + 5, y - 8);
  }
  ctx.closePath();
  ctx.fill();
}

function yAt(px: number, maxH: number, span: number): number {
  return 12 + ((maxH - px) / span) * 248;
}

function paintMa(
  ctx: CanvasRenderingContext2D,
  rows: Candle[],
  w: number,
  maxH: number,
  span: number,
  overlays: KlineOverlays,
): void {
  MA_COLORS.forEach((spec) => {
    if (!overlays[spec.key]) {
      return;
    }
    ctx.strokeStyle = spec.color;
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    let started = false;
    rows.forEach((c, i) => {
      const raw = c[spec.field];
      const px = typeof raw === "number" && Number.isFinite(raw) ? raw : NaN;
      if (!Number.isFinite(px) || px <= 0) {
        started = false;
        return;
      }
      const x = i * w + w * 0.3;
      const y = yAt(px, maxH, span);
      if (!started) {
        ctx.moveTo(x, y);
        started = true;
      } else {
        ctx.lineTo(x, y);
      }
    });
    ctx.stroke();
  });
}

function paintVolume(
  ctx: CanvasRenderingContext2D,
  rows: Candle[],
  w: number,
): void {
  const vols = rows.map((c) => (Number.isFinite(c.volume) && c.volume > 0 ? c.volume : 0));
  const maxV = Math.max(...vols, 0);
  if (maxV <= 0) {
    return;
  }
  rows.forEach((c, i) => {
    const vol = vols[i];
    if (vol <= 0) {
      return;
    }
    const h = Math.max(1, (vol / maxV) * 58);
    const x = i * w + w * 0.15;
    const up = c.close >= c.open;
    ctx.fillStyle = up ? "rgba(190, 74, 64, 0.55)" : "rgba(47, 154, 108, 0.55)";
    ctx.fillRect(x, 350 - h, w * 0.7, h);
  });
}

export function paintKline(
  ctx: CanvasRenderingContext2D,
  rows: Candle[],
  width: number,
  height: number,
  overlays: KlineOverlays = DEFAULT_OVERLAYS,
): void {
  ctx.fillStyle = "#121a24";
  ctx.fillRect(0, 0, width, height);
  if (rows.length < 2) {
    ctx.fillStyle = "#9fb0c0";
    ctx.fillText("DATA_UNAVAILABLE", 16, 24);
    return;
  }
  const highs = rows.map((c) => c.high);
  const lows = rows.map((c) => c.low);
  const maxH = Math.max(...highs);
  const minL = Math.min(...lows);
  const span = Math.max(0.01, maxH - minL);
  const w = width / rows.length;
  ctx.strokeStyle = "#1f2a36";
  ctx.beginPath();
  ctx.moveTo(0, 268);
  ctx.lineTo(width, 268);
  ctx.stroke();
  rows.forEach((c, i) => {
    const x = i * w + w * 0.2;
    const yHigh = yAt(c.high, maxH, span);
    const yLow = yAt(c.low, maxH, span);
    const yO = yAt(c.open, maxH, span);
    const yC = yAt(c.close, maxH, span);
    const up = c.close >= c.open;
    ctx.strokeStyle = up ? "#be4a40" : "#2f9a6c";
    ctx.fillStyle = up ? "#be4a40" : "#2f9a6c";
    ctx.beginPath();
    ctx.moveTo(x + w * 0.3, yHigh);
    ctx.lineTo(x + w * 0.3, yLow);
    ctx.stroke();
    const top = Math.min(yO, yC);
    const body = Math.max(1, Math.abs(yC - yO));
    ctx.fillRect(x, top, w * 0.6, body);
    if (c.signal) {
      paintMark(ctx, x + w * 0.3, yHigh, yLow, c.signal.type, c.signal.color);
    }
  });
  paintMa(ctx, rows, w, maxH, span, overlays);
  paintVolume(ctx, rows, w);
}
