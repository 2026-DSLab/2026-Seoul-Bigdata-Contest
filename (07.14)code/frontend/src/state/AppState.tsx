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

export function AppStateProvider({ children }: { children: ReactNode }) {
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);
  const [selectedDistrict, setSelectedDistrict] = useState<RecommendationCard | null>(null);
  const [districtId, setDistrictId] = useState<string | null>(null);
  const [userEmail, setUserEmail] = useState<string | null>(() =>
    localStorage.getItem(AUTH_STORAGE_KEY)
  );

  const login = (email: string) => {
    localStorage.setItem(AUTH_STORAGE_KEY, email);
    setUserEmail(email);
  };

  const logout = () => {
    localStorage.removeItem(AUTH_STORAGE_KEY);
    setUserEmail(null);
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
