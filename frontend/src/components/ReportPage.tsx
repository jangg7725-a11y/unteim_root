import { useEffect, useMemo, useRef, useState } from "react";
import type { BirthInputPayload } from "@/types/birthInput";
import type { SajuReportData } from "@/types/report";
import type { FortuneLinesData } from "@/types/fortuneLines";
import { SCREEN_COPY } from "@/constants/screenCopy";
import { loadFortuneLines } from "@/services/fortuneLinesApi";
import { pickFortuneLineForReport } from "@/utils/pickFortuneLine";
import { formatKoreanDisplayDate } from "@/utils/formatKoreanDate";
import { COMPAT_SCORE_LEGEND_LINES, starBandFrom100 } from "@/utils/compatibilityLabels";
import { MonthlyFortuneEngine } from "./MonthlyFortuneEngine";
import { MicroPointOffers } from "./MicroPointOffers";
import { PartnerInputModal } from "./PartnerInputModal";
import { MicroPointSingleModal } from "./MicroPointSingleModal";
import { AICounselPreview } from "./AICounselPreview";
import { RelationFortuneCard } from "./RelationFortuneCard";
import { RiskCautionCard } from "./RiskCautionCard";
import { postCompatibility, type CompatibilityResult } from "@/services/compatibilityApi";
import {
  postSoloLoveInsight,
  type SoloLoveInsightResult,
} from "@/services/soloLoveInsightApi";
import type { MicroPointOfferItem } from "@/data/microPointOffersMock";
import { CompatibilityModeModal } from "./CompatibilityModeModal";
import { SoloLoveResultModal } from "./SoloLoveResultModal";
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
  const [pairOpen, setPairOpen] = useState(false);
  const [compatibilityLoading, setCompatibilityLoading] = useState(false);
  const [compatibilityError, setCompatibilityError] = useState<string | null>(null);
  const [compatibility, setCompatibility] = useState<CompatibilityResult | null>(null);
  const [selectedQuestion, setSelectedQuestion] = useState<string | null>(null);
  const [singleOfferModal, setSingleOfferModal] = useState<MicroPointOfferItem | null>(null);
  const [loveModeOpen, setLoveModeOpen] = useState(false);
  const [soloOpen, setSoloOpen] = useState(false);
  const [soloData, setSoloData] = useState<SoloLoveInsightResult | null>(null);
  const [soloLoading, setSoloLoading] = useState(false);
  const [soloError, setSoloError] = useState<string | null>(null);
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

  const onSelectSingle = (item: MicroPointOfferItem) => {
    setSelectedQuestion(item.question);
    setCompatibility(null);
    setCompatibilityError(null);
    setSingleOfferModal(item);
  };

  const prefillCounsel = (text: string) => {
    try {
      sessionStorage.setItem("unteim_counsel_prefill", text);
    } catch {
      /* ignore */
    }
  };

  const runSoloLoveFromPair = async () => {
    if (!birth) return;
    setSoloLoading(true);
    setSoloError(null);
    setSoloData(null);
    try {
      const res = await postSoloLoveInsight(birth, "sseom");
      setSoloData(res);
      setSoloOpen(true);
    } catch (e) {
      setSoloError(e instanceof Error ? e.message : "인연 해석을 불러오지 못했습니다.");
      setSoloOpen(true);
    } finally {
      setSoloLoading(false);
    }
  };

  const onSelectPair = (item: MicroPointOfferItem) => {
    setSelectedQuestion(item.question);
    setCompatibility(null);
    setCompatibilityError(null);
    setLoveModeOpen(true);
  };

  const onSubmitPartner = async (partnerBirth: BirthInputPayload) => {
    if (!birth) {
      setCompatibilityError("내 사주 정보가 없어 궁합 분석을 진행할 수 없습니다.");
      return;
    }
    setCompatibilityLoading(true);
    setCompatibilityError(null);
    try {
      const result = await postCompatibility(birth, partnerBirth);
      setCompatibility(result);
      setPairOpen(false);
      // TODO: 추후 질문/결과 저장 API 연결
      console.log("[pair-question]", selectedQuestion, { birth, partnerBirth });
    } catch (e) {
      setCompatibilityError(e instanceof Error ? e.message : "궁합 분석 중 오류가 발생했습니다.");
    } finally {
      setCompatibilityLoading(false);
    }
  };

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

          {/* 인연운 카드 */}
          <RelationFortuneCard narrativeSlots={report.narrativeSlots} />

          {/* 월운 엔진이 없을 때만: 주의 패턴(월운 내부와 중복 방지) */}
          {!(
            report.monthlyFortune
            && report.monthlyFortune.months.length > 0
            && !report.monthlyFortune.error
          ) ? (
            <RiskCautionCard narrativeSlots={report.narrativeSlots} />
          ) : null}

          <MicroPointOffers onSelectSingle={onSelectSingle} onSelectPair={onSelectPair} />

          {compatibilityError && <p className="report-page__compat-error">{compatibilityError}</p>}
          {compatibility && (
            <section className="report-page__compat-card" aria-label="궁합 분석 결과">
              <h3 className="report-page__compat-title">궁합 분석 결과</h3>
              <div className="report-page__compat-scores">
                <p className="report-page__compat-score-line">
                  <strong>별점 {compatibility.score}/5점</strong>
                  <span className="report-page__compat-dim"> (5점 만점 · 표시용 단계)</span>
                </p>
                {compatibility.score100 != null ? (
                  <>
                    <p className="report-page__compat-score-line">
                      <strong>종합 지수 {Number(compatibility.score100).toFixed(1)}/100점</strong>
                      <span className="report-page__compat-dim"> (100점 만점 · 참고 수치)</span>
                    </p>
                    <p className="report-page__compat-band" role="note">
                      이 종합 지수 구간은{" "}
                      <strong>{starBandFrom100(Number(compatibility.score100)).hint}</strong>으로 볼 수 있습니다. (참고
                      가능성·경향이며, 단정적 판단이 아닙니다.)
                    </p>
                  </>
                ) : (
                  <p className="report-page__compat-band" role="note">
                    종합 지수(100점 만점)는 엔진이 두 사주의 오행·일간·지지·십신 패턴 등을 가중해 만든 참고용 점수입니다.
                  </p>
                )}
              </div>
              <details className="report-page__compat-details">
                <summary className="report-page__compat-summary">점수 의미 · 별점과 100점의 관계</summary>
                <div className="report-page__compat-legend-body">
                  <p>
                    <strong>~/100 표기</strong>는 &quot;종합 지수&quot;로, 엔진이 두 사람 원국을 바탕으로 오행 연결·일간
                    관계·십신 성향·지지 합충형해 등을 반영해 산출한 <strong>100점 만점 기준 참고 점수</strong>입니다.
                    절대적 좋음/나쁨을 보장하지 않으며, 관계 맥락에 따라 달라질 수 있습니다.
                  </p>
                  <p>
                    앞의 <strong>별점(1~5)</strong>은 이 종합 지수를 아래 구간으로 나눈 <strong>5단계 표시</strong>입니다.
                  </p>
                  <p className="report-page__compat-legend-rule">{COMPAT_SCORE_LEGEND_LINES[0]}</p>
                </div>
              </details>
              <p className="report-page__compat-line">{compatibility.summary}</p>
              <p className="report-page__compat-line"><strong>서로 끌리는 이유:</strong> {compatibility.attraction}</p>
              <p className="report-page__compat-line"><strong>갈등 포인트:</strong> {compatibility.conflict}</p>
              <p className="report-page__compat-line"><strong>오래 가는 조건:</strong> {compatibility.longevity}</p>
              <p className="report-page__compat-line"><strong>행동 가이드:</strong> {compatibility.guide}</p>
            </section>
          )}

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

      <CompatibilityModeModal
        open={loveModeOpen}
        onClose={() => setLoveModeOpen(false)}
        onChooseWithPartner={() => {
          setLoveModeOpen(false);
          setPairOpen(true);
        }}
        onChooseSolo={() => {
          setLoveModeOpen(false);
          runSoloLoveFromPair();
        }}
      />

      <PartnerInputModal
        open={pairOpen}
        loading={compatibilityLoading}
        error={compatibilityError}
        onClose={() => {
          setPairOpen(false);
          setCompatibilityError(null);
        }}
        onSubmit={onSubmitPartner}
      />

      <SoloLoveResultModal
        open={soloOpen}
        data={soloData}
        loading={soloLoading}
        error={soloError}
        onClose={() => {
          setSoloOpen(false);
          setSoloData(null);
          setSoloError(null);
        }}
        onGoCounsel={onGoCounsel}
        onPrefillCounsel={prefillCounsel}
      />

      <MicroPointSingleModal
        item={singleOfferModal}
        birth={birth}
        onClose={() => setSingleOfferModal(null)}
        onGoCounsel={onGoCounsel}
      />
    </div>
  );
}

