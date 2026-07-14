export interface MbtiAxis {
  axis: string;
  letter_left: string;
  letter_right: string;
  label_left: string;
  label_right: string;
  pct_left: number;
  pct_right: number;
}

export interface Mbti {
  code: string;
  axes: MbtiAxis[];
}

export interface AnalyzeRequest {
  상호명: string;
  구: string;
  동: string;
  업종_카테고리: string;
  운영_요일: string;
  오픈_시간: string;
  마감_시간: string;
  시그니쳐_상품: string;
  분위기: string;
  고민_사항: string;
  주고객_연령층: string;
  주고객_성별: string;
  extra?: Record<string, unknown>;
}

export interface AnalyzeResponse {
  store_id: number;
  mbti: Mbti;
  reports: Record<string, string>;
}

export interface BrandingStrategy {
  title: string;
  description: string;
  effect: string;
}

export interface MemberPin {
  id: number;
  상호명: string;
  lat: number | null;
  lng: number | null;
  mbti_code: string;
  업종_카테고리: string;
}

export interface RecommendationCard {
  district_id: string | null;
  label: string;
  tags: string[];
  main_categories: string;
  mood: string;
  visitor_feature: string;
  strategies: BrandingStrategy[];
  mbti_code: string;
  similarity: number;
  member_store_ids: number[];
  member_count: number;
  polygon: [number, number][];
  member_pins: MemberPin[];
}

export interface RecommendationsResponse {
  status: "ok" | "insufficient_data";
  message?: string;
  recommendations: RecommendationCard[];
}

export interface AreaCluster {
  label: string;
  is_ours: boolean;
  mbti_code: string;
  polygon: [number, number][];
  member_pins: MemberPin[];
}

export interface DistrictResponse {
  district_id: string;
  label: string;
  polygon: [number, number][];
  clusters: AreaCluster[];
  member_pins: MemberPin[];
  member_count: number;
  tags: string[];
  main_categories: string;
  strategies: BrandingStrategy[];
}
