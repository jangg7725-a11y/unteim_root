import { useState } from "react";
import type { BirthInputPayload } from "@/types/birthInput";
import type { SajuReportData } from "@/types/report";
import { SCREEN_COPY } from "@/constants/screenCopy";
import { TodayFortuneCard } from "./TodayFortuneCard";
import { MonthlyFortunePremium } from "./MonthlyFortunePremium";
import { MonthlyFortuneEngine } from "./MonthlyFortuneEngine";
import { MicroPointOffers } from "./MicroPointOffers";
import { PartnerInputModal } from "./PartnerInputModal";
import { AICounselPreview } from "./AICounselPreview";
import { postCompatibility, type CompatibilityResult } from "@/services/compatibilityApi";
import type { MicroPointOfferItem } from "@/data/microPointOffersMock";
import "./report-page.css";

type Props = {
  birth: BirthInputPayload | null;
  report: SajuReportData | null;
  loading: boolean;
  error: string | null;
  onRetry: () => void;
  onGoCounsel: () => void;
};

type SectionProps = {
  title: string;
  body: string;
};

function ReportSection({ title, body }: SectionProps) {
  return (
    <section className="report-page__card" aria-label={title}>
      <h3 className="report-page__card-title">{title}</h3>
      <p className="report-page__card-text">{body}</p>
    </section>
  );
}


export function ReportPage({ birth, report, loading, error, onRetry, onGoCounsel }: Props) {
  const [pairOpen, setPairOpen] = useState(false);
  const [compatibilityLoading, setCompatibilityLoading] = useState(false);
  const [compatibilityError, setCompatibilityError] = useState<string | null>(null);
  const [compatibility, setCompatibility] = useState<CompatibilityResult | null>(null);
  const [selectedQuestion, setSelectedQuestion] = useState<string | null>(null);

  const onSelectSingle = (item: MicroPointOfferItem) => {
    setSelectedQuestion(item.question);
    setCompatibility(null);
    setCompatibilityError(null);
    // TODO: 향후 single 질문 API 연결
    console.log("[single-question]", item.question);
  };

  const onSelectPair = (item: MicroPointOfferItem) => {
    setSelectedQuestion(item.question);
    setCompatibility(null);
    setCompatibilityError(null);
    setPairOpen(true);
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

  return (
    <div className="report-page">
      <header className="report-page__head">
        <h1 className="report-page__title">{SCREEN_COPY.output.title}</h1>
        <p className="report-page__sub">{SCREEN_COPY.output.subtitle}</p>
      </header>

      {loading && (
        <p className="report-page__state" role="status">
          사주 리포트를 생성하고 있습니다…
        </p>
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
            <MonthlyFortuneEngine data={report.monthlyFortune} onGoCounsel={onGoCounsel} />
          ) : (
            <MonthlyFortunePremium onGoCounsel={onGoCounsel} />
          )}

          <TodayFortuneCard />

          <div className="report-page__grid">
            <ReportSection title="총운" body={report.total} />
            <ReportSection title="성격" body={report.personality} />
            <ReportSection title="직업운" body={report.work} />
            <ReportSection title="재물운" body={report.money} />
            <ReportSection title="건강운" body={report.health} />
          </div>

          <MicroPointOffers onSelectSingle={onSelectSingle} onSelectPair={onSelectPair} />

          {compatibilityError && <p className="report-page__compat-error">{compatibilityError}</p>}
          {compatibility && (
            <section className="report-page__compat-card" aria-label="궁합 분석 결과">
              <h3 className="report-page__compat-title">
                궁합 분석 결과 {compatibility.score}점{compatibility.score100 ? ` (${compatibility.score100}/100)` : ""}
              </h3>
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

      <PartnerInputModal
        open={pairOpen}
        loading={compatibilityLoading}
        onClose={() => setPairOpen(false)}
        onSubmit={onSubmitPartner}
      />
    </div>
  );
}

