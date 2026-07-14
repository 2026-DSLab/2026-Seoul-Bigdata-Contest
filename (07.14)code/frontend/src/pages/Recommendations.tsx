import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { Card } from "../components/Card";
import { api } from "../api/client";
import { useAppState } from "../state/AppState";
import type { RecommendationCard } from "../api/types";
import "./Recommendations.css";

export function Recommendations() {
  const navigate = useNavigate();
  const { analysis, setSelectedDistrict, setDistrictId } = useAppState();

  const [cards, setCards] = useState<RecommendationCard[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null);
  const [confirming, setConfirming] = useState(false);

  useEffect(() => {
    if (!analysis) return;
    api
      .getRecommendations(analysis.store_id)
      .then((res) => {
        if (res.status === "insufficient_data") {
          setMessage(res.message ?? "추천할 상권이 아직 없습니다.");
        } else {
          setCards(res.recommendations);
        }
      })
      .catch((e) => setMessage(e instanceof Error ? e.message : "오류가 발생했습니다."))
      .finally(() => setLoading(false));
  }, [analysis]);

  if (!analysis) {
    return (
      <div className="reco-empty">
        <p>먼저 MBTI 진단을 진행해주세요.</p>
        <button onClick={() => navigate("/diagnosis")}>MBTI 진단하러 가기</button>
      </div>
    );
  }

  const handleConfirm = async () => {
    if (selectedIdx === null) return;
    const card = cards[selectedIdx];
    setConfirming(true);
    try {
      const districtId = `district-${card.label}-${Date.now()}`;
      await api.joinDistrict(analysis.store_id, {
        district_id: districtId,
        district_label: card.label,
        member_store_ids: card.member_store_ids,
      });
      setSelectedDistrict(card);
      setDistrictId(districtId);
      navigate(`/district/${districtId}`);
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "상권 확정 중 오류가 발생했습니다.");
    } finally {
      setConfirming(false);
    }
  };

  return (
    <div className="reco">
      <button className="reco-back" onClick={() => navigate(-1)}>
        <ArrowLeft size={16} /> 뒤로
      </button>

      <span className="reco-badge">MBTI 진단 완료</span>
      <h2 className="reco-title">
        당신의 가게와 가장<br />잘 어울리는 상권이에요
      </h2>
      <p className="reco-sub">MBTI 진단 결과를 기반으로 가장 잘 맞는 상권 {cards.length || 3}곳을 추천했어요</p>

      {loading && <p className="reco-loading">추천 상권을 분석하는 중...</p>}
      {message && <Card className="reco-message">{message}</Card>}

      {cards.map((card, idx) => (
        <Card
          key={idx}
          className={"reco-card" + (selectedIdx === idx ? " reco-card-selected" : "")}
          onClick={() => setSelectedIdx(idx)}
        >
          <h3>{card.label}</h3>
          <div className="reco-tags">
            {card.tags.map((t) => <span key={t} className="reco-tag">{t}</span>)}
          </div>
          <dl className="reco-detail">
            <dt>주요 업종</dt><dd>{card.main_categories}</dd>
            <dt>대표 분위기</dt><dd>{card.mood}</dd>
            <dt>방문 특징</dt><dd>{card.visitor_feature}</dd>
          </dl>
          <button
            className={"reco-select-btn" + (selectedIdx === idx ? " selected" : "")}
            onClick={(e) => { e.stopPropagation(); setSelectedIdx(idx); }}
          >
            {selectedIdx === idx ? "선택됨" : "선택하기"}
          </button>
        </Card>
      ))}

      {cards.length > 0 && (
        <button
          className="reco-confirm-btn"
          disabled={selectedIdx === null || confirming}
          onClick={handleConfirm}
        >
          {confirming ? "확정 중..." : "우리 상권 확정하기"}
        </button>
      )}
    </div>
  );
}
