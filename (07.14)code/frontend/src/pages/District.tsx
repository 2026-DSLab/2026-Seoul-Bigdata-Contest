import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { Store, Footprints, Tag, Stamp, CreditCard, Percent, Video, PiggyBank, MessageCircle } from "lucide-react";
import { Card } from "../components/Card";
import { KakaoMap } from "../components/KakaoMap";
import { LoadingState } from "../components/LoadingState";
import { api } from "../api/client";
import type { DistrictResponse } from "../api/types";
import "./District.css";

const OURS_COLOR = "#6D5BD0";
const OTHER_COLORS = ["#22C55E", "#F97316", "#0EA5E9", "#EC4899", "#EAB308"];

const NETWORKING_PROGRAMS = [
  {
    icon: Stamp,
    title: "상권 통합 스탬프 투어",
    description: "상권 내 가게 3곳 이상 방문 시 스탬프 적립, 완주 고객에게 공동 할인 쿠폰 제공",
    effect: "재방문율 증가 및 가게 간 고객 유입 분산",
  },
  {
    icon: CreditCard,
    title: "상권 공동 구독 패스",
    description:
      "월 정액으로 이종 업종 혜택을 묶은 상권 공동 이용권 운영 (예: 월 1만원에 상권 내 카페 음료 1잔 + 소품샵 할인 + 세탁소 쿠폰 등 이종 업종 묶음 구독)",
    effect: "고정 고객 확보 및 소상공인 매출 안정성 강화",
  },
  {
    icon: Percent,
    title: "유휴시간대 공동 타임세일",
    description: "유동인구 데이터 기반 방문 저조 시간대 파악, 참여 가게 동시 할인 이벤트 진행",
    effect: "데이터 기반 매출 편차 완화 및 소상공인 자원 효율화",
  },
  {
    icon: Video,
    title: "SNS 릴레이 챌린지",
    description: "인접 가게 간 바통 터치 형식의 짧은 영상 콘텐츠로 해시태그 챌린지 확산",
    effect: "저비용 마케팅 및 상권 전체 온라인 노출 증가",
  },
];

const DISTRICT_STEPS = [
  "우리 상권 데이터를 불러오는 중이에요",
  "주변 상권 지도를 그리는 중이에요",
];

function haversineM(a: { lat: number; lng: number }, b: { lat: number; lng: number }): number {
  const R = 6_371_000;
  const dLat = ((b.lat - a.lat) * Math.PI) / 180;
  const dLng = ((b.lng - a.lng) * Math.PI) / 180;
  const s =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((a.lat * Math.PI) / 180) * Math.cos((b.lat * Math.PI) / 180) * Math.sin(dLng / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(s), Math.sqrt(1 - s));
}

function formatDistance(m: number | null | undefined): string {
  if (m == null) return "-";
  return m < 1000 ? `도보 ${m}m` : `도보 ${(m / 1000).toFixed(1)}km`;
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

const FUNDING_GOAL = 3_000_000;
const FUNDING_RAISED = 2_040_000; // 데모용 더미 진행률(68%)
const FUNDING_DDAY = 9;

const COMMUNITY_TEMPLATES = [
  { text: "스탬프 투어 언제부터 시작하나요? 저희 가게도 얼른 참여하고 싶어요!", time: "3시간 전" },
  { text: "펀딩 벌써 68%나 모였네요, 다들 홍보 감사합니다 🙌", time: "5시간 전" },
  { text: "유휴시간대 타임세일은 평일 오후 2~4시 어떠세요? 저희는 그때가 제일 한산해요", time: "어제" },
  { text: "SNS 릴레이 챌린지 해시태그 정했나요? 다음 주자로 저희 가게 지목해주세요!", time: "어제" },
  { text: "구독 패스에 세탁소 쿠폰도 들어가나요? 상권 전체가 같이 하면 좋을 것 같아요", time: "2일 전" },
];

const COMMUNITY_AVATAR_COLORS = ["#6D5BD0", "#F97316", "#22C55E", "#0EA5E9", "#EC4899"];

export function District() {
  const { districtId } = useParams<{ districtId: string }>();
  const [district, setDistrict] = useState<DistrictResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<"map" | "nearby">("map");
  const [fundingJoined, setFundingJoined] = useState(false);
  const [communityOpen, setCommunityOpen] = useState(false);

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

  const communityPosts = useMemo(() => {
    const names = (district?.member_pins ?? []).map((m) => m.상호명).filter(Boolean);
    return COMMUNITY_TEMPLATES.map((t, i) => ({
      ...t,
      store: names.length ? names[i % names.length] : `상권 이웃 ${i + 1}`,
      color: COMMUNITY_AVATAR_COLORS[i % COMMUNITY_AVATAR_COLORS.length],
    }));
  }, [district]);

  if (error) return <p className="district-error">{error}</p>;
  if (!district) return <LoadingState steps={DISTRICT_STEPS} />;

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
        <>
          {clusters.filter((c) => !c.is_ours).length === 0 && (
            <Card className="district-nearby-placeholder">
              <p>도보권 내에 비교할 주변 상권이 아직 없습니다.</p>
            </Card>
          )}
          {clusters
            .filter((c) => !c.is_ours)
            .map((c, i) => (
              <Card key={i} className="district-nearby-card">
                <div className="district-nearby-head">
                  <h3>{c.name ?? c.label}</h3>
                </div>
                {!!c.tags?.length && (
                  <div className="district-nearby-tags">
                    {c.tags.map((t) => (
                      <span key={t} className="district-nearby-tag">{t}</span>
                    ))}
                  </div>
                )}
                <dl className="district-nearby-detail">
                  <dt>주요 업종</dt>
                  <dd>{c.main_categories || "-"}</dd>
                  <dt>대표 분위기</dt>
                  <dd>{c.mood || "-"}</dd>
                  <dt>방문 특징</dt>
                  <dd>{c.visitor_feature || "-"}</dd>
                </dl>
                <div className="district-nearby-meta">
                  <span>
                    <Store size={13} strokeWidth={2} /> {c.member_pins.length}개 매장
                  </span>
                  <span>
                    <Footprints size={13} strokeWidth={2} /> {formatDistance(c.distance_m)}
                  </span>
                </div>
              </Card>
            ))}
        </>
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

      <h4 className="district-section-title">상권 네트워킹 프로그램</h4>
      {NETWORKING_PROGRAMS.map((p, i) => (
        <Card key={i} className="district-strategy-card">
          <div className="district-strategy-head">
            <div className="district-strategy-title-group">
              <span className="district-strategy-icon">
                <p.icon size={15} strokeWidth={2} />
              </span>
              <h5>{p.title}</h5>
            </div>
            <span className="district-strategy-badge">네트워킹</span>
          </div>
          <p>{p.description}</p>
          <span className="district-strategy-effect">↗ {p.effect}</span>
        </Card>
      ))}

      <h4 className="district-section-title">상권 공동 펀딩</h4>
      <Card className="district-funding-card">
        <div className="district-funding-head">
          <span className="district-funding-icon">
            <PiggyBank size={18} strokeWidth={2} />
          </span>
          <div>
            <h5>상권 공동 펀딩</h5>
            <p>"상권 통합 스탬프 투어" 실행을 위한 공동 자금 모집</p>
          </div>
        </div>

        <div className="district-funding-bar">
          <div
            className="district-funding-bar-fill"
            style={{ width: `${Math.round((FUNDING_RAISED / FUNDING_GOAL) * 100)}%` }}
          />
        </div>
        <div className="district-funding-amounts">
          <span className="district-funding-raised">{FUNDING_RAISED.toLocaleString()}원</span>
          <span className="district-funding-goal">/ {FUNDING_GOAL.toLocaleString()}원 목표</span>
        </div>

        <div className="district-funding-meta">
          <span>참여 가게 {district.member_count}곳</span>
          <span>D-{FUNDING_DDAY}</span>
        </div>

        <div className="district-funding-actions">
          <button
            className={"district-funding-btn" + (fundingJoined ? " joined" : "")}
            disabled={fundingJoined}
            onClick={() => setFundingJoined(true)}
          >
            {fundingJoined ? "펀딩 참여 완료" : "펀딩 참여하기"}
          </button>
          <button
            className={"district-community-btn" + (communityOpen ? " active" : "")}
            onClick={() => setCommunityOpen((v) => !v)}
          >
            <MessageCircle size={15} strokeWidth={2} /> 소통하기
          </button>
        </div>
      </Card>

      {communityOpen && (
        <Card className="district-community-card">
          <h5 className="district-community-title">상권 이웃들의 이야기</h5>
          {communityPosts.map((post, i) => (
            <div key={i} className="community-post">
              <span className="community-post-avatar" style={{ background: post.color }}>
                {post.store.slice(0, 1)}
              </span>
              <div className="community-post-body">
                <div className="community-post-head">
                  <strong>{post.store}</strong>
                  <span>{post.time}</span>
                </div>
                <p>{post.text}</p>
              </div>
            </div>
          ))}
        </Card>
      )}
    </div>
  );
}
