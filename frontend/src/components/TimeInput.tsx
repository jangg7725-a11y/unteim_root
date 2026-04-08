import "./field.css";

type Props = {
  id?: string;
  label?: string;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
};

export function TimeInput({
  id = "birth-time",
  label = "출생 시간",
  value,
  onChange,
  disabled,
}: Props) {
  return (
    <div className="field field--soft">
      <label className="field__label" htmlFor={id}>
        {label}
      </label>
      <input
        id={id}
        className="field__input field__input--time"
        type="time"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        step={60}
      />
    </div>
  );
}
