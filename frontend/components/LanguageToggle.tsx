import type { Language } from "@/lib/types";

interface LanguageToggleProps {
  language: Language;
  onChange: (language: Language) => void;
}

export function LanguageToggle({ language, onChange }: LanguageToggleProps) {
  return (
    <div className="flex gap-2 text-sm">
      <button
        type="button"
        onClick={() => onChange("pl")}
        aria-pressed={language === "pl"}
        className={language === "pl" ? "font-semibold underline" : "text-gray-500"}
      >
        PL
      </button>
      <button
        type="button"
        onClick={() => onChange("en")}
        aria-pressed={language === "en"}
        className={language === "en" ? "font-semibold underline" : "text-gray-500"}
      >
        EN
      </button>
    </div>
  );
}
