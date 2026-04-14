import { useCallback, useState } from "react";
import type { FeedNavigateMeta, FeedTabTarget } from "@/types/contentFeed";
import { useSajuSession } from "@/context/SajuSessionContext";
import { EXPLORE_HUB_SECTIONS } from "@/data/exploreHubSections";
import { ContentFeedPage } from "@/components/feed/ContentFeedPage";
import { exploreActionForCategoryId } from "@/utils/exploreCategory";
import { SajuGateModal } from "./SajuGateModal";
import "./exploreHub.css";

type Props = {
  hasBirth: boolean;
  hasReport: boolean;
  onNavigateTab: (tab: FeedTabTarget, meta?: FeedNavigateMeta) => void;
  /** 사주 입력 탭 */
  onOpenSajuInput: () => void;
  /** 로그인·저장 사주로 리포트 탭 — 탐색 카테고리별 월 포커스·앵커 메타 */
  onOpenSavedReportFlow: (meta?: FeedNavigateMeta) => void | Promise<void>;
  /** 로그인·회원가입 모달 열기 */
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
  const { canUseSavedSajuContent, sessionEmail } = useSajuSession();
  const [gateOpen, setGateOpen] = useState(false);
  const [navigating, setNavigating] = useState(false);

  const runCategoryAction = useCallback(
    async (categoryId: string) => {
      if (!canUseSavedSajuContent) {
        setGateOpen(true);
        return;
      }
      const act = exploreActionForCategoryId(categoryId);
      try {
        setNavigating(true);
        if (act.type === "input") {
          onOpenSajuInput();
          return;
        }
        if (act.type === "counsel") {
          if (!hasBirth) {
            setGateOpen(true);
            return;
          }
          if (!hasReport) {
            await onOpenSavedReportFlow(undefined);
          }
          onNavigateTab("counsel");
          return;
        }
        await onOpenSavedReportFlow(act.meta);
      } finally {
        setNavigating(false);
      }
    },
    [canUseSavedSajuContent, hasBirth, hasReport, onNavigateTab, onOpenSavedReportFlow, onOpenSajuInput],
  );

  return (
    <>
      <div className={`explore-hub${navigating ? " explore-hub--busy" : ""}`}>
        {navigating ? (
          <div className="explore-hub__loading" role="status" aria-live="polite">
            <div className="explore-hub__loading-inner">
              <span className="explore-hub__spinner" aria-hidden />
              <span>리포트를 불러오는 중…</span>
            </div>
          </div>
        ) : null}
        <header className="explore-hub__hero">
          <h1 className="explore-hub__hero-title">탐색</h1>
          <p className="explore-hub__hero-sub">
            주제를 고르면 저장된 사주와 오늘 날짜 기준으로 맞춤 화면(월운·섹션)으로 이동합니다. 로그인·사주 저장이
            필요합니다.
          </p>
        </header>

        {EXPLORE_HUB_SECTIONS.map((section) => (
          <section key={section.id} className="explore-hub__section" aria-labelledby={`hub-sec-${section.id}`}>
            <p className="explore-hub__eyebrow">{section.eyebrow}</p>
            <h2 id={`hub-sec-${section.id}`} className="explore-hub__sec-title">
              {section.title}
            </h2>

            {section.layout === "grid3" && (
              <div className="explore-hub__grid3">
                {section.items.map((it) => (
                  <button
                    key={it.id}
                    type="button"
                    className="explore-hub__grid3-btn"
                    onClick={() => runCategoryAction(it.id)}
                  >
                    <span className="explore-hub__grid3-ico" aria-hidden>
                      {it.icon}
                    </span>
                    <span className="explore-hub__grid3-label">{it.label}</span>
                  </button>
                ))}
              </div>
            )}

            {section.layout === "list" && (
              <div className="explore-hub__list">
                {section.items.map((it) => (
                  <button
                    key={it.id}
                    type="button"
                    className="explore-hub__list-btn"
                    onClick={() => runCategoryAction(it.id)}
                  >
                    <span className="explore-hub__list-ico-wrap" aria-hidden>
                      {it.icon}
                    </span>
                    <span className="explore-hub__list-text">
                      <span className="explore-hub__list-title">
                        {it.label}
                        {it.badge === "new" && <span className="explore-hub__badge">NEW</span>}
                        {it.badge === "beta" && <span className="explore-hub__badge">β</span>}
                      </span>
                      {it.description ? <p className="explore-hub__list-desc">{it.description}</p> : null}
                    </span>
                  </button>
                ))}
              </div>
            )}

            {section.layout === "grid2" && (
              <div className="explore-hub__grid2">
                {section.items.map((it) => (
                  <button
                    key={it.id}
                    type="button"
                    className="explore-hub__grid2-btn"
                    onClick={() => runCategoryAction(it.id)}
                  >
                    <span className="explore-hub__grid2-ico" aria-hidden>
                      {it.icon}
                    </span>
                    <span className="explore-hub__grid2-title">
                      {it.label}
                      {it.badge === "new" && (
                        <span className="explore-hub__badge explore-hub__badge--inline">
                          NEW
                        </span>
                      )}
                      {it.badge === "beta" && (
                        <span className="explore-hub__badge explore-hub__badge--inline">
                          β
                        </span>
                      )}
                    </span>
                    {it.description ? <p className="explore-hub__grid2-desc">{it.description}</p> : null}
                  </button>
                ))}
              </div>
            )}
          </section>
        ))}

        <div className="explore-hub__feed-wrap">
          <h2 className="explore-hub__feed-heading">코칭 카드</h2>
          <p className="explore-hub__feed-lead">월별로 갱신되는 카드입니다. 카드를 누르면 안내 모달이 열립니다.</p>
          <ContentFeedPage
            embedded
            hasBirth={hasBirth}
            hasReport={hasReport}
            onNavigateTab={onNavigateTab}
          />
        </div>
      </div>

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
