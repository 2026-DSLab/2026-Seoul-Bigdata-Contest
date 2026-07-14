import { useNavigate } from "react-router-dom";
import { useAppState } from "../state/AppState";

export function MyDistrictRedirect() {
  const navigate = useNavigate();
  const { districtId } = useAppState();

  if (districtId) {
    navigate(`/district/${districtId}`, { replace: true });
    return null;
  }

  return (
    <div style={{ textAlign: "center", marginTop: 60, color: "var(--color-text-muted)" }}>
      <p>아직 확정된 상권이 없습니다.</p>
      <button
        style={{
          marginTop: 14, padding: "10px 18px", border: "none",
          borderRadius: "var(--radius-md)", background: "var(--color-primary)",
          color: "#fff", fontWeight: 700, cursor: "pointer",
        }}
        onClick={() => navigate("/diagnosis")}
      >
        MBTI 진단부터 시작하기
      </button>
    </div>
  );
}

export function ComingSoon({ title }: { title: string }) {
  return (
    <div style={{ textAlign: "center", marginTop: 60, color: "var(--color-text-muted)" }}>
      <p>{title} 기능은 준비 중입니다.</p>
    </div>
  );
}
