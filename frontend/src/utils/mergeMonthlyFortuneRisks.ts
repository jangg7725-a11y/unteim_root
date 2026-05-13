/** narrative_slots.risk.shinsal_risks · monthRiskSlots 공통 형태 */
export type MonthlyMergedRiskSlot = {
  found?: boolean;
  risk_type?: string;
  label_ko?: string;
  core_message?: string;
  warning?: string;
  action?: string;
};

const RISK_ORDER = [
  "gwanjaesu",
  "sonjaesu",
  "accident_su",
  "ibyeolsu",
  "hwongjaesu",
  "guseolsu",
  "ohae",
];

function sortSlotsByRiskOrder(slots: MonthlyMergedRiskSlot[]): MonthlyMergedRiskSlot[] {
  return [...slots].sort((a, b) => {
    const ka = (typeof a.risk_type === "string" && a.risk_type.trim()) || "";
    const kb = (typeof b.risk_type === "string" && b.risk_type.trim()) || "";
    const ia = RISK_ORDER.indexOf(ka);
    const ib = RISK_ORDER.indexOf(kb);
    return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib);
  });
}

/**
 * 월운: monthRiskSlots 우선, 없으면 원국 narrative_slots.risk.shinsal_risks — RiskCautionCard 와 동일.
 */
export function mergeMonthlyFortuneRisks(
  natal: MonthlyMergedRiskSlot[] | undefined | null,
  monthly: MonthlyMergedRiskSlot[] | undefined | null,
): MonthlyMergedRiskSlot[] {
  const n = natal ?? [];
  const m = monthly ?? [];
  if (m.length > 0) return sortSlotsByRiskOrder(m);
  return sortSlotsByRiskOrder([...n]);
}
