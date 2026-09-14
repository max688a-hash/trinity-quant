import type { Candle } from "./types";

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
    const y = Math.min(348, yLow + 10);
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

export function paintKline(
  ctx: CanvasRenderingContext2D,
  rows: Candle[],
  width: number,
  height: number,
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
  rows.forEach((c, i) => {
    const x = i * w + w * 0.2;
    const yHigh = 20 + ((maxH - c.high) / span) * 300;
    const yLow = 20 + ((maxH - c.low) / span) * 300;
    const yO = 20 + ((maxH - c.open) / span) * 300;
    const yC = 20 + ((maxH - c.close) / span) * 300;
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
}
