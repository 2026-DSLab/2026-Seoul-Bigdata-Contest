import { Bell, User } from "lucide-react";
import logoFull from "../assets/logo-full.png";
import "./TopBar.css";

export function TopBar() {
  return (
    <div className="topbar">
      <div className="topbar-row">
        <div className="topbar-logo">
          <img src={logoFull} alt="상권더하기" className="topbar-logo-full" />
        </div>
        <div className="topbar-icons">
          <button className="topbar-icon-btn" aria-label="알림">
            <Bell size={18} strokeWidth={2} />
            <span className="topbar-badge">3</span>
          </button>
          <button className="topbar-icon-btn topbar-avatar" aria-label="내 정보">
            <User size={18} strokeWidth={2} />
          </button>
        </div>
      </div>
    </div>
  );
}
