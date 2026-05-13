import { Fragment, useCallback, useMemo, useState } from "react";
import type { FeedNavigateMeta, FeedTabTarget } from "@/types/contentFeed";
import { useSajuSession } from "@/context/SajuSessionContext";
import { EXPLORE_HUB_SECTIONS, type ExploreHubItem } from "@/data/exploreHubSections";
import { exploreActionForCategoryId } from "@/utils/exploreCategory";
import { deriveTodayPoint, type TodayPointResult } from "@/utils/deriveTodayPoint";
import { deriveTodayFortuneFromReport } from "@/utils/reportTodayCard";
import { TodayFortuneCard } from "@/components/TodayFortuneCard";
import { MicroPointOfferFlow } from "@/components/MicroPointOfferFlow";
import { TodayPointSheet } from "./TodayPointSheet";
import { SajuGateModal } from "./SajuGateModal";
import "./exploreHub.css";

/** flow 섹션(사주로 알아보는 나의 오늘) 항목 — 클릭 시 바텀시트 표시 */
const FLOW_SHEET_IDS = new Set(["m2", "m3", "m4", "m5", "m6", "m7", "m8", "m9", "m10"]);

type SheetState = {
  item: ExploreHubItem;
  point: TodayPointResult | null;
  detailMeta?: FeedNavigateMeta;
};

type Props = {
  hasBirth: boolean;
  hasReport: boolean;
  onNavigateTab: (tab: FeedTabTarget, meta?: FeedNavigateMeta) => void;
  onOpenSajuInput: () => void;
  onOpenSavedReportFlow: (meta?: FeedNavigateMeta) => void | Promise<void>;
  onOpenAuth: () => void;
};

export function ExploreHubPage({
  hasBirth,
  hasReport,
  onNavigateTab,
  onOpenSajuInput,
  onOpenSavedReportFlow,
  onOpenAuth,
}: Props) {
  const { sessionEmail, reportData, birth } = useSajuSession();
  const todayFortuneData = useMemo(() => deriveTodayFortuneFromReport(reportData ?? null), [reportData]);
  const [gateOpen, setGateOpen] = useState(false);
  const [navigating, setNavigating] = useState(false);
  const [sheet, setSheet] = useState<SheetState | null>(null);

  const handleMicroPointCounsel = useCallback(async () => {
    if (!hasReport) {
      try {
        setNavigating(true);
        await onOpenSavedReportFlow(undefined);
      } finally {
        setNavigating(false);
      }
    }
    onNavigateTab("counsel");
  }, [hasReport, onOpenSavedReportFlow, onNavigateTab]);

  /** flow 섹션 항목 클릭 → 바텀시트 */
  const openTodaySheet = useCallback(
    (item: ExploreHubItem) => {
      if (!hasBirth) { setGateOpen(true); return; }
      const point = hasReport ? deriveTodayPoint(item.id, reportData) : null;
      const act = exploreActionForCategoryId(item.id);
      setSheet({ item, point, detailMeta: act.type === "report" ? act.meta : undefined });
    },
    [hasBirth, hasReport, reportData],
  );

  const handleSheetDetail = useCallback(async () => {
    if (!sheet) return;
    setSheet(null);
    try { setNavigating(true); await onOpenSavedReportFlow(sheet.detailMeta); }
    finally { setNavigating(false); }
  }, [sheet, onOpenSavedReportFlow]);

  const handleSheetCounsel = useCallback(async () => {
    setSheet(null);
    if (!hasReport) {
      try { setNavigating(true); await onOpenSavedReportFlow(undefined); }
      finally { setNavigating(false); }
    }
    onNavigateTab("counsel");
  }, [hasReport, onOpenSavedReportFlow, onNavigateTab]);

  const handleSheetStartAnalysis = useCallback(async () => {
    setSheet(null);
    try { setNavigating(true); await onOpenSavedReportFlow(undefined); }
    finally { setNavigating(false); }
  }, [onOpenSavedReportFlow]);

  /** life·quick 섹션 항목 클릭 → 기존 리포트/탭 이동 */
  const runCategoryAction = useCallback(
    async (categoryId: string) => {
      if (!hasBirth) { setGateOpen(true); return; }
      const act = exploreActionForCategoryId(categoryId);
      try {
        setNavigating(true);
        if (act.type === "input") { onOpenSajuInput(); return; }
        if (act.type === "counsel") {
          if (!hasReport) await onOpenSavedReportFlow(undefined);
          onNavigateTab("counsel");
          return;
        }
        await onOpenSavedReportFlow(act.meta);
      } finally { setNavigating(false); }
    },
    [hasBirth, hasReport, onNavigateTab, onOpenSavedReportFlow, onOpenSajuInput],
  );

  /** 아이템 클릭 핸들러 — ID에 따라 sheet / navigation 분기 */
  const handleItemClick = useCallback(
    (item: ExploreHubItem) => {
      if (FLOW_SHEET_IDS.has(item.id)) {
        openTodaySheet(item);
      } else {
        runCategoryAction(item.id);
      }
    },
    [openTodaySheet, runCategoryAction],
  );

  return (
    <>
      <div className={`explore-hub${navigating ? " explore-hub--busy" : ""}`}>
        {navigating && (
          <div className="explore-hub__loading" role="status" aria-live="polite">
            <div className="explore-hub__loading-inner">
              <span className="explore-hub__spinner" aria-hidden />
              <span>리포트를 불러오는 중…</span>
            </div>
          </div>
        )}

        <header className="explore-hub__hero">
          <h1 className="explore-hub__hero-title">탐색</h1>
          <p className="explore-hub__hero-sub">
            주제를 고르면 입력해 둔 사주와 오늘 날짜 기준으로 맞춤 화면(월운·섹션)으로 이동합니다. 사주는 한 번
            입력해 두면 탐색으로 나갔다 와도 같은 정보로 이어집니다.
          </p>
        </header>

        <section className="explore-hub__today-card-wrap" aria-label="사주로알아보는 나의오늘">
          <p className="explore-hub__today-card-eyebrow">사주로 알아보는 나의 오늘</p>
          <TodayFortuneCard data={todayFortuneData ?? undefined} supplementaryLine={null} />
        </section>

        {EXPLORE_HUB_SECTIONS.map((section) => (
          <Fragment key={section.id}>
            <section
              className={`explore-hub__section${section.layout === "action" ? " explore-hub__section--action" : ""}`}
              aria-labelledby={`hub-sec-${section.id}`}
            >
            <p className="explore-hub__eyebrow">{section.eyebrow}</p>
            <h2 id={`hub-sec-${section.id}`} className="explore-hub__sec-title">
              {section.title}
            </h2>

            {/* ── 카드 레이아웃 (2열 그라데이션) ── */}
            {section.layout === "cards" && (
              <div className="explore-hub__cards">
                {section.items.map((it) => (
                  <button
                    key={it.id}
                    type="button"
                    className="explore-hub__card-btn"
                    onClick={() => handleItemClick(it)}
                  >
                    <div
                      className={`explore-hub__card-banner explore-hub__card-banner--${it.theme ?? "violet"}`}
                    >
                      {it.areaLabel && (
                        <span className="explore-hub__card-area">{it.areaLabel}</span>
                      )}
                      <span className="explore-hub__card-ico" aria-hidden="true">{it.icon}</span>
                      <span className="explore-hub__card-label">
                        {it.label}
                        {it.badge === "beta" && (
                          <span className="explore-hub__card-badge">β</span>
                        )}
                        {it.badge === "new" && (
                          <span className="explore-hub__card-badge">NEW</span>
                        )}
                      </span>
                    </div>
                    {it.description && (
                      <div className="explore-hub__card-body">
                        <p className="explore-hub__card-desc">{it.description}</p>
                      </div>
                    )}
                  </button>
                ))}
              </div>
            )}

            {/* ── action 레이아웃 (바로 가기 — 1열 4줄 가로형) ── */}
            {section.layout === "action" && (
              <div className="explore-hub__action">
                {section.items.map((it) => (
                  <button
                    key={it.id}
                    type="button"
                    className={`explore-hub__action-btn explore-hub__action-btn--${it.theme ?? "violet"}`}
                    onClick={() => handleItemClick(it)}
                  >
                    {/* 좌: 아이콘 블록 */}
                    <span className="explore-hub__action-ico" aria-hidden="true">{it.icon}</span>

                    {/* 우: 4줄 텍스트 */}
                    <span className="explore-hub__action-text">
                      {it.areaLabel && (
                        <span className="explore-hub__action-area">{it.areaLabel}</span>
                      )}
                      <span className="explore-hub__action-label">
                        {it.label}
                        {it.badge === "beta" && <span className="explore-hub__action-badge">β</span>}
                        {it.badge === "new"  && <span className="explore-hub__action-badge">NEW</span>}
                      </span>
                      {it.description && (
                        <p className="explore-hub__action-desc">{it.description}</p>
                      )}
                    </span>

                    {/* 우측 화살표 */}
                    <span className="explore-hub__action-arrow" aria-hidden="true">›</span>
                  </button>
                ))}
              </div>
            )}

            {/* ── 3열 그리드 (레거시용 유지) ── */}
            {section.layout === "grid3" && (
              <div className="explore-hub__grid3">
                {section.items.map((it) => (
                  <button
                    key={it.id}
                    type="button"
                    className="explore-hub__grid3-btn"
                    onClick={() => handleItemClick(it)}
                  >
                    <span className="explore-hub__grid3-ico" aria-hidden>{it.icon}</span>
                    <span className="explore-hub__grid3-label">{it.label}</span>
                    {it.description && <p className="explore-hub__grid3-desc">{it.description}</p>}
                  </button>
                ))}
              </div>
            )}

            {/* ── 리스트 ── */}
            {section.layout === "list" && (
              <div className="explore-hub__list">
                {section.items.map((it) => (
                  <button
                    key={it.id}
                    type="button"
                    className="explore-hub__list-btn"
                    onClick={() => handleItemClick(it)}
                  >
                    <span className="explore-hub__list-ico-wrap" aria-hidden>{it.icon}</span>
                    <span className="explore-hub__list-text">
                      <span className="explore-hub__list-title">
                        {it.label}
                        {it.badge === "new" && <span className="explore-hub__badge">NEW</span>}
                        {it.badge === "beta" && <span className="explore-hub__badge">β</span>}
                      </span>
                      {it.description && <p className="explore-hub__list-desc">{it.description}</p>}
                    </span>
                    <span className="explore-hub__list-arrow" aria-hidden>›</span>
                  </button>
                ))}
              </div>
            )}

            {/* ── 2열 카드 (레거시) ── */}
            {section.layout === "grid2" && (
              <div className="explore-hub__grid2">
                {section.items.map((it) => (
                  <button
                    key={it.id}
                    type="button"
                    className="explore-hub__grid2-btn"
                    onClick={() => handleItemClick(it)}
                  >
                    <span className="explore-hub__grid2-ico" aria-hidden>{it.icon}</span>
                    <span className="explore-hub__grid2-title">
                      {it.label}
                      {it.badge === "new" && <span className="explore-hub__badge explore-hub__badge--inline">NEW</span>}
                      {it.badge === "beta" && <span className="explore-hub__badge explore-hub__badge--inline">β</span>}
                    </span>
                    {it.description && <p className="explore-hub__grid2-desc">{it.description}</p>}
                  </button>
                ))}
              </div>
            )}

          </section>
            {section.id === "life" ? (
              <div className="explore-hub__micro-flow">
                <MicroPointOfferFlow birth={birth} onGoCounsel={handleMicroPointCounsel} />
              </div>
            ) : null}
          </Fragment>
        ))}
      </div>

      {sheet && (
        <TodayPointSheet
          item={sheet.item}
          point={sheet.point}
          hasReport={hasReport}
          onClose={() => setSheet(null)}
          onDetail={handleSheetDetail}
          onCounsel={handleSheetCounsel}
          onStartAnalysis={handleSheetStartAnalysis}
        />
      )}

      <SajuGateModal
        open={gateOpen}
        onClose={() => setGateOpen(false)}
        onStartSaju={onOpenSajuInput}
        onOpenAuth={onOpenAuth}
        sessionEmail={sessionEmail}
      />
    </>
  );
}
