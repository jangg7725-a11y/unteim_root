import "./field.css";

type Props = {
  id?: string;
  label?: string;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
};

/** 네이티브 date — 모바일/데스크톱에서 OS date picker 사용 */
export function DateInput({
  id = "birth-date",
  label = "생년월일",
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
        className="field__input field__input--date"
        type="date"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        max="2100-12-31"
        min="1900-01-01"
      />
    </div>
  );
}
