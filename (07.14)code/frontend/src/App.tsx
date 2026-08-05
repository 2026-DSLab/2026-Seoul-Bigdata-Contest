import type { ReactNode } from "react";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { AppStateProvider, useAppState } from "./state/AppState";
import { BottomNav } from "./components/BottomNav";
import { Home } from "./pages/Home";
import { Diagnosis } from "./pages/Diagnosis";
import { DiagnosisResult } from "./pages/DiagnosisResult";
import { Recommendations } from "./pages/Recommendations";
import { District } from "./pages/District";
import { MyDistrictRedirect, ComingSoon, Profile } from "./pages/Placeholder";
import { Login } from "./pages/Login";

function RequireAuth({ children }: { children: ReactNode }) {
  const { isLoggedIn } = useAppState();
  const location = useLocation();

  if (!isLoggedIn) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }
  return <>{children}</>;
}

function AppShell() {
  const { isLoggedIn } = useAppState();

  return (
    <div className="app-shell">
      <div className="app-notch-spacer" />
      <div className="app-content">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<RequireAuth><Home /></RequireAuth>} />
          <Route path="/diagnosis" element={<RequireAuth><Diagnosis /></RequireAuth>} />
          <Route path="/diagnosis/result" element={<RequireAuth><DiagnosisResult /></RequireAuth>} />
          <Route path="/recommendations" element={<RequireAuth><Recommendations /></RequireAuth>} />
          <Route path="/district/:districtId" element={<RequireAuth><District /></RequireAuth>} />
          <Route path="/my-district" element={<RequireAuth><MyDistrictRedirect /></RequireAuth>} />
          <Route path="/market" element={<RequireAuth><ComingSoon title="솔루션 마켓" /></RequireAuth>} />
          <Route path="/profile" element={<RequireAuth><Profile /></RequireAuth>} />
        </Routes>
      </div>
      {isLoggedIn && <BottomNav />}
    </div>
  );
}

function App() {
  return (
    <AppStateProvider>
      <BrowserRouter>
        <AppShell />
      </BrowserRouter>
    </AppStateProvider>
  );
}

export default App;
