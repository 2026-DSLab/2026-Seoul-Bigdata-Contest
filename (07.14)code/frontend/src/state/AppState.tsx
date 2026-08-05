import { createContext, useContext, useState, type ReactNode } from "react";
import type { AnalyzeResponse, RecommendationCard } from "../api/types";

interface AppStateValue {
  analysis: AnalyzeResponse | null;
  setAnalysis: (a: AnalyzeResponse | null) => void;
  selectedDistrict: RecommendationCard | null;
  setSelectedDistrict: (d: RecommendationCard | null) => void;
  districtId: string | null;
  setDistrictId: (id: string | null) => void;
  isLoggedIn: boolean;
  userEmail: string | null;
  login: (email: string) => void;
  logout: () => void;
}

const AppStateContext = createContext<AppStateValue | null>(null);

const AUTH_STORAGE_KEY = "sangkwon_auth_email";
const analysisStorageKey = (email: string) => `sangkwon_last_analysis_${email}`;

interface StoredAnalysis {
  analysis: AnalyzeResponse | null;
  selectedDistrict: RecommendationCard | null;
  districtId: string | null;
}

const EMPTY_STORED: StoredAnalysis = { analysis: null, selectedDistrict: null, districtId: null };

function loadStoredAnalysis(email: string | null): StoredAnalysis {
  if (!email) return EMPTY_STORED;
  try {
    const raw = localStorage.getItem(analysisStorageKey(email));
    return raw ? { ...EMPTY_STORED, ...JSON.parse(raw) } : EMPTY_STORED;
  } catch {
    return EMPTY_STORED;
  }
}

export function AppStateProvider({ children }: { children: ReactNode }) {
  const [userEmail, setUserEmail] = useState<string | null>(() =>
    localStorage.getItem(AUTH_STORAGE_KEY)
  );
  const initialStored = loadStoredAnalysis(userEmail);
  const [analysis, setAnalysisState] = useState<AnalyzeResponse | null>(initialStored.analysis);
  const [selectedDistrict, setSelectedDistrictState] = useState<RecommendationCard | null>(
    initialStored.selectedDistrict
  );
  const [districtId, setDistrictIdState] = useState<string | null>(initialStored.districtId);

  const persist = (patch: Partial<StoredAnalysis>) => {
    if (!userEmail) return;
    const merged = { ...loadStoredAnalysis(userEmail), ...patch };
    localStorage.setItem(analysisStorageKey(userEmail), JSON.stringify(merged));
  };

  const setAnalysis = (a: AnalyzeResponse | null) => {
    setAnalysisState(a);
    persist({ analysis: a });
  };

  const setSelectedDistrict = (d: RecommendationCard | null) => {
    setSelectedDistrictState(d);
    persist({ selectedDistrict: d });
  };

  const setDistrictId = (id: string | null) => {
    setDistrictIdState(id);
    persist({ districtId: id });
  };

  const login = (email: string) => {
    localStorage.setItem(AUTH_STORAGE_KEY, email);
    setUserEmail(email);
    const stored = loadStoredAnalysis(email);
    setAnalysisState(stored.analysis);
    setSelectedDistrictState(stored.selectedDistrict);
    setDistrictIdState(stored.districtId);
  };

  const logout = () => {
    localStorage.removeItem(AUTH_STORAGE_KEY);
    setUserEmail(null);
    setAnalysisState(null);
    setSelectedDistrictState(null);
    setDistrictIdState(null);
  };

  return (
    <AppStateContext.Provider
      value={{
        analysis,
        setAnalysis,
        selectedDistrict,
        setSelectedDistrict,
        districtId,
        setDistrictId,
        isLoggedIn: userEmail !== null,
        userEmail,
        login,
        logout,
      }}
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
