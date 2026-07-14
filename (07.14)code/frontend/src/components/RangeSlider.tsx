import "./RangeSlider.css";

interface RangeSliderProps {
  leftLabel: string;
  rightLabel: string;
  value: number; // 0~100
  onChange: (value: number) => void;
}

export function RangeSlider({ leftLabel, rightLabel, value, onChange }: RangeSliderProps) {
  return (
    <div className="rangeslider">
      <div className="rangeslider-labels">
        <span>{leftLabel}</span>
        <span>{rightLabel}</span>
      </div>
      <input
        type="range"
        min={0}
        max={100}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        style={{ background: `linear-gradient(to right, var(--color-primary) ${value}%, var(--color-border) ${value}%)` }}
      />
      <div className="rangeslider-values">
        <span>{100 - value}</span>
        <span>{value}</span>
      </div>
    </div>
  );
}
