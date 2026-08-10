import { useState } from "react";
import "./RangeSlider.css";

interface RangeSliderProps {
  leftLabel: string;
  rightLabel: string;
  value: number; // 0~100
  onChange: (value: number) => void;
}

export function RangeSlider({ leftLabel, rightLabel, value, onChange }: RangeSliderProps) {
  const [dragging, setDragging] = useState(false);

  return (
    <div className="rangeslider">
      <div className="rangeslider-labels">
        <span>{leftLabel}</span>
        <span>{rightLabel}</span>
      </div>
      <div className="rangeslider-track-wrap">
        {dragging && (
          <div className="rangeslider-bubble" style={{ left: `${value}%` }}>
            {value}
          </div>
        )}
        <input
          type="range"
          min={0}
          max={100}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          onPointerDown={() => setDragging(true)}
          onPointerUp={() => setDragging(false)}
          onBlur={() => setDragging(false)}
          className={dragging ? "dragging" : ""}
          style={{ background: `linear-gradient(to right, var(--color-primary) ${value}%, var(--color-border) ${value}%)` }}
        />
      </div>
      <div className="rangeslider-values">
        <span>0</span>
        <span>100</span>
      </div>
    </div>
  );
}