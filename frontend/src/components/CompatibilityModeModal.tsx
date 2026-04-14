import { useEffect, useId, useRef } from "react";
import "./compatibility-mode-modal.css";

type Props = {
  open: boolean;
  onClose: () => void;
  /** 상대 생년 입력(기존 궁합) */
  onChooseWithPartner: () => void;
  /** 본인만 — 썸/예측 해석 */
  onChooseSolo: () => void;
};

export function CompatibilityModeModal({ open, onClose, onChooseWithPartner, onChooseSolo }: Props) {
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
    <div className="compat-mode__backdrop" role="presentation">
      <button type="button" className="compat-mode__clickout" aria-label="닫기" onClick={onClose} />
      <div className="compat-mode" role="dialog" aria-modal="true" aria-labelledby={titleId}>
        <header className="compat-mode__head">
          <h3 id={titleId} className="compat-mode__title">
            궁합·연애 보기 방식
          </h3>
          <button ref={closeRef} type="button" className="compat-mode__close" onClick={onClose} aria-label="닫기">
            ×
          </button>
        </header>
        <p className="compat-mode__lead">
          상대 생년을 알고 있으면 두 사람 비교 궁합을, 썸 단계처럼 모를 때는 본인 사주만으로 인연 흐름 참고를 볼 수
          있습니다.
        </p>
        <div className="compat-mode__choices">
          <button type="button" className="compat-mode__choice compat-mode__choice--primary" onClick={onChooseWithPartner}>
            <span className="compat-mode__choice-title">상대 정보 있음</span>
            <span className="compat-mode__choice-desc">생년월일·시간을 넣고 두 사람 궁합을 봅니다.</span>
          </button>
          <button type="button" className="compat-mode__choice" onClick={onChooseSolo}>
            <span className="compat-mode__choice-title">상대 정보 없이 보기 (썸·예측)</span>
            <span className="compat-mode__choice-desc">본인 원국만으로 인연·감정 흐름 참고 문장을 봅니다.</span>
          </button>
        </div>
        <p className="compat-mode__fine" role="note">
          두 방식 모두 먼저 사주 기반 텍스트를 보여 주며, AI 상담은 선택 시에만 이어질 수 있습니다.
        </p>
      </div>
    </div>
  );
}
