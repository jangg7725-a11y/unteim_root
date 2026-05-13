/**
 * narrative/risk_fortune_db.json 의 engine_mapping.shinsal_risk_map 과 동기화.
 * 월별 주의 패턴(monthRiskSlots)과 같은 축을 설명하는 신살은
 * 「이달의 신살」카테고리에서 빼고 패턴 카드에 맡긴다.
 */
export const SHINSAL_TO_MONTH_RISK_TYPES: Record<string, readonly string[]> = {
  백호살: ["accident_su", "sonjaesu"],
  천라지망: ["gwanjaesu", "sonjaesu"],
  혈인살: ["accident_su"],
  겁살: ["sonjaesu", "gwanjaesu"],
  망신살: ["gwanjaesu", "guseolsu"],
  귀문관살: ["accident_su", "ohae"],
  화개살: ["ibyeolsu", "ohae"],
  양인살: ["guseolsu"],
  도화: ["ibyeolsu", "guseolsu"],
  도화살: ["ibyeolsu", "guseolsu"],
  역마살: ["ibyeolsu"],
  역마: ["ibyeolsu"],
  고란살: ["ibyeolsu"],
  월살: ["accident_su"],
  지살: ["accident_su"],
  천살: ["accident_su"],
  상문살: ["accident_su", "ohae"],
  재살: ["sonjaesu"],
  수옥살: ["gwanjaesu"],
};

/** 월간 활성 risk_type 집합 */
export function monthRiskTypeSet(
  slots: ReadonlyArray<{ found?: boolean; risk_type?: string }> | undefined | null,
): Set<string> {
  const out = new Set<string>();
  for (const r of slots ?? []) {
    if (r.found === false) continue;
    const rt = typeof r.risk_type === "string" ? r.risk_type.trim() : "";
    if (rt) out.add(rt);
  }
  return out;
}

/** 신살 이름이 현재 월 패턴 슬롯과 같은 축을 쓰면 true */
export function shinsalOverlapsMonthRiskPattern(
  shinsalName: string,
  activeRiskTypes: Set<string>,
): boolean {
  const raw = shinsalName.trim();
  const candidates = [raw, raw.replace(/살$/, "").trim()].filter(Boolean);
  const uniq = [...new Set(candidates)];
  for (const k of uniq) {
    const mapped = SHINSAL_TO_MONTH_RISK_TYPES[k];
    if (mapped?.some((rt) => activeRiskTypes.has(rt))) return true;
  }
  return false;
}
