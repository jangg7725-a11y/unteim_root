import type { CalendarKind } from "@/types/birthInput";
import "./field.css";

type Props = {
  value: CalendarKind;
  onChange: (value: CalendarKind) => void;
};

export function CalendarToggle({ value, onChange }: Props) {
  return (
    <div className="field field--soft">
      <span className="field__label">달력</span>
      <div className="segment segment--calendar" role="group" aria-label="양력 또는 음력">
        <button
          type="button"
          className={`segment__btn${value === "lunar" ? " segment__btn--active" : ""}`}
          onClick={() => onChange("lunar")}
        >
          음력
        </button>
        <button
          type="button"
          className={`segment__btn${value === "solar" ? " segment__btn--active" : ""}`}
          onClick={() => onChange("solar")}
        >
          양력
        </button>
      </div>
    </div>
  );
}
