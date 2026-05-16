/** Month keys aligned with `MonthlyLineChart` (Recharts) X axis. */
export const CHART_MONTHS = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

export function emptyMonthlySeries() {
  return CHART_MONTHS.map((month) => ({ month, value: 0, topCity: "" }));
}

/** Sum absolute movement per calendar month from wallet transactions (EGP). */
export function walletTransactionsToMonthly(transactions) {
  const buckets = Object.fromEntries(CHART_MONTHS.map((m) => [m, 0]));
  for (const tx of transactions || []) {
    const d = new Date(tx.date);
    if (Number.isNaN(d.getTime())) continue;
    const m = CHART_MONTHS[d.getMonth()];
    const amt = parseFloat(tx.amount, 10);
    if (Number.isNaN(amt)) continue;
    buckets[m] += Math.abs(amt);
  }
  return CHART_MONTHS.map((month) => ({
    month,
    value: Math.round(buckets[month] * 100) / 100,
  }));
}

/** Trip counts per calendar month from API trips (`dateIso` YYYY-MM-DD), plus busiest city per month. */
export function tripsToMonthlyCounts(trips) {
  const buckets = Object.fromEntries(CHART_MONTHS.map((m) => [m, 0]));
  const cityAgg = Object.fromEntries(CHART_MONTHS.map((m) => [m, {}]));
  for (const trip of trips || []) {
    const iso = trip.dateIso;
    if (!iso) continue;
    const d = new Date(`${iso}T12:00:00`);
    if (Number.isNaN(d.getTime())) continue;
    const m = CHART_MONTHS[d.getMonth()];
    buckets[m] += 1;
    const city = (trip.governorate || "").trim() || "—";
    const inner = cityAgg[m];
    inner[city] = (inner[city] || 0) + 1;
  }
  return CHART_MONTHS.map((month) => {
    const cities = cityAgg[month];
    const topEntry = Object.entries(cities).sort(
      (a, b) => b[1] - a[1] || a[0].localeCompare(b[0]),
    )[0];
    const topCity = topEntry?.[0] && topEntry[1] > 0 ? topEntry[0] : "";
    return { month, value: buckets[month], topCity };
  });
}

