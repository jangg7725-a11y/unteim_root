import { useEffect, useId, useRef } from "react";

type Props = {
  open: boolean;
  onClose: () => void;
  /** 사주 입력 탭으로 이동 */
  onStartSaju: () => void;
  /** 로그인·회원가입 모달 */
  onOpenAuth: () => void;
  sessionEmail: string | null;
};

/**
 * 카테고리 진입 전 안내 — 엔진 분석과 별개의 안내 문구입니다.
 */
export function SajuGateModal({ open, onClose, onStartSaju, onOpenAuth, sessionEmail }: Props) {
  const titleId = useId();
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
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

  return (
    <div className="saju-gate" role="presentation">
      <button type="button" className="saju-gate__backdrop" aria-label="닫기" onClick={onClose} />
      <div
        className="saju-gate__panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
      >
        <button ref={closeRef} type="button" className="saju-gate__close" onClick={onClose} aria-label="닫기">
          ×
        </button>
        <h2 id={titleId} className="saju-gate__title">
          당신의 앞날이 궁금하다면?
        </h2>
        <p className="saju-gate__body">
          지금 사주정보를 입력하고 <strong>운트임</strong>에서 알아봐요!
          {!sessionEmail ? (
            <>
              <br />
              <span className="saju-gate__hint">
                회원가입·로그인하면 계정이 연결되고, 한 번 저장한 사주로 탐색 주제를 바로 열 수 있어요.
              </span>
            </>
          ) : null}
        </p>
        <div className="saju-gate__actions">
          <button
            type="button"
            className="saju-gate__btn saju-gate__btn--primary"
            onClick={() => {
              onClose();
              onStartSaju();
            }}
          >
            {sessionEmail ? "사주 입력 · 저장" : "운트임 시작하기"}
          </button>
          {!sessionEmail ? (
            <button
              type="button"
              className="saju-gate__btn saju-gate__btn--secondary"
              onClick={() => {
                onClose();
                onOpenAuth();
              }}
            >
              로그인 · 회원가입
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
}
