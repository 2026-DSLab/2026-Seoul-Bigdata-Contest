import { useNavigate } from "react-router-dom";
import { Sparkles, BarChart3, MapPin, ChevronRight } from "lucide-react";
import { TopBar } from "../components/TopBar";
import { Card } from "../components/Card";
import { useAppState } from "../state/AppState";
import "./Home.css";

export function Home() {
  const navigate = useNavigate();
  const { analysis, districtId, selectedDistrict } = useAppState();

  return (
    <>
      <TopBar />

      <Card className="home-cta" onClick={() => navigate("/diagnosis")}>
        <div className="home-cta-icon">
          <Sparkles size={20} strokeWidth={2} />
        </div>
        <h3>우리 가게 MBTI 진단</h3>
        <p>우리 가게의 성향을 진단하고 상권 속 정체성을 확인해보세요</p>
        <button className="home-cta-btn" onClick={() => navigate("/diagnosis")}>
          진단하러 가기 &gt;
        </button>
      </Card>

      {analysis && (
        <Card className="home-list-item" onClick={() => navigate("/diagnosis/result")}>
          <div className="home-list-icon home-list-icon-orange">
            <BarChart3 size={20} strokeWidth={2} />
          </div>
          <div className="home-list-text">
            <h4>우리 가게 MBTI 진단 결과</h4>
            <p>분석된 상권 성향과 브랜딩 결과를 확인해보세요</p>
            <span className="home-list-code">{analysis.mbti.code}</span>
          </div>
          <ChevronRight size={18} className="home-list-arrow" />
        </Card>
      )}

      {districtId && selectedDistrict && (
        <Card className="home-list-item" onClick={() => navigate(`/district/${districtId}`)}>
          <div className="home-list-icon home-list-icon-purple">
            <MapPin size={20} strokeWidth={2} />
          </div>
          <div className="home-list-text">
            <h4>새롭게 정의된 상권</h4>
            <p>{selectedDistrict.label}</p>
          </div>
          <ChevronRight size={18} className="home-list-arrow" />
        </Card>
      )}
    </>
  );
}
