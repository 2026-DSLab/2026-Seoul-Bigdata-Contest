import { NavLink } from "react-router-dom";
import { Home, Users, Store, User } from "lucide-react";
import "./BottomNav.css";

const TABS = [
  { to: "/", label: "홈", Icon: Home, end: true },
  { to: "/my-district", label: "우리 상권+", Icon: Users, end: false },
  { to: "/market", label: "솔루션 마켓", Icon: Store, end: false },
  { to: "/profile", label: "내 정보", Icon: User, end: false },
];

export function BottomNav() {
  return (
    <nav className="bottomnav">
      {TABS.map(({ to, label, Icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          className={({ isActive }) => "bottomnav-item" + (isActive ? " active" : "")}
        >
          <Icon size={22} strokeWidth={1.8} className="bottomnav-icon" />
          <span className="bottomnav-label">{label}</span>
        </NavLink>
      ))}
    </nav>
  );
}
