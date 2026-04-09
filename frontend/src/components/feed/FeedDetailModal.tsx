import { useEffect, useId } from "react";
import type { FeedItem, FeedNavigateMeta, FeedTabTarget } from "@/types/contentFeed";
import "./feed.css";

type Props = {
  item: FeedItem | null;
  open: boolean;
  onClose: () => void;
  onGoTab: (target: FeedTabTarget, meta?: FeedNavigateMeta) => void;
  hasBirth: boolean;
  hasReport: boolean;
};

function primaryLabel(action: FeedItem["action"]): string {
  if (action.type !== "tab") return "닫기";
  switch (action.target) {
    case "input":
      return "사주 입력하러 가기";
    case "report":
      return "사주 리포트 보기";
    case "counsel":
      return "AI 상담으로 이동";
    default:
      return "이동";
  }
}

export function FeedDetailModal({ item, open, onClose, onGoTab, hasBirth, hasReport }: Props) {
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

  if (!open || !item) return null;

  const act = item.action;
  const canDo =
    act.type === "none" ||
    (act.type === "tab" && act.target === "input") ||
    (act.type === "tab" && act.target === "report" && hasBirth) ||
    (act.type === "tab" && act.target === "counsel" && hasBirth && hasReport);

  const blockedReason =
    act.type === "tab" && act.target === "report" && !hasBirth
      ? "먼저 사주 입력을 완료해 주세요."
      : act.type === "tab" && act.target === "counsel" && (!hasBirth || !hasReport)
        ? "사주 입력 후 리포트를 생성하면 AI 상담을 이용할 수 있습니다."
        : null;

  const tabMeta = (): FeedNavigateMeta | undefined => {
    if (act.type !== "tab") return undefined;
    const fm = act.focusMonth;
    if (typeof fm === "number" && fm >= 1 && fm <= 12) return { focusMonth: fm };
    return undefined;
  };

  const onPrimary = () => {
    if (act.type === "tab" && canDo) {
      onGoTab(act.target, tabMeta());
      onClose();
    }
  };

  const needsBirthForAction =
    act.type === "tab" && (act.target === "report" || act.target === "counsel") && !hasBirth;
  const needsReportForCounsel = act.type === "tab" && act.target === "counsel" && hasBirth && !hasReport;

  return (
    <div className="feed-modal-overlay" role="presentation" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="feed-modal" role="dialog" aria-modal="true" aria-labelledby={titleId}>
        <div className="feed-modal__head">
          <h2 id={titleId} className="feed-modal__title">
            {item.title}
          </h2>
          <button type="button" className="feed-modal__close" onClick={onClose} aria-label="닫기">
            ×
          </button>
        </div>
        <p className="feed-modal__body">{item.description}</p>
        <div className="feed-modal__actions">
          {act.type === "tab" && (
            <>
              <button
                type="button"
                className="feed-modal__btn feed-modal__btn--primary"
                onClick={onPrimary}
                disabled={!canDo}
              >
                {primaryLabel(act)}
              </button>
              {needsBirthForAction && (
                <button
                  type="button"
                  className="feed-modal__btn feed-modal__btn--secondary"
                  onClick={() => {
                    onGoTab("input", tabMeta());
                    onClose();
                  }}
                >
                  사주 입력하러 가기
                </button>
              )}
              {needsReportForCounsel && (
                <button
                  type="button"
                  className="feed-modal__btn feed-modal__btn--secondary"
                  onClick={() => {
                    onGoTab("report");
                    onClose();
                  }}
                >
                  사주 리포트 만들기
                </button>
              )}
              {blockedReason && <p className="feed-modal__hint">{blockedReason}</p>}
            </>
          )}
          {act.type === "none" && (
            <button type="button" className="feed-modal__btn feed-modal__btn--secondary" onClick={onClose}>
              닫기
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
