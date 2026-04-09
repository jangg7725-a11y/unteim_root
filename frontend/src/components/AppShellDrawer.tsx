import { useEffect, useId } from "react";
import { useSajuSession } from "@/context/SajuSessionContext";
import type { BirthInputPayload } from "@/types/birthInput";
import "./app-shell-drawer.css";

export type AppShellTab = "explore" | "input" | "report" | "counsel";

type Props = {
  open: boolean;
  onClose: () => void;
  tab: AppShellTab;
  onSelectTab: (t: AppShellTab) => void;
};

function formatBirthLine(birth: BirthInputPayload) {
  const g = birth.gender === "male" ? "남" : "여";
  return `${birth.date} · ${birth.time} · ${g}`;
}

export function AppShellDrawer({ open, onClose, tab, onSelectTab }: Props) {
  const { birth, reportData } = useSajuSession();
  const titleId = useId();

  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  const hasBirth = Boolean(birth?.date && birth?.time && birth?.gender);
  const canReport = hasBirth;
  const canCounsel = hasBirth && !!reportData;

  const go = (t: AppShellTab) => {
    onSelectTab(t);
    onClose();
  };

  return (
    <div className="app-drawer" role="dialog" aria-modal="true" aria-labelledby={titleId}>
      <button type="button" className="app-drawer__backdrop" aria-label="메뉴 닫기" onClick={onClose} />
      <div className="app-drawer__panel">
        <div className="app-drawer__profile">
          <div className="app-drawer__avatar" aria-hidden />
          <div className="app-drawer__profile-main">
            <p id={titleId} className="app-drawer__profile-title">
              {hasBirth ? "사주 정보 연결됨" : "로그인"}
            </p>
            {hasBirth && birth ? (
              <>
                <p className="app-drawer__profile-sub">{formatBirthLine(birth)}</p>
                <p className="app-drawer__profile-hint">
                  이 기기에 저장되어 있습니다. 탐색·리포트·상담에서 같은 정보로 이용할 수 있어요.
                </p>
                <button type="button" className="app-drawer__primary" onClick={() => go("input")}>
                  정보 수정
                </button>
              </>
            ) : (
              <>
                <p className="app-drawer__profile-hint">
                  사주 정보를 한 번 입력·저장하면 모든 카테고리에서 다시 입력하지 않아도 됩니다.
                </p>
                <button type="button" className="app-drawer__primary" onClick={() => go("input")}>
                  사주 정보 입력하기
                </button>
              </>
            )}
          </div>
        </div>

        <hr className="app-drawer__rule" />

        <nav className="app-drawer__nav" aria-label="메뉴">
          <button
            type="button"
            className={`app-drawer__item${tab === "explore" ? " app-drawer__item--on" : ""}`}
            onClick={() => go("explore")}
          >
            탐색
          </button>
          <button
            type="button"
            className={`app-drawer__item${tab === "input" ? " app-drawer__item--on" : ""}`}
            onClick={() => go("input")}
          >
            사주 입력
          </button>
          <button
            type="button"
            className={`app-drawer__item${tab === "report" ? " app-drawer__item--on" : ""}`}
            disabled={!canReport}
            onClick={() => canReport && go("report")}
          >
            사주 리포트
            {!canReport && <span className="app-drawer__item-note"> (입력 후)</span>}
          </button>
          <button
            type="button"
            className={`app-drawer__item${tab === "counsel" ? " app-drawer__item--on" : ""}`}
            disabled={!canCounsel}
            onClick={() => canCounsel && go("counsel")}
          >
            AI 상담
            {!canCounsel && <span className="app-drawer__item-note"> (리포트 후)</span>}
          </button>
        </nav>

        <hr className="app-drawer__rule" />

        <div className="app-drawer__footer">
          <p className="app-drawer__footer-text">UNTEIM · 이 기기 브라우저에 안전하게 저장됩니다.</p>
        </div>
      </div>
    </div>
  );
}
