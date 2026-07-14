import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { Store, Footprints, Tag } from "lucide-react";
import { Card } from "../components/Card";
import { KakaoMap } from "../components/KakaoMap";
import { api } from "../api/client";
import type { DistrictResponse } from "../api/types";
import "./District.css";

const OURS_COLOR = "#6D5BD0";
const OTHER_COLORS = ["#22C55E", "#F97316", "#0EA5E9", "#EC4899", "#EAB308"];

function haversineM(a: { lat: number; lng: number }, b: { lat: number; lng: number }): number {
  const R = 6_371_000;
  const dLat = ((b.lat - a.lat) * Math.PI) / 180;
  const dLng = ((b.lng - a.lng) * Math.PI) / 180;
  const s =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((a.lat * Math.PI) / 180) * Math.cos((b.lat * Math.PI) / 180) * Math.sin(dLng / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(s), Math.sqrt(1 - s));
}

function maxSpanKm(points: { lat: number; lng: number }[]): number {
  let max = 0;
  for (let i = 0; i < points.length; i++) {
    for (let j = i + 1; j < points.length; j++) {
      max = Math.max(max, haversineM(points[i], points[j]));
    }
  }
  return Math.round((max / 1000) * 10) / 10;
}

export function District() {
  const { districtId } = useParams<{ districtId: string }>();
  const [district, setDistrict] = useState<DistrictResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<"map" | "nearby">("map");

  useEffect(() => {
    if (!districtId) return;
    api.getDistrict(districtId).then(setDistrict).catch((e) =>
      setError(e instanceof Error ? e.message : "상권 정보를 불러오지 못했습니다.")
    );
  }, [districtId]);

  const ourPins = useMemo(
    () => district?.member_pins.filter((p) => p.lat != null && p.lng != null) ?? [],
    [district]
  );

  const clusters = district?.clusters ?? [];

  const allValidPins = useMemo(
    () => clusters.flatMap((c) => c.member_pins.filter((p) => p.lat != null && p.lng != null)),
    [clusters]
  );

  const center = allValidPins.length
    ? {
        lat: allValidPins.reduce((s, p) => s + (p.lat ?? 0), 0) / allValidPins.length,
        lng: allValidPins.reduce((s, p) => s + (p.lng ?? 0), 0) / allValidPins.length,
      }
    : { lat: 37.5478, lng: 126.9228 };

  const walkingDistanceKm = ourPins.length >= 2
    ? maxSpanKm(ourPins.map((p) => ({ lat: p.lat as number, lng: p.lng as number })))
    : 0;

  if (error) return <p className="district-error">{error}</p>;
  if (!district) return <p className="district-loading">불러오는 중...</p>;

  let otherColorIdx = 0;
  const polygons = clusters.map((c) => {
    const color = c.is_ours ? OURS_COLOR : OTHER_COLORS[otherColorIdx++ % OTHER_COLORS.length];
    return { path: c.polygon, color, label: c.label, _memberPins: c.member_pins, _color: color };
  });

  const pins = polygons.flatMap((p) =>
    p._memberPins
      .filter((m) => m.lat != null && m.lng != null)
      .map((m) => ({ lat: m.lat as number, lng: m.lng as number, label: m.상호명, color: p._color }))
  );

  return (
    <div className="district">
      <h2 className="district-title">우리 상권+</h2>
      <p className="district-sub">우리 상권 활성화를 위한 브랜딩</p>

      <Card className="district-name-card">
        <h3>{district.label}</h3>
        <p>{district.main_categories}</p>
      </Card>

      <div className="district-stats">
        <Card className="district-stat">
          <div className="district-stat-icon"><Store size={18} strokeWidth={2} /></div>
          <span className="district-stat-value">{district.member_count}개</span>
          <span className="district-stat-label">연결 매장</span>
        </Card>
        <Card className="district-stat">
          <div className="district-stat-icon"><Footprints size={18} strokeWidth={2} /></div>
          <span className="district-stat-value">{walkingDistanceKm}km</span>
          <span className="district-stat-label">도보 거리</span>
        </Card>
        <Card className="district-stat">
          <div className="district-stat-icon"><Tag size={18} strokeWidth={2} /></div>
          <span className="district-stat-value">{district.tags.length}개</span>
          <span className="district-stat-label">정체성 태그</span>
        </Card>
      </div>

      <div className="district-tabs">
        <button className={tab === "map" ? "active" : ""} onClick={() => setTab("map")}>상권맵</button>
        <button className={tab === "nearby" ? "active" : ""} onClick={() => setTab("nearby")}>주변상권</button>
      </div>

      {tab === "map" ? (
        <Card className="district-map-card">
          <KakaoMap
            center={center}
            polygons={polygons.map(({ path, color, label }) => ({ path, color, label }))}
            pins={pins}
          />
          <p className="district-map-caption">
            이 상권은 행정구역이 아닌 고객 행동과 브랜딩 DNA로 새롭게 정의되었습니다
            {clusters.length > 1 && ` · 주변 ${clusters.length - 1}개 상권과 함께 표시 중`}
          </p>
        </Card>
      ) : (
        <Card className="district-nearby-placeholder">
          <p>주변 상권 비교 기능은 준비 중입니다.</p>
        </Card>
      )}

      <h4 className="district-section-title">우리 상권 공동 브랜딩 전략</h4>
      {district.strategies.length === 0 && (
        <p className="district-empty-strategy">아직 생성된 브랜딩 전략이 없습니다.</p>
      )}
      {district.strategies.map((s, i) => (
        <Card key={i} className="district-strategy-card">
          <div className="district-strategy-head">
            <h5>{s.title}</h5>
            <span className="district-strategy-badge">상권 전체</span>
          </div>
          <p>{s.description}</p>
          <span className="district-strategy-effect">↗ {s.effect}</span>
        </Card>
      ))}
    </div>
  );
}
