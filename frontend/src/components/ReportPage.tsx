import { useEffect, useMemo, useRef, useState } from "react";
import type { BirthInputPayload } from "@/types/birthInput";
import type { SajuReportData } from "@/types/report";
import type { FortuneLinesData } from "@/types/fortuneLines";
import { SCREEN_COPY } from "@/constants/screenCopy";
import { loadFortuneLines } from "@/services/fortuneLinesApi";
import { pickFortuneLineForReport } from "@/utils/pickFortuneLine";
import { formatKoreanDisplayDate } from "@/utils/formatKoreanDate";
import { MonthlyFortuneEngine } from "./MonthlyFortuneEngine";
import { AICounselPreview } from "./AICounselPreview";
import { RelationFortuneCard } from "./RelationFortuneCard";
import { RiskCautionCard } from "./RiskCautionCard";
import "./report-page.css";

type Props = {
  birth: BirthInputPayload | null;
  report: SajuReportData | null;
  loading: boolean;
  analyzeWaitSec?: number | null;
  error: string | null;
  onRetry: () => void;
  onGoCounsel: () => void;
  /** 피드 등에서 지정한 달만 월운 먼저 표시 — null이면 12개월 넘기기 */
  monthFocus: number | null;
  onClearMonthFocus: () => void;
  /** 탐색 등에서 지정한 섹션으로 스크롤 — 적용 후 onConsumedScrollAnchor 호출 */
  scrollAnchor?: string | null;
  onConsumedScrollAnchor?: () => void;
};

export function ReportPage({
  birth,
  report,
  loading,
  analyzeWaitSec = null,
  error,
  onRetry,
  onGoCounsel,
  monthFocus,
  onClearMonthFocus,
  scrollAnchor,
  onConsumedScrollAnchor,
}: Props) {
  const [fortuneLines, setFortuneLines] = useState<FortuneLinesData | null>(null);
  const consumedAnchorRef = useRef<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    loadFortuneLines().then((d) => {
      if (!cancelled) setFortuneLines(d);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!scrollAnchor) {
      consumedAnchorRef.current = null;
      return;
    }
    if (!report) return;
    const t = window.setTimeout(() => {
      const el = document.getElementById(scrollAnchor);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "start" });
        consumedAnchorRef.current = scrollAnchor;
        onConsumedScrollAnchor?.();
      }
    }, 160);
    return () => window.clearTimeout(t);
  }, [scrollAnchor, report, onConsumedScrollAnchor]);

  const reportFortune = useMemo(() => {
    if (!birth) return null;
    const raw = report?.raw ?? null;
    return {
      monthlyIntro: pickFortuneLineForReport("monthlyIntro", fortuneLines, birth, raw),
    };
  }, [birth, fortuneLines, report?.raw]);

  const outputDateLine = formatKoreanDisplayDate();

  return (
    <div className="report-page">
      <header className="report-page__head">
        <h1 className="report-page__lead">{SCREEN_COPY.output.subtitle}</h1>
        {!loading && !error && report ? (
          <p className="report-page__output-date" role="note">
            출력일 {outputDateLine}
          </p>
        ) : null}
      </header>

      {loading && (
        <div className="report-page__state" role="status">
          <p className="report-page__state-line">사주 리포트를 생성하고 있습니다…</p>
          {typeof analyzeWaitSec === "number" ? (
            <p className="report-page__state-line report-page__state-wait" aria-live="polite">
              서버 분석 경과: <strong>{analyzeWaitSec}</strong>초 — 연결이 끊기지 않았다면 계속 진행 중입니다.
            </p>
          ) : null}
          <p className="report-page__state-line report-page__state-hint">
            서버 상태에 따라 분석에 시간이 걸릴 수 있습니다. 이 탭을 닫지 말고 잠시만 기다려 주세요.
          </p>
        </div>
      )}

      {!loading && error && (
        <div className="report-page__error" role="alert">
          <p>{error}</p>
          <button type="button" className="report-page__retry" onClick={onRetry}>
            리포트 다시 생성
          </button>
        </div>
      )}

      {!loading && !error && report && (
        <>
          {report.monthlyFortune && report.monthlyFortune.months.length > 0 && !report.monthlyFortune.error ? (
            <div id="report-anchor-monthly">
              <MonthlyFortuneEngine
                data={report.monthlyFortune}
                onGoCounsel={onGoCounsel}
                monthFocus={monthFocus}
                onShowFullYear={onClearMonthFocus}
                supplementaryIntroLine={reportFortune?.monthlyIntro ?? null}
                narrativeSlots={report.narrativeSlots}
              />
            </div>
          ) : (
            <div id="report-anchor-monthly" className="report-page__card" aria-live="polite">
              <h3 className="report-page__card-title">월별 운세</h3>
              {reportFortune?.monthlyIntro ? (
                <div className="report-page__fortune-aside report-page__fortune-aside--block" role="note">
                  <span className="report-page__fortune-label">참고 한 줄 · 월운 흐름</span>
                  <p className="report-page__fortune-text">{reportFortune.monthlyIntro}</p>
                </div>
              ) : null}
              <p className="report-page__card-text">
                엔진 기반 12개월 상세 리포트를 불러오지 못했습니다. 서버 분석 시간이 길어 중간에 끊기거나, 일시적인
                오류일 수 있습니다. 아래에서 다시 생성해 주세요. (짧은 데모 리포트로 대체하지 않습니다.)
              </p>
              {report.monthlyFortune?.error ? (
                <p className="report-page__compat-error" role="status">
                  {report.monthlyFortune.error}
                </p>
              ) : null}
              <button type="button" className="report-page__retry" onClick={onRetry}>
                월별 리포트 포함 전체 다시 생성
              </button>
            </div>
          )}

          <RelationFortuneCard narrativeSlots={report.narrativeSlots} />

          {!(
            report.monthlyFortune
            && report.monthlyFortune.months.length > 0
            && !report.monthlyFortune.error
          ) ? (
            <RiskCautionCard narrativeSlots={report.narrativeSlots} />
          ) : null}

          <AICounselPreview onClick={onGoCounsel} />
        </>
      )}

      {!loading && !error && !report && (
        <div className="report-page__state">
          <p className="report-page__empty">저장된 사주 정보로 아직 리포트를 만들지 않았습니다.</p>
          <button type="button" className="report-page__retry" onClick={onRetry}>
            리포트 생성하기
          </button>
        </div>
      )}
    </div>
  );
}
