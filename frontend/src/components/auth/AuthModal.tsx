import { useEffect, useId, useRef, useState } from "react";
import { useSajuSession } from "@/context/SajuSessionContext";
import "./auth-modal.css";

type Props = {
  open: boolean;
  onClose: () => void;
};

type LoginKind = "email" | "phone";

export function AuthModal({ open, onClose }: Props) {
  const titleId = useId();
  const closeRef = useRef<HTMLButtonElement>(null);
  const { login, register } = useSajuSession();
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [loginKind, setLoginKind] = useState<LoginKind>("email");
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setMsg(null);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    closeRef.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = prev;
      window.removeEventListener("keydown", onKey);
    };
  }, [open, onClose]);

  if (!open) return null;

  const onRegister = () => {
    setMsg(null);
    const r = register(email, password, phone.trim() || undefined);
    if (r.ok) {
      onClose();
      return;
    }
    setMsg(r.message ?? "가입에 실패했습니다.");
  };

  const onLogin = () => {
    setMsg(null);
    const id = loginKind === "email" ? email.trim() : phone.trim();
    const r = login(id, password);
    if (r.ok) {
      onClose();
      return;
    }
    setMsg(r.message ?? "로그인에 실패했습니다.");
  };

  return (
    <div className="auth-modal" role="presentation">
      <button type="button" className="auth-modal__backdrop" aria-label="닫기" onClick={onClose} />
      <div className="auth-modal__panel" role="dialog" aria-modal="true" aria-labelledby={titleId}>
        <button ref={closeRef} type="button" className="auth-modal__close" onClick={onClose} aria-label="닫기">
          ×
        </button>
        <h2 id={titleId} className="auth-modal__title">
          회원가입 · 로그인
        </h2>
        <p className="auth-modal__lead">
          이 기기 브라우저에만 저장되는 데모입니다. <strong>로그인에 성공하면 가입 시 이메일로 본인이 자동 연결</strong>됩니다.
          실서비스에서는 서버 인증으로 교체하세요.
        </p>

        <fieldset className="auth-modal__segment">
          <legend className="auth-modal__legend">로그인 시 사용</legend>
          <div className="auth-modal__segment-btns" role="group" aria-label="로그인 방식">
            <button
              type="button"
              className={`auth-modal__seg${loginKind === "email" ? " auth-modal__seg--on" : ""}`}
              onClick={() => setLoginKind("email")}
            >
              이메일
            </button>
            <button
              type="button"
              className={`auth-modal__seg${loginKind === "phone" ? " auth-modal__seg--on" : ""}`}
              onClick={() => setLoginKind("phone")}
            >
              휴대폰 번호
            </button>
          </div>
        </fieldset>

        <label className="auth-modal__field">
          <span className="auth-modal__label">이메일 (회원가입 시 필수)</span>
          <input
            className="auth-modal__input"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
          />
        </label>

        <label className="auth-modal__field">
          <span className="auth-modal__label">
            휴대폰 번호 (회원가입 시 선택 · 등록 시 휴대폰 로그인 가능)
          </span>
          <input
            className="auth-modal__input"
            type="tel"
            inputMode="numeric"
            autoComplete="tel"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="01012345678"
          />
        </label>

        <label className="auth-modal__field">
          <span className="auth-modal__label">비밀번호 (4자 이상)</span>
          <input
            className="auth-modal__input"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>

        <p className="auth-modal__login-hint">
          {loginKind === "email"
            ? "로그인: 위 이메일과 비밀번호를 사용합니다."
            : "로그인: 가입 시 넣은 휴대폰 번호와 비밀번호를 사용합니다. (번호 미등록 계정은 이메일로 로그인)"}
        </p>

        {msg ? <p className="auth-modal__msg">{msg}</p> : null}
        <div className="auth-modal__actions">
          <button type="button" className="auth-modal__btn auth-modal__btn--primary" onClick={onLogin}>
            로그인
          </button>
          <button type="button" className="auth-modal__btn auth-modal__btn--secondary" onClick={onRegister}>
            회원가입
          </button>
        </div>
      </div>
    </div>
  );
}
