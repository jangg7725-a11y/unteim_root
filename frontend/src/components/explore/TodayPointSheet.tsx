import type { ExploreHubItem } from "@/data/exploreHubSections";
import type { TodayPointResult } from "@/utils/deriveTodayPoint";
import "./TodayPointSheet.css";

type Props = {
  item: ExploreHubItem;
  point: TodayPointResult | null;
  /** 리포트에 분석 데이터가 있는지 여부 */
  hasReport: boolean;
  onClose: () => void;
  /** 자세히 보기 → 리포트 해당 섹션 */
  onDetail: () => void;
  /** AI 상담 하기 → 상담 탭 */
  onCounsel: () => void;
  /** 분석 시작 (리포트 없을 때) */
  onStartAnalysis: () => void;
};

export function TodayPointSheet({
  item,
  point,
  hasReport,
  onClose,
  onDetail,
  onCounsel,
  onStartAnalysis,
}: Props) {
  return (
    <div className="tp-sheet" role="dialog" aria-modal="true" aria-label={`${item.label} 오늘의 포인트`}>
      <button
        type="button"
        className="tp-sheet__backdrop"
        aria-label="닫기"
        onClick={onClose}
      />
      <div className="tp-sheet__panel">
        {/* 닫기 버튼 */}
        <button type="button" className="tp-sheet__close" aria-label="닫기" onClick={onClose}>
          ×
        </button>

        {/* 헤더 */}
        <div className="tp-sheet__header">
          <span className="tp-sheet__ico" aria-hidden="true">{item.icon}</span>
          <div className="tp-sheet__header-text">
            <p className="tp-sheet__eyebrow">오늘의 포인트</p>
            <h2 className="tp-sheet__title">{item.label}</h2>
          </div>
        </div>

        {/* 본문 */}
        <div className="tp-sheet__body">
          {point ? (
            <>
              <p className="tp-sheet__headline">{point.headline}</p>
              {point.sub ? <p className="tp-sheet__sub">{point.sub}</p> : null}
            </>
          ) : (
            <p className="tp-sheet__headline tp-sheet__headline--muted">
              사주 분석을 완료하면 오늘의 포인트를 확인할 수 있어요.
            </p>
          )}
        </div>

        {/* CTA 버튼 영역 */}
        <div className="tp-sheet__actions">
          {hasReport ? (
            <>
              <button type="button" className="tp-sheet__btn tp-sheet__btn--primary" onClick={onDetail}>
                <span className="tp-sheet__btn-ico" aria-hidden="true">📖</span>
                자세히 보기
              </button>
              <button type="button" className="tp-sheet__btn tp-sheet__btn--counsel" onClick={onCounsel}>
                <span className="tp-sheet__btn-ico" aria-hidden="true">💬</span>
                AI 상담 하기
                <span className="tp-sheet__premium-badge">프리미엄</span>
              </button>
            </>
          ) : (
            <>
              <button type="button" className="tp-sheet__btn tp-sheet__btn--primary" onClick={onStartAnalysis}>
                <span className="tp-sheet__btn-ico" aria-hidden="true">✨</span>
                분석 시작하기
              </button>
              <button type="button" className="tp-sheet__btn tp-sheet__btn--counsel" onClick={onCounsel}>
                <span className="tp-sheet__btn-ico" aria-hidden="true">💬</span>
                AI 상담 하기
                <span className="tp-sheet__premium-badge">프리미엄</span>
              </button>
            </>
          )}
        </div>

        {/* 유료 유도 한 줄 */}
        <p className="tp-sheet__upsell">
          더 깊은 해석과 맞춤 조언은 <strong>AI 상담</strong>에서 확인하세요.
        </p>
      </div>
    </div>
  );
}
