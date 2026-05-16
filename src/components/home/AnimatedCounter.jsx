import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

/**
 * Hero stats counter — defined at module scope so parent re-renders do not
 * remount it (which would restart the animation and waste work).
 */
export default function AnimatedCounter({ end, duration, suffix = "", uptimePercent = false }) {
  const { i18n } = useTranslation();
  const [count, setCount] = useState(0);

  useEffect(() => {
    let start = 0;
    const tickMs = 50;
    const increment = end / (duration / tickMs);
    const timer = setInterval(() => {
      start += increment;
      if (start >= end) {
        setCount(end);
        clearInterval(timer);
      } else {
        setCount(Math.floor(start));
      }
    }, tickMs);
    return () => clearInterval(timer);
  }, [end, duration]);

  const loc = i18n.language?.toLowerCase().startsWith("ar") ? "ar-EG" : "en-US";

  if (uptimePercent) {
    const value = (count + 0.9) / 100;
    const text = new Intl.NumberFormat(loc, {
      style: "percent",
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    }).format(value);
    return (
      <span dir="ltr" className="hero-stat-number-ltr" translate="no">
        {text}
      </span>
    );
  }

  return (
    <span dir="ltr" className="hero-stat-number-ltr" translate="no">
      {count.toLocaleString(loc)}
      {suffix}
    </span>
  );
}
