import { useEffect, useState } from "react";
import { SCREEN_COPY } from "./constants/screenCopy";
import { SajuSessionProvider, useSajuSession } from "./context/SajuSessionContext";
import { ApiConnectionBanner } from "./components/ApiConnectionBanner";
import { SajuInputScreen } from "./components/SajuInputScreen";
import { ReportPage } from "./components/ReportPage";
import { CounselCorner } from "./counsel/CounselCorner";
import { hasStoredBirth } from "./services/userMemoryStorage";
import { fetchSajuReport } from "./services/reportApi";
import "./app.css";

function AppShell() {
  const { birth, setBirth, reportData, setReportData } = useSajuSession();
  const [tab, setTab] = useState<"input" | "report" | "counsel">(() =>
    typeof window !== "undefined" && hasStoredBirth() ? "report" : "input"
  );
  const [reportLoading, setReportLoading] = useState(false);
  const [reportError, setReportError] = useState<string | null>(null);

  useEffect(() => {
    document.title = `UNTEIM · ${SCREEN_COPY.home.title}`;
  }, []);

  const createReport = async () => {
    if (!birth) return;
    try {
      setReportLoading(true);
      setReportError(null);
      const data = await fetchSajuReport(birth);
      setReportData(data);
    } catch (err) {
      setReportError(err instanceof Error ? err.message : "리포트 생성 중 오류가 발생했습니다.");
      setReportData(null);
    } finally {
      setReportLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <div className="app-shell__blob" aria-hidden />
      <ApiConnectionBanner />
      <nav className="app-shell__nav" aria-label="화면 전환">
        <button
          type="button"
          className={`app-shell__tab${tab === "input" ? " app-shell__tab--on" : ""}`}
          onClick={() => setTab("input")}
        >
          사주 입력
        </button>
        <button
          type="button"
          className={`app-shell__tab${tab === "report" ? " app-shell__tab--on" : ""}`}
          onClick={() => setTab("report")}
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
        {tab === "input" ? (
          <SajuInputScreen
            onSubmit={async (p) => {
              setBirth(p);
              setTab("report");
              setReportError(null);
              setReportLoading(true);
              try {
                const data = await fetchSajuReport(p);
                setReportData(data);
              } catch (err) {
                setReportError(err instanceof Error ? err.message : "리포트 생성 중 오류가 발생했습니다.");
                setReportData(null);
              } finally {
                setReportLoading(false);
              }
            }}
          />
        ) : tab === "report" ? (
          <ReportPage
            birth={birth}
            report={reportData}
            loading={reportLoading}
            error={reportError}
            onRetry={createReport}
            onGoCounsel={() => setTab("counsel")}
          />
        ) : (
          <CounselCorner />
        )}
      </main>
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
