// frontend/src/components/RiskCautionCard.tsx
// 신살 기반 위험 패턴 주의 카드 — narrative_slots.risk 데이터 출력

import type { NarrativeSlots } from "@/types/report";
import "./risk-caution-card.css";

type RiskSlot = {
  found: boolean;
  label_ko?: string;
  core_message?: string;
  warning?: string;
  action?: string;
};

type Props = {
  narrativeSlots?: NarrativeSlots | null;
};

const RISK_ICON: Record<string, string> = {
  "관재수(官災數)": "⚖️",
  "사고수(事故數)": "🛡️",
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

export function RiskCautionCard({ narrativeSlots }: Props) {
  const risks = narrativeSlots?.risk?.shinsal_risks;
  if (!risks || risks.length === 0) return null;

  const validRisks = risks.filter((r): r is RiskSlot & { found: true } => !!r.found);
  if (validRisks.length === 0) return null;

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
        {validRisks.map((risk, i) => {
          const label = risk.label_ko ?? "";
          const positive = isPositive(label);
          return (
            <div
              key={i}
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
        신살 구조 기반 경향 안내입니다. 단정이 아닌 참고 정보로 활용하세요.
      </p>
    </section>
  );
}
