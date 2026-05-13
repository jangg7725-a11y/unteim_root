import { useState } from "react";
import type { BirthInputPayload } from "@/types/birthInput";
import { MicroPointOffers } from "./MicroPointOffers";
import { PartnerInputModal } from "./PartnerInputModal";
import { MicroPointSingleModal } from "./MicroPointSingleModal";
import { CompatibilityModeModal } from "./CompatibilityModeModal";
import { SoloLoveResultModal } from "./SoloLoveResultModal";
import { postCompatibility, type CompatibilityResult } from "@/services/compatibilityApi";
import { postSoloLoveInsight, type SoloLoveInsightResult } from "@/services/soloLoveInsightApi";
import { COMPAT_SCORE_LEGEND_LINES, starBandFrom100 } from "@/utils/compatibilityLabels";
import type { MicroPointOfferItem } from "@/data/microPointOffersMock";

type Props = {
  birth: BirthInputPayload | null;
  onGoCounsel: () => void;
};

export function MicroPointOfferFlow({ birth, onGoCounsel }: Props) {
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
      console.log("[pair-question]", selectedQuestion, { birth, partnerBirth });
    } catch (e) {
      setCompatibilityError(e instanceof Error ? e.message : "궁합 분석 중 오류가 발생했습니다.");
    } finally {
      setCompatibilityLoading(false);
    }
  };

  return (
    <>
      <MicroPointOffers onSelectSingle={onSelectSingle} onSelectPair={onSelectPair} />

      {compatibilityError ? <p className="report-page__compat-error">{compatibilityError}</p> : null}
      {compatibility ? (
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
          <p className="report-page__compat-line">
            <strong>서로 끌리는 이유:</strong> {compatibility.attraction}
          </p>
          <p className="report-page__compat-line">
            <strong>갈등 포인트:</strong> {compatibility.conflict}
          </p>
          <p className="report-page__compat-line">
            <strong>오래 가는 조건:</strong> {compatibility.longevity}
          </p>
          <p className="report-page__compat-line">
            <strong>행동 가이드:</strong> {compatibility.guide}
          </p>
        </section>
      ) : null}

      <CompatibilityModeModal
        open={loveModeOpen}
        onClose={() => setLoveModeOpen(false)}
        onChooseWithPartner={() => {
          setLoveModeOpen(false);
          setPairOpen(true);
        }}
        onChooseSolo={() => {
          setLoveModeOpen(false);
          void runSoloLoveFromPair();
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
    </>
  );
}
