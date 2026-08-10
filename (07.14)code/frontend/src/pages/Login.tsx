import { useState, type FormEvent } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { useAppState } from "../state/AppState";
import logoFull from "../assets/logo-full.png";
import "./Login.css";

export function Login() {
  const { isLoggedIn, login } = useAppState();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  if (isLoggedIn) {
    return <Navigate to="/" replace />;
  }

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password.trim()) {
      setError("이메일과 비밀번호를 입력해주세요.");
      return;
    }
    login(email.trim());
    const from = (location.state as { from?: string } | null)?.from ?? "/";
    navigate(from, { replace: true });
  };

  return (
    <div className="login-page">
      <img src={logoFull} alt="상권더하기" className="login-logo" />
      <p className="login-subtitle">로그인하고 우리 가게 상권 분석을 시작해보세요</p>

      <form className="login-form" onSubmit={handleSubmit}>
        <label htmlFor="login-email">이메일</label>
        <input
          id="login-email"
          type="email"
          placeholder="example@email.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        <label htmlFor="login-password">비밀번호</label>
        <input
          id="login-password"
          type="password"
          placeholder="비밀번호를 입력하세요"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        {error && <p className="login-error">{error}</p>}

        <button type="submit" className="login-submit">
          로그인
        </button>
      </form>
    </div>
  );
}
