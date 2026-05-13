// frontend/src/components/RiskCautionCard.tsx
// 신살 기반 위험 패턴 주의 카드 — narrative_slots.risk + health + relation + separation + movement 데이터 출력

import type { MonthlyFortuneEngineMonth, NarrativeSlots, SepMovSlot } from "@/types/report";
import { LifeEventSignalCard } from "./LifeEventSignalCard";
import "./risk-caution-card.css";

type RiskSlot = {
  found: boolean;
  /** 엔진 위험 키 (gwanjaesu, accident_su, ibyeolsu …) — 월별·원국 병합 시 중복 제거용 */
  risk_type?: string;
  label_ko?: string;
  core_message?: string;
  warning?: string;
  action?: string;
};

type Props = {
  narrativeSlots?: NarrativeSlots | null;
  /** 월지와 맞닿아 발동한 위험 신살 슬롯 — 엔진 `monthRiskSlots`, 달마다 다름 */
  monthRiskSlots?: RiskSlot[] | null;
  /**
   * true일 때 관재·손재·사고·이별(gwanjaesu/sonjaesu/accident_su/ibyeolsu) 슬롯이 하나도 없으면
   * 안내 한 줄을 표시합니다. 월별 운세 카드에서만 사용합니다.
   */
  showEmptyCoreFourHint?: boolean;
  /** 월운 전용 — 인생 사건 신호를 상단에서 “이 시기 주의할 패턴” 카드와 한 블록으로 표시 */
  lifeEventSignals?: MonthlyFortuneEngineMonth["life_event_signals"];
  lifeEventMonth?: number;
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

/** 엔진 risk_type 기준 표시 순서 (관재·재물·신체·관계 순) */
const RISK_ORDER = [
  "gwanjaesu",
  "sonjaesu",
  "accident_su",
  "ibyeolsu",
  "hwongjaesu",
  "guseolsu",
  "ohae",
];

function sortSlotsByRiskOrder(slots: RiskSlot[]): RiskSlot[] {
  return [...slots].sort((a, b) => {
    const ka = (typeof a.risk_type === "string" && a.risk_type.trim()) || "";
    const kb = (typeof b.risk_type === "string" && b.risk_type.trim()) || "";
    const ia = RISK_ORDER.indexOf(ka);
    const ib = RISK_ORDER.indexOf(kb);
    return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib);
  });
}

/**
 * 월운 카드: monthRiskSlots가 있으면 엔진 월별 슬롯만 사용(문구가 달·월지 시드로 매번 다름).
 * 월 데이터가 없을 때만 원국 narrative_slots.risk 를 사용.
 */
function mergeShinsalRisks(
  natal: RiskSlot[] | undefined,
  monthly: RiskSlot[] | undefined,
): RiskSlot[] {
  if (monthly?.length) return sortSlotsByRiskOrder(monthly);
  return sortSlotsByRiskOrder(natal ?? []);
}

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
}: Props) {
  const validRisks = mergeShinsalRisks(narrativeSlots?.risk?.shinsal_risks, monthRiskSlots ?? undefined);
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

  const showCoreFourEmptyNote =
    showEmptyCoreFourHint && coreFourRisks.length === 0;

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

        {/* 이별수 박스 */}
        {hasSeparation && separation && (
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
            <p className="risk-card__empty-core-four-text">해당 내용이 없어요~^^</p>
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
