import "./ChipSelect.css";

interface ChipSelectProps {
  options: string[];
  value: string[];
  onChange: (value: string[]) => void;
  multi?: boolean;
}

export function ChipSelect({ options, value, onChange, multi = false }: ChipSelectProps) {
  const toggle = (opt: string) => {
    if (multi) {
      onChange(value.includes(opt) ? value.filter((v) => v !== opt) : [...value, opt]);
    } else {
      onChange([opt]);
    }
  };

  return (
    <div className="chipselect">
      {options.map((opt) => (
        <button
          type="button"
          key={opt}
          className={"chip" + (value.includes(opt) ? " chip-selected" : "")}
          onClick={() => toggle(opt)}
        >
          {opt}
        </button>
      ))}
    </div>
  );
}
