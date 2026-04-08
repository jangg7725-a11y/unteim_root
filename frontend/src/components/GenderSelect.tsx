import "./field.css";

type Props = {
  value: "" | "male" | "female";
  onChange: (value: "male" | "female") => void;
};

export function GenderSelect({ value, onChange }: Props) {
  return (
    <div className="field field--soft">
      <span className="field__label">성별</span>
      <div className="segment segment--gender" role="group" aria-label="성별">
        <button
          type="button"
          className={`segment__btn${value === "male" ? " segment__btn--active" : ""}`}
          onClick={() => onChange("male")}
        >
          남
        </button>
        <button
          type="button"
          className={`segment__btn${value === "female" ? " segment__btn--active" : ""}`}
          onClick={() => onChange("female")}
        >
          여
        </button>
      </div>
    </div>
  );
}
