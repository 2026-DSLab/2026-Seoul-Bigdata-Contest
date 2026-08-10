import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { AlertTriangle } from "lucide-react";
import { Card } from "../components/Card";
import { ChipSelect } from "../components/ChipSelect";
import { RangeSlider } from "../components/RangeSlider";
import { TextField } from "../components/TextField";
import { LoadingState } from "../components/LoadingState";
import { api } from "../api/client";
import { useAppState } from "../state/AppState";
import "./Diagnosis.css";

const CATEGORY_OPTIONS = [
  "외식/F&B", "식품/식재료", "생활서비스", "생활/홈인테리어", "의료/건강", "교육",
  "오락/여가", "숙박/부동산", "전문서비스", "전자/디지털", "자동차/이동수단", "패션/뷰티",
];

const ANALYZE_STEPS = [
  "가게 정보를 확인하고 있어요",
  "서울시 공공데이터를 조회하고 있어요",
  "AI가 상권을 분석하고 있어요",
  "우리 가게 MBTI를 계산하는 중이에요",
];

function moodDescription(
  activity: number,
  brightness: number,
  style: number,
  spaciousness: number,
  formality: number
): string {
  const a = activity >= 50 ? "활기찬" : "조용한";
  const b = brightness >= 50 ? "어둡고 무드있는" : "밝고 환한";
  const s = style >= 50 ? "화려한" : "심플한";
  const sp = spaciousness >= 50 ? "넓고 트인" : "아늑하고 좁은";
  const f = formality >= 50 ? "격식있는" : "편안하고 캐주얼한";
  return `${a}, ${b}, ${s}, ${sp}, ${f}`;
}

export function Diagnosis() {
  const navigate = useNavigate();
  const { setAnalysis } = useAppState();

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 기본 정보
  const [상호명, set상호명] = useState("");
  const [구, set구] = useState("");
  const [동, set동] = useState("");
  const [업종_카테고리, set업종_카테고리] = useState(CATEGORY_OPTIONS[0]);
  const [운영_요일, set운영_요일] = useState<string[]>(["주7일"]);
  const [오픈_시간, set오픈_시간] = useState("10:00");
  const [마감_시간, set마감_시간] = useState("22:00");
  const [시그니쳐_상품, set시그니쳐_상품] = useState("");
  const [주고객_연령층, set주고객_연령층] = useState<string[]>(["20대"]);
  const [주고객_성별, set주고객_성별] = useState<string[]>(["여성"]);

  // 추가 정보
  const [객단가, set객단가] = useState<string[]>(["1~2만원"]);
  const [가게_장점, set가게_장점] = useState("");
  const [활기, set활기] = useState(50);
  const [무드, set무드] = useState(50);
  const [화려함, set화려함] = useState(50);
  const [공간감, set공간감] = useState(50);
  const [격식, set격식] = useState(50);
  const [위협요인, set위협요인] = useState<string[]>([]);

  // 함께 성장하기
  const [브랜딩_의향, set브랜딩_의향] = useState<string[]>(["적극 관심"]);

  const validate = (): string | null => {
    const missing: string[] = [];
    if (!상호명.trim()) missing.push("상호명");
    if (!구.trim()) missing.push("구");
    if (!동.trim()) missing.push("동");
    if (!시그니쳐_상품.trim()) missing.push("시그니처 상품");
    if (missing.length > 0) {
      return `${missing.join(", ")}을(를) 입력해주세요.`;
    }
    return null;
  };

  const handleSubmit = async () => {
    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const 분위기 = moodDescription(활기, 무드, 화려함, 공간감, 격식);
      const 고민_사항 = 위협요인.length
        ? `최근 고민: ${위협요인.join(", ")}`
        : "특별한 고민사항은 없지만 매출 개선 방안이 궁금해요";

      const res = await api.analyze({
        상호명, 구, 동, 업종_카테고리,
        운영_요일: 운영_요일[0] ?? "주7일",
        오픈_시간, 마감_시간,
        시그니쳐_상품: 시그니쳐_상품 || 가게_장점,
        분위기,
        고민_사항,
        주고객_연령층: 주고객_연령층[0] ?? "20대",
        주고객_성별: 주고객_성별[0] === "혼합" ? "여성" : (주고객_성별[0] ?? "여성"),
        extra: { 객단가: 객단가[0], 가게_장점, 브랜딩_의향: 브랜딩_의향[0] },
      });
      setAnalysis(res);
      navigate("/diagnosis/result");
    } catch (e) {
      setError(e instanceof Error ? e.message : "분석 중 오류가 발생했습니다.");
    } finally {
      setSubmitting(false);
    }
  };

  if (submitting) {
    return (
      <div className="diagnosis">
        <h2 className="diagnosis-title">우리 가게 MBTI 진단</h2>
        <LoadingState steps={ANALYZE_STEPS} />
      </div>
    );
  }

  return (
    <div className="diagnosis">
      <h2 className="diagnosis-title">우리 가게 MBTI 진단</h2>

      <Card className="diagnosis-section">
        <h4>기본 정보 <span>우리 가게를 알려주세요</span></h4>

        <label>상호명 <em>*</em></label>
        <TextField value={상호명} onChange={(e) => set상호명(e.target.value)} placeholder="가게 이름을 입력하세요" />

        <label>위치 <em>*</em></label>
        <div className="diagnosis-row">
          <TextField value={구} onChange={(e) => set구(e.target.value)} placeholder="구 (예: 마포구)" />
          <TextField value={동} onChange={(e) => set동(e.target.value)} placeholder="동 (예: 서교동)" />
        </div>

        <label>업종 카테고리</label>
        <select value={업종_카테고리} onChange={(e) => set업종_카테고리(e.target.value)}>
          {CATEGORY_OPTIONS.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>

        <label>운영 요일</label>
        <ChipSelect options={["주5일", "주6일", "주7일"]} value={운영_요일} onChange={set운영_요일} />

        <label>운영 시간</label>
        <div className="diagnosis-row">
          <TextField value={오픈_시간} onChange={(e) => set오픈_시간(e.target.value)} placeholder="오픈시간" />
          <span className="diagnosis-tilde">~</span>
          <TextField value={마감_시간} onChange={(e) => set마감_시간(e.target.value)} placeholder="마감시간" />
        </div>

        <label>시그니처 상품 <em>*</em></label>
        <TextField value={시그니쳐_상품} onChange={(e) => set시그니쳐_상품(e.target.value)} placeholder="대표 메뉴를 입력하세요" />

        <label>주 고객층: 연령대</label>
        <ChipSelect options={["10대", "20대", "30대", "40대"]} value={주고객_연령층} onChange={set주고객_연령층} />

        <label>주 고객층: 성별</label>
        <ChipSelect options={["남성", "여성", "혼합"]} value={주고객_성별} onChange={set주고객_성별} />
      </Card>

      <Card className="diagnosis-section">
        <h4>추가 정보 <span>우리 가게의 상황을 알려주세요</span></h4>

        <label>객단가</label>
        <ChipSelect options={["1만원 이하", "1~2만원", "2만원 이상"]} value={객단가} onChange={set객단가} />

        <label>우리 가게의 장점</label>
        <TextField value={가게_장점} onChange={(e) => set가게_장점(e.target.value)} placeholder="예: 아인슈페너가 맛있기로 유명해요" />

        <label>가게 분위기 선택</label>
        <RangeSlider leftLabel="조용한" rightLabel="활기찬" value={활기} onChange={set활기} />
        <RangeSlider leftLabel="밝고 환한" rightLabel="어둡고 무드있는" value={무드} onChange={set무드} />
        <RangeSlider leftLabel="심플한" rightLabel="화려한" value={화려함} onChange={set화려함} />
        <RangeSlider leftLabel="아늑한" rightLabel="넓고 트인" value={공간감} onChange={set공간감} />
        <RangeSlider leftLabel="편안한" rightLabel="격식있는" value={격식} onChange={set격식} />

        <label>최근 가게 위협 요인 (복수 응답 가능)</label>
        <ChipSelect
          multi
          options={["임대료 상승", "인건비", "경쟁 심화", "단골 이탈", "온라인·배달 전환", "기타"]}
          value={위협요인}
          onChange={set위협요인}
        />
      </Card>

      <Card className="diagnosis-section">
        <h4>함께 성장하기 <span>상권 공동 브랜딩을 위해</span></h4>
        <label>상권 공동 브랜딩 의향</label>
        <ChipSelect options={["적극 관심", "조건부", "관심 없음"]} value={브랜딩_의향} onChange={set브랜딩_의향} />
      </Card>

      {error && (
        <p className="diagnosis-error">
          <AlertTriangle size={14} strokeWidth={2} /> {error}
        </p>
      )}

      <button className="diagnosis-submit" onClick={handleSubmit}>
        진단하기
      </button>
    </div>
  );
}
