import type { BirthInputPayload } from "@/types/birthInput";
import type { MonthlyFortuneEnginePayload, SajuOverviewPayload, SajuReportData } from "@/types/report";
import { getApiBase } from "./apiBase";

type AnalyzeRequest = {
  name: string;
  sex: string;
  birth: string;
  calendar: "solar" | "lunar" | "lunar_leap";
};

function asRecord(v: unknown): Record<string, unknown> | null {
  return v && typeof v === "object" ? (v as Record<string, unknown>) : null;
}

function pickText(...vals: unknown[]): string {
  for (const v of vals) {
    if (typeof v === "string" && v.trim()) return v.trim();
  }
  return "";
}

function splitSentences(text: string): string[] {
  return text
    .split(/(?<=[.!?])\s+|\n+/)
    .map((s) => s.trim())
    .filter(Boolean);
}

function pickDominantTenGod(analysis: Record<string, unknown>): string {
  const sipsin = asRecord(analysis.sipsin) ?? {};
  const summary = asRecord(sipsin.summary) ?? {};
  const cand = pickText(
    summary.dominant,
    summary.main,
    summary.core,
    sipsin.dominant
  );
  return cand || "기본";
}

type ReportSectionKey = "total" | "personality" | "work" | "money" | "health";

function sectionReason(section: ReportSectionKey, tenGod: string): string {
  const t = String(tenGod || "").trim();
  if (section === "total") {
    if (t.includes("관")) return "전체 흐름에서는 기준을 높게 잡아 스스로 긴장을 키우는 패턴이 반복되기 쉽습니다.";
    if (t.includes("재")) return "전체 흐름에서는 불안할수록 통제 강도를 높이는 패턴이 체감 피로를 키울 수 있습니다.";
    if (t.includes("식신") || t.includes("상관"))
      return "전체 흐름에서는 성과 압박이 과열되면 회복 리듬이 깨지는 패턴이 나타나기 쉽습니다.";
    return "전체 흐름에서는 피로가 누적될 때 익숙한 자동 반응으로 돌아가는 패턴이 반복될 수 있습니다.";
  }
  if (section === "personality") {
    if (t.includes("인")) return "성격 흐름에서는 생각이 깊어질수록 실행이 늦어지는 패턴이 자기 의심으로 이어지기 쉽습니다.";
    if (t.includes("비견") || t.includes("겁재"))
      return "성격 흐름에서는 혼자 책임을 과하게 떠안는 패턴이 관계 부담으로 이어질 수 있습니다.";
    return "성격 흐름에서는 완벽 기준이 높아질수록 자기 검열이 강해지는 패턴이 반복되기 쉽습니다.";
  }
  if (section === "work") {
    if (t.includes("관")) return "직업운에서는 평가와 책임을 먼저 의식해 과도하게 긴장하는 패턴이 업무 효율을 떨어뜨릴 수 있습니다.";
    if (t.includes("식신") || t.includes("상관"))
      return "직업운에서는 성과를 빨리 내야 한다는 압박이 과로 루프로 이어지기 쉬운 시기입니다.";
    return "직업운에서는 역할 경계가 흐려질 때 할 일을 과잉으로 잡는 패턴이 반복되기 쉽습니다.";
  }
  if (section === "money") {
    if (t.includes("재")) return "재물운에서는 불안이 올라올 때 즉시 통제·결정을 강화하는 패턴이 지출 피로를 키울 수 있습니다.";
    return "재물운에서는 단기 불안을 줄이려는 선택이 장기 흐름을 흔드는 패턴으로 이어지기 쉽습니다.";
  }
  if (section === "health") {
    if (t.includes("관")) return "건강운에서는 책임을 놓지 못해 회복 시간을 뒤로 미루는 패턴이 피로를 누적시킬 수 있습니다.";
    if (t.includes("식신") || t.includes("상관"))
      return "건강운에서는 과집중 뒤 급소진이 반복되는 패턴이 컨디션 기복을 키우기 쉽습니다.";
    return "건강운에서는 생활 리듬이 흔들릴 때 수면·회복 루틴이 무너지는 패턴이 반복될 수 있습니다.";
  }
  return "반복되는 장면은 피로가 쌓일 때 자동 반응 패턴으로 돌아가며 강화되는 경우가 많습니다.";
}

function sectionAcknowledge(section: ReportSectionKey, tenGod: string): string {
  const t = String(tenGod || "").trim();
  if (section === "total") {
    return "지금의 반응은 실패가 아니라 버티기 위해 형성된 대응 방식이며, 흐름을 조절하는 방향으로 충분히 바꿔갈 수 있습니다.";
  }
  if (section === "personality") {
    if (t.includes("인")) return "신중함과 깊은 점검 성향은 약점이 아니라 강점이며, 지금은 자기 비난보다 자기 신뢰를 회복하는 쪽이 유리합니다.";
    return "엄격함과 책임감은 분명한 장점이며, 성격 해석에서는 강도를 조절해 장점을 유지하는 접근이 더 효과적입니다.";
  }
  if (section === "work") {
    return "업무에서의 긴장감은 성실함의 다른 표현이므로, 자신을 몰아붙이기보다 일하는 리듬을 재설계하는 것이 성과에 더 도움이 됩니다.";
  }
  if (section === "money") {
    return "재정 불안을 빠르게 통제하려는 태도는 책임감에서 나온 반응이며, 방향만 조정하면 안정성으로 전환될 수 있습니다.";
  }
  if (section === "health") {
    return "몸이 보내는 피로 신호는 의지 부족이 아니라 회복이 필요하다는 안내이므로, 휴식을 우선순위로 두는 것이 핵심입니다.";
  }
  return "그 반응은 실패가 아니라 버티기 위해 형성된 방식이라는 점을 인정하는 것이 회복의 시작입니다.";
}

function sectionAction(section: ReportSectionKey, tenGod: string): string {
  const t = String(tenGod || "").trim();
  if (section === "total") {
    return "이번 주에는 반드시 지킬 핵심 기준 2~3개만 남기고, 나머지는 보류해 전체 흐름의 압박 강도를 낮춰보세요.";
  }
  if (section === "personality") {
    if (t.includes("인")) return "하루 10분 기록(사건·감정·다음 1행동)으로 생각-행동 간격을 줄이는 연습을 권합니다.";
    return "자기평가 문장을 줄이고, 하루 한 번은 '지금 충분히 한 것'을 체크해 자기 검열 강도를 낮춰보세요.";
  }
  if (section === "work") {
    return "직업운에서는 오늘의 최우선 업무 1개만 먼저 완료하고, 나머지는 시간 블록으로 분리해 과로 루프를 끊어보세요.";
  }
  if (section === "money") {
    return "재물운에서는 결제·계약 전 24시간 유예 규칙과 주간 지출 상한 1개를 고정해 흐름을 안정화해 보세요.";
  }
  if (section === "health") {
    return "건강운에서는 수면 시작 시각과 짧은 회복 루틴(스트레칭/산책) 1가지를 7일만 고정해 컨디션 기복을 줄여보세요.";
  }
  return "이번 달에는 사건보다 반응 패턴을 기록해, 반복 고리를 먼저 알아차려 보세요.";
}

function healingToneByTenGod(
  tenGod: string,
  section: ReportSectionKey
): { reason: string; acknowledge: string; action: string } {
  const t = String(tenGod || "").trim();
  if (t.includes("비견") || t.includes("겁재")) {
    return {
      reason: sectionReason(section, t),
      acknowledge: sectionAcknowledge(section, t),
      action: sectionAction(section, t),
    };
  }
  if (t.includes("식신") || t.includes("상관")) {
    return {
      reason: sectionReason(section, t),
      acknowledge: sectionAcknowledge(section, t),
      action: sectionAction(section, t),
    };
  }
  if (t.includes("재")) {
    return {
      reason: sectionReason(section, t),
      acknowledge: sectionAcknowledge(section, t),
      action: sectionAction(section, t),
    };
  }
  if (t.includes("관")) {
    return {
      reason: sectionReason(section, t),
      acknowledge: sectionAcknowledge(section, t),
      action: sectionAction(section, t),
    };
  }
  if (t.includes("인")) {
    return {
      reason: sectionReason(section, t),
      acknowledge: sectionAcknowledge(section, t),
      action: sectionAction(section, t),
    };
  }
  return {
    reason: sectionReason(section, t),
    acknowledge: sectionAcknowledge(section, t),
    action: sectionAction(section, t),
  };
}

function enrichHealingCard(baseText: string, tenGod: string, section: ReportSectionKey): string {
  const base = pickText(baseText);
  const sents = splitSentences(base);
  const intro = sents.slice(0, 2).join(" ");
  const tone = healingToneByTenGod(tenGod, section);
  return [intro, tone.reason, tone.acknowledge, tone.action].filter(Boolean).join(" ");
}

function parseMonthlyFortune(raw: Record<string, unknown>): MonthlyFortuneEnginePayload | null {
  const mf = raw.monthly_fortune;
  if (!mf || typeof mf !== "object") return null;
  const o = mf as Record<string, unknown>;
  const monthsRaw = o.months;
  if (!Array.isArray(monthsRaw)) return null;
  const months = monthsRaw
    .map((m) => {
      if (!m || typeof m !== "object") return null;
      const x = m as Record<string, unknown>;
      const score = Number(x.score);
      const sc = (score >= 1 && score <= 5 ? score : 3) as 1 | 2 | 3 | 4 | 5;
      return {
        month: Number(x.month) || 0,
        year: Number(x.year) || 0,
        monthPillar: String(x.monthPillar ?? ""),
        monthStem: String(x.monthStem ?? ""),
        monthBranch: String(x.monthBranch ?? ""),
        stemTenGod: String(x.stemTenGod ?? ""),
        branchTenGodMain: String(x.branchTenGodMain ?? ""),
        twelveStage: String(x.twelveStage ?? ""),
        seunPillar: String(x.seunPillar ?? ""),
        daewoonPillar: String(x.daewoonPillar ?? ""),
        interactionHints: Array.isArray(x.interactionHints)
          ? (x.interactionHints as unknown[]).map((s) => String(s))
          : [],
        gongmangLine: String(x.gongmangLine ?? ""),
        yongshinLine: String(x.yongshinLine ?? ""),
        patternTop: Array.isArray(x.patternTop)
          ? (x.patternTop as unknown[]).map((s) => String(s))
          : [],
        shinsalHighlights: Array.isArray(x.shinsalHighlights)
          ? (x.shinsalHighlights as unknown[]).map((s) => String(s))
          : [],
        narrative: String(x.narrative ?? ""),
        flow: String(x.flow ?? ""),
        good: String(x.good ?? ""),
        caution: String(x.caution ?? ""),
        action: String(x.action ?? ""),
        overallFlow: pickText(x.overallFlow),
        mingliInterpretation: pickText(x.mingliInterpretation),
        realityChanges: pickText(x.realityChanges),
        coreEvents: pickText(x.coreEvents),
        opportunity: pickText(x.opportunity),
        riskPoints: pickText(x.riskPoints),
        actionGuide: pickText(x.actionGuide),
        behaviorGuide: pickText(x.behaviorGuide),
        emotionCoaching: pickText(x.emotionCoaching),
        elementPractice: pickText(x.elementPractice),
        oneLineConclusion: pickText(x.oneLineConclusion),
        aiCounselBridge: pickText(x.aiCounselBridge),
        score: sc,
        luckScore: typeof x.luckScore === "number" ? x.luckScore : undefined,
      };
    })
    .filter((m): m is NonNullable<typeof m> => m !== null && m.month >= 1 && m.month <= 12);

  if (months.length === 0) return null;

  return {
    year: Number(o.year) || new Date().getFullYear(),
    yearSummary: String(o.yearSummary ?? ""),
    bestMonth: Math.min(12, Math.max(1, Number(o.bestMonth) || 1)),
    cautionMonth: Math.min(12, Math.max(1, Number(o.cautionMonth) || 1)),
    months,
    error: typeof o.error === "string" ? o.error : undefined,
  };
}

function parseSajuOverview(raw: Record<string, unknown>): SajuOverviewPayload | null {
  const so = raw.saju_overview;
  if (!so || typeof so !== "object") return null;
  const o = so as Record<string, unknown>;
  const pillars = o.pillars as Record<string, unknown> | undefined;
  if (!pillars || typeof pillars !== "object") return null;

  const pickPillar = (k: string) => {
    const p = pillars[k] as Record<string, unknown> | undefined;
    const hs = Array.isArray(p?.hiddenStems) ? p?.hiddenStems : [];
    return {
      gan: String(p?.gan ?? ""),
      ji: String(p?.ji ?? ""),
      ganOhaeng: String(p?.ganOhaeng ?? ""),
      jiOhaeng: String(p?.jiOhaeng ?? ""),
      sipsin: String(p?.sipsin ?? ""),
      twelve: String(p?.twelve ?? ""),
      shinsal: Array.isArray(p?.shinsal) ? (p?.shinsal as unknown[]).map((x) => String(x)) : [],
      hiddenStems: hs.map((x) => {
        const h = (x as Record<string, unknown>) || {};
        return { stem: String(h.stem ?? ""), role: String(h.role ?? ""), sipsin: String(h.sipsin ?? "") };
      }),
    };
  };

  const fe = (o.fiveElements as Record<string, unknown>) || {};
  const counts = ((fe.counts as Record<string, unknown>) || {}) as Record<string, unknown>;
  const yy = ((fe.yinYangCounts as Record<string, unknown>) || {}) as Record<string, unknown>;
  const gm = ((o.gongmang as Record<string, unknown>) || {}) as Record<string, unknown>;
  const daewoon = Array.isArray(o.daewoon) ? o.daewoon : [];
  const cm = ((o.calcMeta as Record<string, unknown>) || {}) as Record<string, unknown>;

  return {
    pillars: {
      hour: pickPillar("hour"),
      day: pickPillar("day"),
      month: pickPillar("month"),
      year: pickPillar("year"),
    },
    fiveElements: {
      counts: Object.fromEntries(Object.entries(counts).map(([k, v]) => [k, Number(v) || 0])),
      yinYangCounts: Object.fromEntries(Object.entries(yy).map(([k, v]) => [k, Number(v) || 0])),
    },
    gongmang: {
      dayBase: String(gm.dayBase ?? ""),
      yearBase: String(gm.yearBase ?? ""),
      engineVoidBranches: Array.isArray(gm.engineVoidBranches)
        ? (gm.engineVoidBranches as unknown[]).map((x) => String(x))
        : [],
    },
    daewoon: daewoon.map((d) => {
      const x = (d as Record<string, unknown>) || {};
      return {
        pillar: String(x.pillar ?? ""),
        startAge: (x.startAge as number | string | null | undefined) ?? null,
        endAge: (x.endAge as number | string | null | undefined) ?? null,
        direction: String(x.direction ?? ""),
        isCurrent: Boolean(x.isCurrent),
      };
    }),
    calcMeta: {
      monthTerm: String(cm.monthTerm ?? ""),
      monthTermTimeKst: String(cm.monthTermTimeKst ?? ""),
    },
  };
}

function pickSection(raw: Record<string, unknown>): SajuReportData {
  const analysis = asRecord(raw.analysis) ?? {};
  const unified = asRecord(raw.unified) ?? {};
  const extra = asRecord(raw.extra) ?? {};
  const domains = asRecord(extra.domains) ?? {};
  const dayMaster = asRecord(analysis.day_master) ?? {};
  const sipsin = asRecord(analysis.sipsin) ?? {};
  const sipsinSummary = asRecord(sipsin.summary) ?? {};
  const dominantTenGod = pickDominantTenGod(analysis);

  const total =
    pickText(
      unified.summary,
      raw.summary,
      raw.total_summary,
      raw.overview,
      raw.message
    ) || "전체 흐름은 완만한 상승/조정이 반복되는 경향으로 보이며, 작은 실천을 누적하는 방식이 유리할 수 있습니다.";

  const personality =
    pickText(
      dayMaster.summary,
      dayMaster.headline,
      dayMaster.title,
      dayMaster.text,
      analysis.personality
    ) || "기본 성향은 책임감과 현실 감각이 함께 드러나는 편으로, 상황을 정리하며 움직일 때 안정감이 커질 수 있습니다.";

  const work =
    pickText(domains.work, domains.career, sipsinSummary.work, sipsinSummary.career) ||
    "직업운은 한 번에 크게 바꾸기보다 현재 강점을 확실히 쌓는 전략이 도움이 될 수 있습니다.";

  const money =
    pickText(domains.money, domains.wealth, sipsinSummary.wealth, sipsinSummary.money) ||
    "재물운은 지출 통제와 우선순위 정리가 핵심일 가능성이 높으며, 단기 성과보다 지속 가능한 흐름을 우선하는 편이 좋습니다.";

  const health =
    pickText(domains.health, sipsinSummary.health, analysis.health) ||
    "건강운은 과로 누적 관리가 중요해 보이며, 수면·회복 루틴을 먼저 안정화하는 것이 도움이 될 수 있습니다.";

  const monthlyFortune = parseMonthlyFortune(raw);
  const sajuOverview = parseSajuOverview(raw);

  const total2 = enrichHealingCard(total, dominantTenGod, "total");
  const personality2 = enrichHealingCard(personality, dominantTenGod, "personality");
  const work2 = enrichHealingCard(work, dominantTenGod, "work");
  const money2 = enrichHealingCard(money, dominantTenGod, "money");
  const health2 = enrichHealingCard(health, dominantTenGod, "health");

  return {
    total: total2,
    personality: personality2,
    work: work2,
    money: money2,
    health: health2,
    sajuOverview,
    monthlyFortune,
    raw,
  };
}

/**
 * localStorage에 저장된 구버전 reportData를 최신 문장 규칙으로 재가공한다.
 * raw 원본이 없으면 기존 값을 그대로 사용한다.
 */
export function refreshReportDataCopy(report: SajuReportData | null | undefined): SajuReportData | null {
  if (!report) return null;
  const raw = asRecord(report.raw);
  if (!raw) return report;
  return pickSection(raw);
}

export async function fetchSajuReport(birth: BirthInputPayload): Promise<SajuReportData> {
  const base = getApiBase();
  const url = base ? `${base}/api/analyze` : "/api/analyze";
  const body: AnalyzeRequest = {
    name: "",
    sex: birth.gender === "male" ? "남자" : "여자",
    birth: `${birth.date} ${birth.time}`,
    calendar: birth.calendarApi,
  };

  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  const rawText = await res.text();
  let json: unknown = null;
  try {
    json = rawText ? JSON.parse(rawText) : null;
  } catch {
    json = null;
  }
  if (!res.ok) {
    throw new Error(
      typeof json === "object" && json && "detail" in json
        ? String((json as { detail: unknown }).detail)
        : rawText || "리포트 생성 중 오류가 발생했습니다."
    );
  }

  const record = asRecord(json);
  if (!record) {
    throw new Error("리포트 응답 형식이 올바르지 않습니다.");
  }
  return pickSection(record);
}

