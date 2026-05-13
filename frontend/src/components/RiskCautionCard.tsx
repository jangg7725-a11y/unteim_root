// frontend/src/components/RiskCautionCard.tsx
// 신살 기반 위험 패턴 주의 카드 — narrative_slots.risk + health + relation + separation + movement 데이터 출력

import type { MonthlyFortuneEngineMonth, NarrativeSlots, SepMovSlot } from "@/types/report";
import {
  mergeMonthlyFortuneRisks,
  type MonthlyMergedRiskSlot,
} from "@/utils/mergeMonthlyFortuneRisks";
import { LifeEventSignalCard } from "./LifeEventSignalCard";
import "./risk-caution-card.css";

type Props = {
  narrativeSlots?: NarrativeSlots | null;
  /** 월지와 맞닿아 발동한 위험 신살 슬롯 — 엔진 `monthRiskSlots`, 달마다 다름 */
  monthRiskSlots?: MonthlyMergedRiskSlot[] | null;
  /**
   * true일 때 관재·손재·사고·이별(gwanjaesu/sonjaesu/accident_su/ibyeolsu) 슬롯이 하나도 없으면
   * 안내 한 줄을 표시합니다. 월별 운세 카드에서만 사용합니다.
   */
  showEmptyCoreFourHint?: boolean;
  /** 월운 전용 — 인생 사건 신호를 상단에서 “이 시기 주의할 패턴” 카드와 한 블록으로 표시 */
  lifeEventSignals?: MonthlyFortuneEngineMonth["life_event_signals"];
  lifeEventMonth?: number;
  /** 월운에서 「이달의 핵심」으로 옮긴 risk_type 은 여기서 렌더하지 않음 */
  omitRiskTypes?: readonly string[] | null;
};

/** 관재수·손재수·사고수·이별수 — 사용자가 기대하는 네 가지 ‘수’ 패턴 */
const CORE_FOUR_RISK_TYPES = new Set([
  "gwanjaesu",
  "sonjaesu",
  "accident_su",
  "ibyeolsu",
]);

const RISK_ICON: Record<string, string> = {
  "관재수(官災數)": "⚖️",
  "사고수(事故數)": "🛡️",
  "이별수(離別數)": "🥀",
  "손재수(損財數)": "💸",
  "횡재수(橫財數)": "🍀",
};

function getIcon(label: string): string {
  for (const [key, icon] of Object.entries(RISK_ICON)) {
    if (label.includes(key.slice(0, 3))) return icon;
  }
  return "⚠️";
}

function isPositive(label: string): boolean {
  return label.includes("횡재");
}

function SepMovBox({ slot, icon, colorClass }: { slot: SepMovSlot; icon: string; colorClass: string }) {
  const mainText = slot.warning || slot.guidance || "";
  return (
    <div className={`risk-card__item ${colorClass}`}>
      <div className="risk-card__item-head">
        <span className="risk-card__item-icon" aria-hidden>{icon}</span>
        <span className="risk-card__item-label">{slot.label_ko}</span>
      </div>
      {slot.context && <p className="risk-card__core">{slot.context}</p>}
      {slot.core_message && !slot.context && (
        <p className="risk-card__core">{slot.core_message}</p>
      )}
      {mainText && (
        <div className="risk-card__row">
          <span className="risk-card__row-label">안내</span>
          <p className="risk-card__row-text">{mainText}</p>
        </div>
      )}
      {slot.action && (
        <div className="risk-card__row">
          <span className="risk-card__row-label">행동</span>
          <p className="risk-card__row-text">{slot.action}</p>
        </div>
      )}
    </div>
  );
}

export function RiskCautionCard({
  narrativeSlots,
  monthRiskSlots,
  showEmptyCoreFourHint = false,
  lifeEventSignals,
  lifeEventMonth,
  omitRiskTypes,
}: Props) {
  const mergedRisks = mergeMonthlyFortuneRisks(
    narrativeSlots?.risk?.shinsal_risks,
    monthRiskSlots ?? undefined,
  );
  const omitSet = new Set(
    (omitRiskTypes ?? []).map((x) => x.trim()).filter(Boolean),
  );
  const validRisks =
    omitSet.size > 0
      ? mergedRisks.filter((r) => {
          const rt = typeof r.risk_type === "string" ? r.risk_type.trim() : "";
          return !rt || !omitSet.has(rt);
        })
      : mergedRisks;

  const health = narrativeSlots?.health;
  const relation = narrativeSlots?.relation;
  const separation = narrativeSlots?.separation;
  const movement = narrativeSlots?.movement;

  const coreFourRisks = validRisks.filter(
    (r) => typeof r.risk_type === "string" && CORE_FOUR_RISK_TYPES.has(r.risk_type),
  );
  const otherRisks = validRisks.filter(
    (r) => !r.risk_type || !CORE_FOUR_RISK_TYPES.has(r.risk_type),
  );

  const mergedCoreFourCount = mergedRisks.filter(
    (r) => typeof r.risk_type === "string" && CORE_FOUR_RISK_TYPES.has(r.risk_type),
  ).length;
  const showCoreFourEmptyNote =
    showEmptyCoreFourHint && mergedCoreFourCount === 0;

  const healthTendency =
    health?.daymaster?.health_tendency || health?.oheng?.care || "";
  const healthCareTip = health?.daymaster?.care_tip || "";
  const healthOrgan = health?.oheng?.organ_system || "";

  const relationAdvice =
    relation?.oheng?.advice || relation?.oheng?.strategy || "";
  const relationMonthly = relation?.oheng?.monthly || "";

  const hasHealth = !!(healthTendency || healthCareTip || healthOrgan);
  const hasRelation = !!(relationAdvice || relationMonthly);
  const hasShinsal = validRisks.length > 0;
  const hasSeparation = !!separation?.found;
  const hasMovement = !!movement?.found;

  /** 이별수 슬롯이 있으면 narrative separation 과 메시지가 겹치므로 생략 (omit 전 병합 기준) */
  const hasIbyeolsuRiskSlot = mergedRisks.some(
    (r) => typeof r.risk_type === "string" && r.risk_type.trim() === "ibyeolsu",
  );
  const showSeparationBox = hasSeparation && separation && !hasIbyeolsuRiskSlot;

  const hasLifeEvents = !!(lifeEventSignals && lifeEventSignals.length > 0);

  const hasAnythingToShow =
    hasLifeEvents ||
    hasHealth ||
    hasRelation ||
    hasSeparation ||
    hasMovement ||
    hasShinsal ||
    showCoreFourEmptyNote;

  if (!hasAnythingToShow) return null;

  return (
    <section
      id="report-section-risk"
      className="report-page__card risk-card"
      aria-label="주의 패턴 카드"
    >
      <h3 className="report-page__card-title risk-card__title">
        <span className="risk-card__icon" aria-hidden>🔍</span>
        이 시기 주의할 패턴
      </h3>

      <div className="risk-card__body">
        {hasLifeEvents && lifeEventSignals && (
          <LifeEventSignalCard
            variant="embedded"
            events={lifeEventSignals}
            month={typeof lifeEventMonth === "number" ? lifeEventMonth : 1}
          />
        )}

        {/* 건강 박스 */}
        {hasHealth && (
          <div className="risk-card__item risk-card__item--health">
            <div className="risk-card__item-head">
              <span className="risk-card__item-icon" aria-hidden>🌿</span>
              <span className="risk-card__item-label">건강</span>
            </div>
            {healthTendency && (
              <p className="risk-card__core">{healthTendency}</p>
            )}
            {healthOrgan && (
              <div className="risk-card__row">
                <span className="risk-card__row-label">관련 기관</span>
                <p className="risk-card__row-text">{healthOrgan}</p>
              </div>
            )}
            {healthCareTip && (
              <div className="risk-card__row">
                <span className="risk-card__row-label">관리 팁</span>
                <p className="risk-card__row-text">{healthCareTip}</p>
              </div>
            )}
          </div>
        )}

        {/* 관계 박스 */}
        {hasRelation && (
          <div className="risk-card__item risk-card__item--relation">
            <div className="risk-card__item-head">
              <span className="risk-card__item-icon" aria-hidden>🤝</span>
              <span className="risk-card__item-label">관계</span>
            </div>
            {relationAdvice && (
              <p className="risk-card__core">{relationAdvice}</p>
            )}
            {relationMonthly && (
              <div className="risk-card__row">
                <span className="risk-card__row-label">이번 달</span>
                <p className="risk-card__row-text">{relationMonthly}</p>
              </div>
            )}
          </div>
        )}

        {/* 이별수 narrative — 월별 이별수 슬롯과 중복되면 후자만 표시 */}
        {showSeparationBox && separation && (
          <SepMovBox slot={separation} icon="💔" colorClass="risk-card__item--separation" />
        )}

        {/* 이동수 박스 */}
        {hasMovement && movement && (
          <SepMovBox slot={movement} icon="🚀" colorClass="risk-card__item--movement" />
        )}

        {/* 관재·손재·사고·이별 네 가지가 없는 달(월별) */}
        {showCoreFourEmptyNote && (
          <div
            className="risk-card__item risk-card__item--empty-core-four"
            role="status"
            aria-live="polite"
          >
            <p className="risk-card__empty-core-four-text">
              관재·손재·사고·이별 패턴 중 특별히 두드러지는 신호는 적습니다.
            </p>
          </div>
        )}

        {/* 신살 위험 패턴 — 네 가지 우선, 그 외(횡재·구설 등) */}
        {coreFourRisks.map((risk) => {
          const label = risk.label_ko ?? "";
          const positive = isPositive(label);
          const rk = risk.risk_type || label;
          return (
            <div
              key={rk}
              className={`risk-card__item ${positive ? "risk-card__item--positive" : "risk-card__item--caution"}`}
            >
              <div className="risk-card__item-head">
                <span className="risk-card__item-icon" aria-hidden>
                  {getIcon(label)}
                </span>
                <span className="risk-card__item-label">{label}</span>
              </div>

              {risk.core_message && (
                <p className="risk-card__core">{risk.core_message}</p>
              )}
              {risk.warning && (
                <div className="risk-card__row">
                  <span className="risk-card__row-label">주의</span>
                  <p className="risk-card__row-text">{risk.warning}</p>
                </div>
              )}
              {risk.action && (
                <div className="risk-card__row">
                  <span className="risk-card__row-label">행동</span>
                  <p className="risk-card__row-text">{risk.action}</p>
                </div>
              )}
            </div>
          );
        })}
        {otherRisks.map((risk) => {
          const label = risk.label_ko ?? "";
          const positive = isPositive(label);
          const rk = `other-${risk.risk_type || label}`;
          return (
            <div
              key={rk}
              className={`risk-card__item ${positive ? "risk-card__item--positive" : "risk-card__item--caution"}`}
            >
              <div className="risk-card__item-head">
                <span className="risk-card__item-icon" aria-hidden>
                  {getIcon(label)}
                </span>
                <span className="risk-card__item-label">{label}</span>
              </div>

              {risk.core_message && (
                <p className="risk-card__core">{risk.core_message}</p>
              )}
              {risk.warning && (
                <div className="risk-card__row">
                  <span className="risk-card__row-label">주의</span>
                  <p className="risk-card__row-text">{risk.warning}</p>
                </div>
              )}
              {risk.action && (
                <div className="risk-card__row">
                  <span className="risk-card__row-label">행동</span>
                  <p className="risk-card__row-text">{risk.action}</p>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <p className="risk-card__note">
        사주 구조 기반 경향 안내입니다. 단정이 아닌 참고 정보로 활용하세요.
      </p>
    </section>
  );
}
