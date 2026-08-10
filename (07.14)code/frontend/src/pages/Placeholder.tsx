import { useNavigate } from "react-router-dom";
import { Users, Construction, User, LogOut } from "lucide-react";
import { Card } from "../components/Card";
import { useAppState } from "../state/AppState";
import "./Placeholder.css";

export function MyDistrictRedirect() {
  const navigate = useNavigate();
  const { districtId } = useAppState();

  if (districtId) {
    navigate(`/district/${districtId}`, { replace: true });
    return null;
  }

  return (
    <Card className="empty-state">
      <div className="empty-state-icon">
        <Users size={24} strokeWidth={2} />
      </div>
      <p className="empty-state-title">아직 확정된 상권이 없습니다</p>
      <p className="empty-state-desc">
        MBTI 진단을 먼저 진행하면
        <br />
        우리 가게와 잘 맞는 상권을 추천해드려요
      </p>
      <button className="empty-state-btn" onClick={() => navigate("/diagnosis")}>
        MBTI 진단부터 시작하기
      </button>
    </Card>
  );
}

export function ComingSoon({ title }: { title: string }) {
  return (
    <Card className="empty-state">
      <div className="empty-state-icon">
        <Construction size={24} strokeWidth={2} />
      </div>
      <p className="empty-state-title">{title}</p>
      <p className="empty-state-desc">더 나은 경험을 위해 준비 중이에요</p>
    </Card>
  );
}

export function Profile() {
  const navigate = useNavigate();
  const { userEmail, logout } = useAppState();

  return (
    <Card>
      <div className="profile-header">
        <div className="profile-avatar">
          <User size={24} strokeWidth={2} />
        </div>
        <div>
          <p className="profile-email">{userEmail}</p>
          <p className="profile-status">상권더하기 회원</p>
        </div>
      </div>

      <p className="profile-note">내 정보 관리 기능은 준비 중입니다</p>

      <button
        className="profile-logout-btn"
        onClick={() => {
          logout();
          navigate("/login", { replace: true });
        }}
      >
        <LogOut size={15} strokeWidth={2} style={{ verticalAlign: -2, marginRight: 6 }} />
        로그아웃
      </button>
    </Card>
  );
}
