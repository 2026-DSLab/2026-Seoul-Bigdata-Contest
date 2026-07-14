import type { MbtiAxis } from "../api/types";
import "./MbtiProgressBar.css";

interface MbtiProgressBarProps {
  axis: MbtiAxis;
  theme?: "onGradient" | "onLight";
}

export function MbtiProgressBar({ axis, theme = "onGradient" }: MbtiProgressBarProps) {
  return (
    <div className={`mbtibar mbtibar-${theme}`}>
      <div className="mbtibar-labels">
        <span>
          {axis.label_left} ({axis.letter_left})
        </span>
        <span>{axis.pct_left}%</span>
      </div>
      <div className="mbtibar-track">
        <div className="mbtibar-fill" style={{ width: `${axis.pct_left}%` }} />
      </div>
      <div className="mbtibar-labels mbtibar-labels-right">
        <span>{axis.pct_right}%</span>
        <span>
          {axis.label_right} ({axis.letter_right})
        </span>
      </div>
    </div>
  );
}
