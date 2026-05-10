// frontend/src/components/DailyReturnBanner.tsx
// 재방문 사용자에게 "오늘 운세가 도착했어요!" 배너 표시

import "./daily-return-banner.css";

type Props = {
  /** 마지막 방문일 (없으면 null) */
  lastVisitDate?: string | null;
  /** 오늘의 운세 보기 클릭 */
  onViewFortune: () => void;
  /** 배너 닫기 */
  onDismiss: () => void;
};

function formatLastVisit(dateStr: string | null | undefined): string {
  if (!dateStr) return "오랜만이에요";
  try {
    const d = new Date(dateStr);
    const month = d.getMonth() + 1;
    const day = d.getDate();
    return `${month}월 ${day}일 이후 처음이네요`;
  } catch {
    return "오랜만이에요";
  }
}

export function DailyReturnBanner({ lastVisitDate, onViewFortune, onDismiss }: Props) {
  const visitLabel = formatLastVisit(lastVisitDate);

  return (
    <aside className="daily-banner" role="status" aria-live="polite">
      <div className="daily-banner__inner">
        <div className="daily-banner__icon" aria-hidden>🌅</div>
        <div className="daily-banner__content">
          <p className="daily-banner__greeting">
            어서 오세요! <span className="daily-banner__visit">{visitLabel}</span>
          </p>
          <p className="daily-banner__sub">오늘의 운세가 준비됐어요.</p>
        </div>
        <div className="daily-banner__actions">
          <button
            className="daily-banner__btn daily-banner__btn--primary"
            onClick={onViewFortune}
          >
            오늘 운세 보기
          </button>
          <button
            className="daily-banner__btn daily-banner__btn--close"
            onClick={onDismiss}
            aria-label="닫기"
          >
            ✕
          </button>
        </div>
      </div>
    </aside>
  );
}
