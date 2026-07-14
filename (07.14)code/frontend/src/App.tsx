import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AppStateProvider } from "./state/AppState";
import { BottomNav } from "./components/BottomNav";
import { Home } from "./pages/Home";
import { Diagnosis } from "./pages/Diagnosis";
import { DiagnosisResult } from "./pages/DiagnosisResult";
import { Recommendations } from "./pages/Recommendations";
import { District } from "./pages/District";
import { MyDistrictRedirect, ComingSoon } from "./pages/Placeholder";

function App() {
  return (
    <AppStateProvider>
      <BrowserRouter>
        <div className="app-shell">
          <div className="app-content">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/diagnosis" element={<Diagnosis />} />
              <Route path="/diagnosis/result" element={<DiagnosisResult />} />
              <Route path="/recommendations" element={<Recommendations />} />
              <Route path="/district/:districtId" element={<District />} />
              <Route path="/my-district" element={<MyDistrictRedirect />} />
              <Route path="/market" element={<ComingSoon title="솔루션 마켓" />} />
              <Route path="/profile" element={<ComingSoon title="내 정보" />} />
            </Routes>
          </div>
          <BottomNav />
        </div>
      </BrowserRouter>
    </AppStateProvider>
  );
}

export default App;
