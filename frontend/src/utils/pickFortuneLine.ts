import type { BirthInputPayload } from "@/types/birthInput";
import type { FeedItem } from "@/types/contentFeed";
import type { FortuneLinesData } from "@/types/fortuneLines";

function hashToUint(str: string): number {
  let h = 5381;
  for (let i = 0; i < str.length; i++) {
    h = ((h << 5) + h) ^ str.charCodeAt(i);
  }
  return h >>> 0;
}

/** 한국 날짜(Asia/Seoul) YYYYMMDD — 하루 동안 같은 카드에 같은 문장 유지 */
export function yyyymmddKST(): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Seoul",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  })
    .format(new Date())
    .replace(/-/g, "");
}

function uniquePool(lines: string[] | undefined): string[] {
  if (!lines?.length) return [];
  const seen = new Set<string>();
  const out: string[] = [];
  for (const line of lines) {
    const t = line.trim();
    if (!t || seen.has(t)) continue;
    seen.add(t);
    out.push(t);
  }
  return out;
}

function pickFromPrimaryIds(
  bc: Record<string, string[]>,
  primaryIds: string[],
  seed: string,
): string | null {
  for (const id of primaryIds) {
    const pool = uniquePool(bc[id]);
    if (pool.length === 0) continue;
    const idx = hashToUint(seed) % pool.length;
    return pool[idx] ?? null;
  }

  const allPool = uniquePool(bc.all);
  if (allPool.length > 0) {
    const idx = hashToUint(seed) % allPool.length;
    return allPool[idx] ?? null;
  }

  const seen = new Set<string>();
  const union: string[] = [];
  for (const id of Object.keys(bc)) {
    if (id === "all") continue;
    for (const line of uniquePool(bc[id])) {
      if (seen.has(line)) continue;
      seen.add(line);
      union.push(line);
    }
  }
  if (union.length === 0) return null;
  const idx = hashToUint(seed) % union.length;
  return union[idx] ?? null;
}

/**
 * 피드 카드의 categoryIds 순서를 우선해 상황에 맞는 풀에서 고르고,
 * 없으면 all → 여러 풀 합집합 순으로 폴백합니다.
 */
export function pickFortuneLine(item: FeedItem, data: FortuneLinesData | null): string | null {
  if (!data?.byCategory) return null;

  const bc = data.byCategory;
  const seed = `${yyyymmddKST()}|${item.id}`;

  const orderedIds = (item.categoryIds || []).filter((id) => id !== "all");
  return pickFromPrimaryIds(bc, orderedIds, seed);
}

/** 사주 리포트·월운 등 — 엔진 본문과 별도 참고 문장 슬롯 */
export type ReportFortuneSlot =
  | "total"
  | "personality"
  | "work"
  | "money"
  | "health"
  | "todayCard"
  | "monthlyIntro";

/** 슬롯별로 우선 시도할 버킷 id (앞이 더 상황에 가깝게 매핑) */
const REPORT_SLOT_PRIMARY: Record<ReportFortuneSlot, string[]> = {
  total: ["monthly", "saju", "all"],
  personality: ["mind", "all"],
  work: ["work", "all"],
  money: ["work", "all"],
  health: ["mind", "all"],
  todayCard: ["monthly", "mind", "all"],
  monthlyIntro: ["monthly", "all"],
};

function asRecord(v: unknown): Record<string, unknown> | null {
  return v && typeof v === "object" ? (v as Record<string, unknown>) : null;
}

type SipsinGroup = "비겁" | "식상" | "재성" | "관성" | "인성";

function accumulateSipsinGroups(raw: Record<string, unknown> | null | undefined): Record<SipsinGroup, number> {
  const groups: Record<SipsinGroup, number> = {
    비겁: 0,
    식상: 0,
    재성: 0,
    관성: 0,
    인성: 0,
  };
  const analysisRec = asRecord(asRecord(raw)?.analysis);
  const sipsin = analysisRec ? asRecord(analysisRec["sipsin"]) : null;
  const profiles = asRecord(sipsin?.profiles);
  if (!profiles) return groups;
  for (const [k, v] of Object.entries(profiles)) {
    const n = Number(v) || 0;
    if (!n) continue;
    const key = String(k);
    if (/비견|겁재/.test(key)) groups.비겁 += n;
    else if (/식신|상관/.test(key)) groups.식상 += n;
    else if (/편재|정재/.test(key)) groups.재성 += n;
    else if (/편관|정관/.test(key)) groups.관성 += n;
    else if (/편인|정인/.test(key)) groups.인성 += n;
  }
  return groups;
}

function dominantSipsinGroup(raw: Record<string, unknown> | null | undefined): SipsinGroup | null {
  const g = accumulateSipsinGroups(raw);
  let max = 0;
  let name: SipsinGroup | null = null;
  (Object.entries(g) as [SipsinGroup, number][]).forEach(([k, n]) => {
    if (n > max) {
      max = n;
      name = k;
    }
  });
  return max > 0 ? name : null;
}

function weakestElementKey(raw: Record<string, unknown> | null | undefined): string | null {
  const so = asRecord(raw?.saju_overview);
  const fe = asRecord(so?.fiveElements);
  const counts = asRecord(fe?.counts);
  if (!counts) return null;
  const keys = ["목", "화", "토", "금", "수"] as const;
  let min = Infinity;
  let weak: string | null = null;
  for (const k of keys) {
    const n = Number(counts[k]) || 0;
    if (n < min) {
      min = n;
      weak = k;
    }
  }
  return weak;
}

function uniqueCategoryOrder(ids: string[]): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const id of ids) {
    if (seen.has(id)) continue;
    seen.add(id);
    out.push(id);
  }
  return out;
}

/**
 * analyze API raw + 슬롯에 맞춰 fortune_lines 버킷 우선순위(오행·십신 그룹 반영).
 */
function categoryOrderForSlot(slot: ReportFortuneSlot, raw: Record<string, unknown> | null | undefined): string[] {
  const base = REPORT_SLOT_PRIMARY[slot];
  const dom = dominantSipsinGroup(raw);
  const weak = weakestElementKey(raw);
  const prefs: string[] = [];

  if (slot === "work" || slot === "money") {
    if (dom === "재성") prefs.push("work", "monthly");
    if (dom === "관성") prefs.push("work", "monthly");
    if (dom === "식상") prefs.push("work", "mind");
  }
  if (slot === "personality" || slot === "health" || slot === "todayCard") {
    if (dom === "인성" || dom === "비겁") prefs.push("mind", "monthly");
    if (weak) prefs.push("mind");
  }
  if (slot === "monthlyIntro" || slot === "total") {
    prefs.push("monthly");
    if (dom === "재성") prefs.push("work");
    if (dom === "관성") prefs.push("work");
    if (dom === "인성") prefs.push("mind");
    if (weak) prefs.push("mind");
  }

  return uniqueCategoryOrder([...prefs, ...base, "all"]);
}

export function birthSeed(birth: BirthInputPayload): string {
  return `${birth.date}|${birth.time}|${birth.gender}|${birth.calendarApi}`;
}

/**
 * analyze 응답(raw)이 있으면 십신·오행 분포를 반영해 버킷을 고르고,
 * 없으면 기존 슬롯 기본 순서를 씁니다. 같은 날·같은 사주에는 동일 문장(슬롯별 시드 분리).
 */
export function pickFortuneLineForReport(
  slot: ReportFortuneSlot,
  data: FortuneLinesData | null,
  birth: BirthInputPayload | null,
  reportRaw?: Record<string, unknown> | null,
): string | null {
  if (!data?.byCategory || !birth) return null;
  const ordered = reportRaw
    ? categoryOrderForSlot(slot, reportRaw)
    : uniqueCategoryOrder([...REPORT_SLOT_PRIMARY[slot], "all"]);
  const dom = dominantSipsinGroup(reportRaw ?? null);
  const weak = weakestElementKey(reportRaw ?? null);
  const cm = String(new Date().getMonth() + 1);
  const seed = `${yyyymmddKST()}|${birthSeed(birth)}|${slot}|${dom ?? ""}|${weak ?? ""}|${cm}`;
  return pickFromPrimaryIds(data.byCategory, ordered, seed);
}
