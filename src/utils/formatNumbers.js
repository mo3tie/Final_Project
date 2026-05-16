/**
 * Consistent money / count formatting for dashboard, wallet, trips (locale-aware).
 */

export function resolveLocale(i18nLanguage) {
  return i18nLanguage?.toLowerCase().startsWith("ar") ? "ar-EG" : "en-US";
}

const moneyCache = new Map();

function getMoneyFormatter(locale) {
  if (!moneyCache.has(locale)) {
    moneyCache.set(
      locale,
      new Intl.NumberFormat(locale, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }),
    );
  }
  return moneyCache.get(locale);
}

/** EGP amounts with grouped thousands and 2 decimals. */
export function formatMoney(value, locale, egpLabel) {
  const n = Number(value);
  const safe = Number.isFinite(n) ? n : 0;
  return `${getMoneyFormatter(locale).format(safe)}\u00A0${egpLabel}`;
}

/** + / − prefix for wallet transactions. */
export function formatSignedMoney(value, locale, egpLabel) {
  const n = Number(value);
  const safe = Number.isFinite(n) ? n : 0;
  const sign = safe < 0 ? "−" : "+";
  const body = getMoneyFormatter(locale).format(Math.abs(safe));
  return `${sign}${body}\u00A0${egpLabel}`;
}

/** Integers: trip counts, violations count, etc. */
export function formatCount(value, locale) {
  const n = Number(value);
  const safe = Number.isFinite(n) ? Math.trunc(n) : 0;
  return new Intl.NumberFormat(locale, {
    maximumFractionDigits: 0,
    useGrouping: true,
  }).format(safe);
}

/** Chart tooltips: money (2 dp) or counts (0 dp). */
export function formatChartMoney(value, locale) {
  return getMoneyFormatter(locale).format(Number.isFinite(Number(value)) ? Number(value) : 0);
}

export function formatChartCount(value, locale) {
  return formatCount(value, locale);
}

/** Y-axis ticks for wallet-style amounts (compact when large). */
export function formatAxisMoneyShort(value, locale) {
  const n = Number(value);
  if (!Number.isFinite(n)) return "0";
  const a = Math.abs(n);
  if (a >= 1_000_000) {
    return `${(n / 1_000_000).toLocaleString(locale, { maximumFractionDigits: 1 })}M`;
  }
  if (a >= 1000) {
    return `${(n / 1000).toLocaleString(locale, { maximumFractionDigits: 1 })}k`;
  }
  return getMoneyFormatter(locale).format(n);
}

/** Recharge / small displays — same as formatMoney but without NBSP if caller prefers */
export function formatMoneyPlain(value, locale, egpLabel) {
  return formatMoney(value, locale, egpLabel).replace("\u00A0", " ");
}
