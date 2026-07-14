import type {
  AnalyzeRequest,
  AnalyzeResponse,
  RecommendationsResponse,
  DistrictResponse,
} from "./types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API 요청 실패 (${res.status}): ${path}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  analyze: (body: AnalyzeRequest) =>
    request<AnalyzeResponse>("/api/analyze", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  getStore: (storeId: number) => request(`/api/stores/${storeId}`),

  getRecommendations: (storeId: number) =>
    request<RecommendationsResponse>(`/api/stores/${storeId}/recommendations`),

  joinDistrict: (
    storeId: number,
    body: { district_id: string; district_label: string; member_store_ids: number[] }
  ) =>
    request(`/api/stores/${storeId}/join-district`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  getDistrict: (districtId: string) =>
    request<DistrictResponse>(`/api/districts/${districtId}`),
};
