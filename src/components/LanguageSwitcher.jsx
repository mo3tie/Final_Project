import { useTranslation } from "react-i18next";
import { Languages } from "lucide-react";
import "./LanguageSwitcher.css";

/**
 * @param {{
 *   className?: string;
 *   variant?: "sidebar" | "navbar" | "auth" | "ghost";
 *   hintTitle?: string;
 * }} props
 *
 * hintTitle — short hover `title` on sidebar only; navbar/auth omit browser tooltips.
 */
export default function LanguageSwitcher({ className = "", variant = "ghost", hintTitle }) {
  const { i18n, t } = useTranslation();
  const isAr = i18n.language?.toLowerCase().startsWith("ar");
  const next = isAr ? "en" : "ar";
  const label = isAr ? t("lang.switchToEnglish") : t("lang.switchToArabic");

  const handleSwitch = async () => {
    if (next === "ar" && !i18n.hasResourceBundle("ar", "translation")) {
      const mod = await import("../locales/ar.json");
      i18n.addResourceBundle("ar", "translation", mod.default, true, true);
    }
    await i18n.changeLanguage(next);
  };

  return (
    <button
      type="button"
      className={`language-switcher language-switcher--${variant} ${className}`.trim()}
      onClick={() => void handleSwitch()}
      title={variant === "sidebar" ? hintTitle || label : undefined}
      aria-label={label}
    >
      <Languages size={20} strokeWidth={1.75} aria-hidden />
      {variant === "navbar" ? (
        <span className="language-switcher__badge">{isAr ? "EN" : "عربي"}</span>
      ) : null}
    </button>
  );
}
