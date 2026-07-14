import { Bell, Search, User } from "lucide-react";
import logoFull from "../assets/logo-full.png";
import "./TopBar.css";

interface TopBarProps {
  onSearch?: (value: string) => void;
  showSearch?: boolean;
}

export function TopBar({ onSearch, showSearch = true }: TopBarProps) {
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
      {showSearch && (
        <div className="topbar-search">
          <input
            placeholder="찾으시는 상권명을 입력하세요"
            onChange={(e) => onSearch?.(e.target.value)}
          />
          <Search size={16} strokeWidth={2} color="var(--color-text-faint)" />
        </div>
      )}
    </div>
  );
}
