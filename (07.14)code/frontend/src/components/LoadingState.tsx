import { useEffect, useState } from "react";
import "./LoadingState.css";

interface LoadingStateProps {
  steps: string[];
  intervalMs?: number;
}

export function LoadingState({ steps, intervalMs = 1600 }: LoadingStateProps) {
  const [stepIdx, setStepIdx] = useState(0);

  useEffect(() => {
    if (steps.length <= 1) return;
    const timer = setInterval(() => {
      setStepIdx((i) => Math.min(i + 1, steps.length - 1));
    }, intervalMs);
    return () => clearInterval(timer);
  }, [steps.length, intervalMs]);

  return (
    <div className="loading-state">
      <div className="loading-spinner" />
      <p className="loading-text">{steps[stepIdx]}</p>
      <div className="loading-dots">
        {steps.map((_, i) => (
          <span key={i} className={"loading-dot" + (i <= stepIdx ? " active" : "")} />
        ))}
      </div>
    </div>
  );
}
