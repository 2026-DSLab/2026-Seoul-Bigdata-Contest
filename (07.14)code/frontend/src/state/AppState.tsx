import { createContext, useContext, useState, type ReactNode } from "react";
import type { AnalyzeResponse, RecommendationCard } from "../api/types";

interface AppStateValue {
  analysis: AnalyzeResponse | null;
  setAnalysis: (a: AnalyzeResponse | null) => void;
  selectedDistrict: RecommendationCard | null;
  setSelectedDistrict: (d: RecommendationCard | null) => void;
  districtId: string | null;
  setDistrictId: (id: string | null) => void;
}

const AppStateContext = createContext<AppStateValue | null>(null);

export function AppStateProvider({ children }: { children: ReactNode }) {
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);
  const [selectedDistrict, setSelectedDistrict] = useState<RecommendationCard | null>(null);
  const [districtId, setDistrictId] = useState<string | null>(null);

  return (
    <AppStateContext.Provider
      value={{ analysis, setAnalysis, selectedDistrict, setSelectedDistrict, districtId, setDistrictId }}
    >
      {children}
    </AppStateContext.Provider>
  );
}

export function useAppState(): AppStateValue {
  const ctx = useContext(AppStateContext);
  if (!ctx) throw new Error("useAppState must be used within AppStateProvider");
  return ctx;
}
