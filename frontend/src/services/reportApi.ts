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

function healingToneByTenGod(tenGod: string): { reason: string; acknowledge: string; action: string } {
  const t = String(tenGod || "").trim();
  if (t.includes("비견") || t.includes("겁재")) {
    return {
      reason: "반복 패턴은 혼자 감당하려는 책임 과부하에서 시작되기 쉽습니다.",
      acknowledge: "이 방식은 약점이 아니라 오래 버티기 위해 익힌 생존 전략이었다는 점을 먼저 인정해도 좋습니다.",
      action: "이번 주에는 도움 요청 문장을 미리 준비해 두고, 하루 한 번은 역할을 나누는 연습을 권합니다.",
    };
  }
  if (t.includes("식신") || t.includes("상관")) {
    return {
      reason: "반복 패턴은 성과 압박이 과로와 자책으로 이어지는 루프에서 자주 나타납니다.",
      acknowledge: "성과 민감성은 결함이 아니라 강점의 그림자이므로, 자신을 비난하기보다 리듬을 조절하는 접근이 필요합니다.",
      action: "완료 기준을 조금 낮추고 회복 시간을 먼저 캘린더에 고정해 탈진 루프를 끊어보세요.",
    };
  }
  if (t.includes("재")) {
    return {
      reason: "반복 패턴은 불안이 올라올 때 통제를 먼저 강화하는 반응에서 커질 수 있습니다.",
      acknowledge: "통제하려는 태도는 불안을 견디기 위한 보호 장치였다는 점을 인정하면 긴장이 완화됩니다.",
      action: "결정 전 24시간 유예 규칙을 두고, 지출/계약은 재확인 후 확정하는 습관이 도움이 됩니다.",
    };
  }
  if (t.includes("관")) {
    return {
      reason: "반복 패턴은 평가와 책임을 먼저 의식해 스스로를 과도하게 압박하는 흐름에서 생기기 쉽습니다.",
      acknowledge: "엄격함은 스스로를 지키기 위한 장치였고, 지금은 기준의 강도를 조절할 타이밍입니다.",
      action: "반드시 지킬 기준 3개만 남기고 나머지는 유보해, 자기 압박 강도를 낮추는 실천을 권합니다.",
    };
  }
  if (t.includes("인")) {
    return {
      reason: "반복 패턴은 생각은 깊어지지만 행동이 늦어지는 루프에서 자책으로 이어질 수 있습니다.",
      acknowledge: "신중함은 약점이 아니라 통찰의 힘이며, 속도보다 자기 신뢰 회복이 먼저입니다.",
      action: "하루 10분 기록(사건·감정·다음 1행동)으로 생각-행동 간격을 줄여보세요.",
    };
  }
  return {
    reason: "반복되는 장면은 피로가 쌓일 때 자동 반응 패턴으로 돌아가며 강화되는 경우가 많습니다.",
    acknowledge: "그 반응은 실패가 아니라 버티기 위해 형성된 방식이라는 점을 인정하는 것이 회복의 시작입니다.",
    action: "이번 달에는 사건보다 반응 패턴을 기록해, 반복 고리를 먼저 알아차려 보세요.",
  };
}

function enrichHealingCard(baseText: string, tenGod: string): string {
  const base = pickText(baseText);
  const sents = splitSentences(base);
  const intro = sents.slice(0, 2).join(" ");
  const tone = healingToneByTenGod(tenGod);
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

  const total2 = enrichHealingCard(total, dominantTenGod);
  const personality2 = enrichHealingCard(personality, dominantTenGod);
  const work2 = enrichHealingCard(work, dominantTenGod);
  const money2 = enrichHealingCard(money, dominantTenGod);
  const health2 = enrichHealingCard(health, dominantTenGod);

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

