import { useNavigate } from "react-router-dom";
import { ArrowLeft, BarChart3 } from "lucide-react";
import { Card } from "../components/Card";
import { MbtiProgressBar } from "../components/MbtiProgressBar";
import { useAppState } from "../state/AppState";
import "./DiagnosisResult.css";

const LETTER_DESCRIPTION: Record<string, string> = {
  D: "아침~늦은 오후(06~17시)에 유동·매출이 집중돼요",
  N: "저녁~새벽(17~06시)에 유동·매출이 강한 편이에요",
  U: "가성비와 실속을 우선하는 소비가 많아요",
  F: "분위기와 취향을 중시하는 소비가 많아요",
  T: "역세권 유입 고객 비중이 높아요",
  L: "동네 단골 고객 비중이 높아요",
  M: "프랜차이즈 등 대중적 경쟁이 많은 편이에요",
  G: "차별화된 틈새 포지션을 갖고 있어요",
};

export function DiagnosisResult() {
  const navigate = useNavigate();
  const { analysis } = useAppState();

  if (!analysis) {
    return (
      <div className="result-empty">
        <p>아직 진단 결과가 없습니다.</p>
        <button onClick={() => navigate("/diagnosis")}>MBTI 진단하러 가기</button>
      </div>
    );
  }

  const { mbti } = analysis;
  const dominantAxes = mbti.axes.map((axis) => {
    const dominant = axis.pct_left >= axis.pct_right;
    return {
      letter: dominant ? axis.letter_left : axis.letter_right,
      label: dominant ? axis.label_left : axis.label_right,
    };
  });
  const summary = dominantAxes
    .slice(0, 2)
    .map((a) => LETTER_DESCRIPTION[a.letter])
    .join(" · ");

  return (
    <div className="diagnosis-result">
      <button className="result-back" onClick={() => navigate(-1)}>
        <ArrowLeft size={16} /> 뒤로
      </button>

      <Card className="result-hero">
        <p className="result-hero-caption">우리 가게 MBTI는</p>
        <div className="result-hero-code">
          {mbti.code.split("").map((letter, i) => (
            <span key={i}>{letter}</span>
          ))}
        </div>
        <p className="result-hero-summary">{summary}</p>

        <div className="result-hero-grid">
          {dominantAxes.map((a, i) => (
            <div key={mbti.axes[i].axis} className="result-hero-box">
              <span className="result-hero-letter">
                {a.letter} <em>{a.label}</em>
              </span>
              <span className="result-hero-desc">{LETTER_DESCRIPTION[a.letter]}</span>
            </div>
          ))}
        </div>
      </Card>

      <Card className="result-compare">
        <h4>
          <BarChart3 size={16} strokeWidth={2} /> MBTI 비교 분석
        </h4>
        {mbti.axes.map((axis) => (
          <MbtiProgressBar key={axis.axis} axis={axis} theme="onLight" />
        ))}
      </Card>

      <button className="result-cta" onClick={() => navigate("/recommendations")}>
        상권 추천 결과 확인하기 →
      </button>
    </div>
  );
}
