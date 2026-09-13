/** 选股引擎给 6 位代码，撮合器与看板要交易所后缀。 */
export function toListedSymbol(raw: string): string {
  const symbol = raw.trim().toUpperCase();
  if (!symbol || symbol.includes(".")) {
    return symbol;
  }
  if (/^[69]/.test(symbol)) {
    return `${symbol}.SH`;
  }
  if (/^[03]/.test(symbol)) {
    return `${symbol}.SZ`;
  }
  return symbol;
}
