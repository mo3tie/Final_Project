import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import en from "../locales/en.json";

const STORAGE_KEY = "misr-gate-lang";

export function applyI18nToDocument(lng) {
  const code = lng && String(lng).toLowerCase().startsWith("ar") ? "ar" : "en";
  document.documentElement.lang = code;
  document.documentElement.dir = code === "ar" ? "rtl" : "ltr";
  return code;
}

function readStoredLang() {
  try {
    const v = localStorage.getItem(STORAGE_KEY);
    if (v === "ar" || v === "en") return v;
  } catch {
    /* ignore */
  }
  return "en";
}

const initial = readStoredLang();
applyI18nToDocument(initial);

const resources = { en: { translation: en } };

if (initial === "ar") {
  const arMod = await import("../locales/ar.json");
  resources.ar = { translation: arMod.default };
}

await i18n.use(initReactI18next).init({
  resources,
  lng: initial,
  fallbackLng: "en",
  interpolation: { escapeValue: false },
});

i18n.on("languageChanged", (lng) => {
  const code = applyI18nToDocument(lng);
  try {
    localStorage.setItem(STORAGE_KEY, code);
  } catch {
    /* ignore */
  }
});

export default i18n;
