import { useEffect, useRef, useState } from "react";
import { SajuSessionProvider, useSajuSession } from "./context/SajuSessionContext";
import { ApiConnectionBanner } from "./components/ApiConnectionBanner";
import { ProdApiMissingBanner } from "./components/ProdApiMissingBanner";
import { isProdBundleMissingApiBase } from "./services/apiBase";
import { SajuInputScreen } from "./components/SajuInputScreen";
import { ReportPage } from "./components/ReportPage";
import { CounselCorner } from "./counsel/CounselCorner";
import { AppShellDrawer } from "./components/AppShellDrawer";
import { AuthModal } from "./components/auth/AuthModal";
import { ExploreHubPage } from "./components/explore/ExploreHubPage";
import { PwaInstallHint } from "./components/PwaInstallHint";
import { DailyReturnBanner } from "./components/DailyReturnBanner";
import { useDailyReturnLoop } from "./hooks/useDailyReturnLoop";
import { hasStoredBirth } from "./services/userMemoryStorage";
import { fetchSajuReport } from "./services/reportApi";
import type { BirthInputPayload } from "./types/birthInput";
import type { FeedNavigateMeta, FeedTabTarget } from "./types/contentFeed";
import "./app.css";

function AppShell() {
  const { birth, setBirth, reportData, setReportData, resetSajuMemory } = useSajuSession();
  const [tab, setTab] = useState<"explore" | "input" | "report" | "counsel">(() =>
    typeof window !== "undefined" && hasStoredBirth() ? "report" : "explore"
  );
  const [reportLoading, setReportLoading] = useState(false);
  const [reportError, setReportError] = useState<string | null>(null);
  /** 리포트 생성 중 경과 초 — 멈춘 것처럼 보이지 않게 표시 */
  const [reportWaitSec, setReportWaitSec] = useState<number | null>(null);
  /** 피드·탐색의 focusMonth — 있으면 월운을 해당 달만 먼저 표시 */
  const [reportMonthFocus, setReportMonthFocus] = useState<number | null>(null);
  /** 리포트 탭에서 스크롤할 섹션 id */
  const [reportScrollAnchor, setReportScrollAnchor] = useState<string | null>(null);
  const feedMonthPendingRef = useRef<number | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [authOpen, setAuthOpen] = useState(false);

  // 재방문 루프 — 오늘 운세 알림
  const { showDailyBanner, dismissBanner, markFortuneSeen, lastVisitDate } = useDailyReturnLoop();

  const selectTabFromMenu = (t: "explore" | "input" | "report" | "counsel") => {
    if (t === "input") feedMonthPendingRef.current = null;
    if (t === "report") {
      feedMonthPendingRef.current = null;
      setReportMonthFocus(null);
      setReportScrollAnchor(null);
    }
    setTab(t);
  };

  useEffect(() => {
    const sub =
      tab === "explore"
        ? "탐색"
        : tab === "input"
          ? "사주 입력"
          : tab === "report"
            ? "사주 리포트"
            : "AI 상담";
    document.title = `UNTEIM · ${sub}`;
  }, [tab]);

  /** @returns 성공 여부 */
  const runFetchReport = async (payload: BirthInputPayload): Promise<boolean> => {
    setReportLoading(true);
    setReportError(null);
    setReportData(null);
    setReportWaitSec(0);
    const tick = window.setInterval(() => {
      setReportWaitSec((s) => (s == null ? 0 : s) + 1);
    }, 1000);
    let ok = false;
    try {
      const data = await fetchSajuReport(payload);
      setReportData(data);
      ok = true;
    } catch (err) {
      setReportError(err instanceof Error ? err.message : "리포트 생성 중 오류가 발생했습니다.");
      setReportData(null);
    } finally {
      window.clearInterval(tick);
      setReportLoading(false);
      setReportWaitSec(null);
    }
    return ok;
  };

  const createReport = async () => {
    if (!birth) return;
    await runFetchReport(birth);
  };

  return (
    <div className="app-shell">
      <div className="app-shell__blob" aria-hidden />
      <header className="app-shell__header">
        <span className="app-shell__brand">UNTEIM</span>
        <button
          type="button"
          className="app-shell__hamburger"
          aria-label="메뉴 열기"
          aria-expanded={drawerOpen}
          onClick={() => setDrawerOpen(true)}
        >
          <span className="app-shell__hamburger-line" aria-hidden />
          <span className="app-shell__hamburger-line" aria-hidden />
          <span className="app-shell__hamburger-line" aria-hidden />
        </button>
      </header>
      <ApiConnectionBanner />
      {isProdBundleMissingApiBase() ? <ProdApiMissingBanner /> : null}
      <nav className="app-shell__nav" aria-label="화면 전환">
        <button
          type="button"
          className={`app-shell__tab${tab === "explore" ? " app-shell__tab--on" : ""}`}
          onClick={() => setTab("explore")}
        >
          탐색
        </button>
        <button
          type="button"
          className={`app-shell__tab${tab === "input" ? " app-shell__tab--on" : ""}`}
          onClick={() => {
            feedMonthPendingRef.current = null;
            setTab("input");
          }}
        >
          사주 입력
        </button>
        <button
          type="button"
          className={`app-shell__tab${tab === "report" ? " app-shell__tab--on" : ""}`}
          onClick={() => {
            feedMonthPendingRef.current = null;
            setReportMonthFocus(null);
            setReportScrollAnchor(null);
            setTab("report");
          }}
          disabled={!birth}
        >
          사주 리포트
        </button>
        <button
          type="button"
          className={`app-shell__tab${tab === "counsel" ? " app-shell__tab--on" : ""}`}
          onClick={() => setTab("counsel")}
          disabled={!birth || !reportData}
        >
          AI 상담
        </button>
      </nav>
      <main className="app-shell__main">
        {tab === "explore" ? (
          <ExploreHubPage
            hasBirth={!!birth}
            hasReport={!!reportData}
            onOpenSajuInput={() => {
              feedMonthPendingRef.current = null;
              setTab("input");
            }}
            onOpenSavedReportFlow={async (meta) => {
              feedMonthPendingRef.current = null;
              const fm = meta?.focusMonth;
              if (typeof fm === "number" && fm >= 1 && fm <= 12) {
                setReportMonthFocus(fm);
              } else {
                setReportMonthFocus(null);
              }
              if (meta?.reportAnchor) {
                setReportScrollAnchor(meta.reportAnchor);
              } else {
                setReportScrollAnchor(null);
              }
              if (birth && !reportData) {
                await runFetchReport(birth);
              }
              setTab("report");
            }}
            onOpenAuth={() => setAuthOpen(true)}
            onNavigateTab={(target: FeedTabTarget, meta?: FeedNavigateMeta) => {
              const fm = meta?.focusMonth;
              if (target === "input") {
                if (typeof fm === "number" && fm >= 1 && fm <= 12) {
                  feedMonthPendingRef.current = fm;
                } else {
                  feedMonthPendingRef.current = null;
                }
                setTab("input");
              }
              if (target === "report") {
                feedMonthPendingRef.current = null;
                if (typeof fm === "number" && fm >= 1 && fm <= 12) {
                  setReportMonthFocus(fm);
                } else {
                  setReportMonthFocus(null);
                }
                if (meta?.reportAnchor) {
                  setReportScrollAnchor(meta.reportAnchor);
                } else {
                  setReportScrollAnchor(null);
                }
                setTab("report");
              }
              if (target === "counsel") {
                setTab("counsel");
              }
            }}
          />
        ) : tab === "input" ? (
          <SajuInputScreen
            birth={birth}
            report={reportData}
            loading={reportLoading}
            analyzeWaitSec={reportLoading ? reportWaitSec : null}
            error={reportError}
            onGoReport={() => setTab("report")}
            onResetSession={() => {
              resetSajuMemory();
              setReportError(null);
              setReportLoading(false);
              setReportWaitSec(null);
              setReportMonthFocus(null);
            }}
            onSubmit={async (p) => {
              setBirth(p);
              setReportError(null);
              const ok = await runFetchReport(p);
              if (ok) {
                const pm = feedMonthPendingRef.current;
                if (pm != null) {
                  setReportMonthFocus(pm);
                  feedMonthPendingRef.current = null;
                }
              }
            }}
          />
        ) : tab === "report" ? (
          <ReportPage
            birth={birth}
            report={reportData}
            loading={reportLoading}
            analyzeWaitSec={reportLoading ? reportWaitSec : null}
            error={reportError}
            onRetry={createReport}
            onGoCounsel={() => setTab("counsel")}
            monthFocus={reportMonthFocus}
            onClearMonthFocus={() => setReportMonthFocus(null)}
            scrollAnchor={reportScrollAnchor}
            onConsumedScrollAnchor={() => setReportScrollAnchor(null)}
          />
        ) : (
          <CounselCorner />
        )}
      </main>
      <AppShellDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        tab={tab}
        onSelectTab={selectTabFromMenu}
        onOpenAuth={() => setAuthOpen(true)}
      />
      <AuthModal open={authOpen} onClose={() => setAuthOpen(false)} />
      <PwaInstallHint />
      {showDailyBanner && (
        <DailyReturnBanner
          lastVisitDate={lastVisitDate}
          onViewFortune={() => { selectTabFromMenu("report"); markFortuneSeen(); }}
          onDismiss={dismissBanner}
        />
      )}
    </div>
  );
}

export default function App() {
  return (
    <SajuSessionProvider>
      <AppShell />
    </SajuSessionProvider>
  );
}
