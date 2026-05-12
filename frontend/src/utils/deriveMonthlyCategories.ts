/**
 * deriveMonthlyCategories.ts
 * MonthlyFortuneEngineMonth → 6개 카테고리별 운세 도출
 *
 * 근거 필드 (월별 변동 필드만 우선 사용):
 *   stemTenGod         — 월간 십성 (매달 다름)
 *   branchTenGodMain   — 월지 본기 십성
 *   twelveStage        — 12운성 (매달 다름)
 *   interactionHints   — 합·충·형 힌트 (매달 다름)
 *   shinsalHighlights  — 활성 신살 (매달 다름)
 *   monthRiskSlots     — 월지 기반 위험 슬롯 (매달 다름)
 *   oheng_monthly_strategy — 오행 전략 (매달 다름)
 *   daymaster_monthly_tip  — 일간 월별 팁
 *   yongshinLine       — 용신·희신·기신 월간 평가
 *   good / opportunity — 잘 풀리는 방향 (매달 다름)
 *   patternTop         — 이달 키워드
 *   luckScore          — 종합 점수 (매달 다름)
 *
 * ※ emotionCoaching, caution 필드는 AI 템플릿 반복이 많아 주력으로 사용하지 않음
 */

import type { MonthlyFortuneEngineMonth } from "@/types/report";

export type CategoryScore = 1 | 2 | 3 | 4 | 5;

export type MonthCategory = {
  key: "health" | "love" | "money" | "shinsal" | "caution" | "goodluck";
  title: string;
  emoji: string;
  score?: CategoryScore;
  lines: string[];
  caution?: string;
  chips?: string[];
};

// ── 내부 헬퍼 ────────────────────────────────────────────────

function clip(text: string, max = 90): string {
  const t = text.trim();
  return t.length <= max ? t : t.slice(0, max) + "…";
}

function luckToScore(luckScore: number | undefined): CategoryScore {
  const n = Number(luckScore ?? 50);
  if (n >= 78) return 5;
  if (n >= 63) return 4;
  if (n >= 48) return 3;
  if (n >= 33) return 2;
  return 1;
}

// ── 십성 매핑 테이블 ──────────────────────────────────────────

// 십성 → 애정운 점수
const SIPSIN_LOVE: Record<string, CategoryScore> = {
  정재: 5, 정인: 4, 편재: 4, 식신: 3, 정관: 3,
  비견: 3, 겁재: 2, 상관: 2, 편관: 2, 편인: 2,
};

// 십성 → 재물운 점수
const SIPSIN_MONEY: Record<string, CategoryScore> = {
  편재: 5, 정재: 4, 식신: 4, 상관: 3, 정관: 3,
  정인: 3, 비견: 2, 편관: 2, 편인: 2, 겁재: 1,
};

// 12운성 → 건강 점수
const STAGE_HEALTH: Record<string, CategoryScore> = {
  제왕: 5, 임관: 5, 관대: 4, 장생: 4,
  양: 3, 태: 3,
  쇠: 2, 목욕: 2, 묘: 2, 절: 2,
  병: 1, 사: 1,
};

// 12운성 → 건강 본문 메시지 (월별 변동 보장)
const HEALTH_MSG: Record<string, string> = {
  제왕:  "체력·활력이 최고조인 달입니다. 활동적인 스케줄을 잡아도 잘 버팁니다.",
  임관:  "건강 흐름이 상승 중입니다. 새로운 건강 루틴을 시작하기에 적합합니다.",
  관대:  "활기차고 자신감이 있는 달입니다. 꾸준한 운동 루틴으로 체력을 비축하세요.",
  장생:  "회복력이 좋고 활기찬 달입니다. 기초 체력 관리를 유지하세요.",
  양:    "회복과 준비 에너지의 달입니다. 과소비보다 축적에 집중하세요.",
  태:    "새 출발 기운이 있지만 체력 변동이 생기기 쉽습니다. 수면 리듬을 지키세요.",
  쇠:    "흐름이 잦아드는 달입니다. 새 활동보다 기존 루틴 유지에 집중하세요.",
  목욕:  "에너지가 불규칙할 수 있습니다. 감정 기복과 피로감을 함께 주의하세요.",
  묘:    "에너지를 아끼는 흐름입니다. 과로를 피하고 규칙적 휴식을 확보하세요.",
  절:    "신체 리듬이 흔들리기 쉬운 구간입니다. 스트레스 관리를 최우선으로 하세요.",
  병:    "체력이 쉽게 떨어지는 달입니다. 무리한 일정을 줄이고 수면·식사를 챙기세요.",
  사:    "활력이 낮은 시기입니다. 큰 활동보다 회복에 집중하는 것이 유리합니다.",
};

// 십성 → 애정 본문 메시지
const LOVE_MSG: Record<string, string> = {
  정재:  "안정적인 관계에서 교류가 깊어지는 달입니다. 진지한 약속과 대화가 잘 맞습니다.",
  편재:  "새로운 만남이나 감정 변화가 생기기 쉬운 달입니다. 설렘은 좋지만 충동적 결정은 조심하세요.",
  정인:  "상대에게 배려·지지받기 좋은 달입니다. 먼저 감사 표현을 건네보세요.",
  식신:  "편안하고 즐거운 교류가 이어지는 달입니다. 함께하는 취미·식사가 관계를 깊게 합니다.",
  비견:  "서로 독립적인 흐름이라 거리감이 자연스러울 수 있습니다. 각자의 공간을 존중하세요.",
  겁재:  "경쟁심이나 오해가 생기기 쉬운 달입니다. 중요한 대화 전 감정을 가라앉히세요.",
  상관:  "표현이 강해지지만 예민해지기 쉽습니다. 말투와 뉘앙스에 주의하세요.",
  편관:  "외부 압박으로 관계에 긴장이 생길 수 있습니다. 서로 여유를 주는 것이 도움이 됩니다.",
  정관:  "책임감 있는 관계 흐름입니다. 신뢰가 쌓이기 좋은 시기입니다.",
  편인:  "감정 표현보다 혼자 생각하는 시간이 많아집니다. 의도적인 교류를 늘려보세요.",
};

// 십성 → 재물 본문 메시지
const MONEY_MSG: Record<string, string> = {
  편재:  "재물 기회가 들어오는 달입니다. 투자·소비 결정은 계획 위주로 하세요.",
  정재:  "안정적인 수입·관리가 잘 되는 달입니다. 고정 지출을 점검해 두세요.",
  식신:  "노력이 수입으로 연결되기 좋은 달입니다. 꾸준한 활동이 결과로 이어집니다.",
  상관:  "수입은 생기지만 지출도 늘어나기 쉽습니다. 예산을 미리 정해 두세요.",
  비견:  "혼자 진행하는 프로젝트가 유리한 달입니다. 동업·공동 투자는 조심하세요.",
  겁재:  "지출·분쟁·손실 가능성이 높은 달입니다. 큰 재정 결정은 다음 달로 미루세요.",
  편관:  "부담이 재정에도 영향을 미칠 수 있습니다. 고정비를 줄이는 것이 도움이 됩니다.",
  정관:  "재정 관리가 안정적으로 유지되는 달입니다. 계획대로 실행하면 좋습니다.",
  정인:  "큰 흐름보다 유지에 초점을 두는 달입니다. 비용 관리가 핵심입니다.",
  편인:  "배움·정보 취득에 집중하는 달입니다. 직접 투자보다 준비 단계가 유리합니다.",
};

// 십성 → 주의포인트 (위험 신호가 있는 십성)
const CAUTION_SIPSIN: Record<string, { chip: string; msg: string }> = {
  겁재:  { chip: "재물·분쟁", msg: "지출·보증·동업 등 재물 관련 결정을 특히 신중하게 하세요." },
  편관:  { chip: "압박·관재", msg: "외부 압박·충돌 가능성이 있습니다. 관재·시비를 피하려면 먼저 양보하세요." },
  상관:  { chip: "시비·표현", msg: "표현이 강해져 시비·오해가 생기기 쉬운 달입니다. 공식 자리 발언에 주의하세요." },
  편재:  { chip: "충동소비", msg: "기회가 많지만 충동적 결정이 나중에 부담이 될 수 있습니다." },
};

// 12운성 → 주의포인트
const CAUTION_STAGE: Record<string, string> = {
  병:   "체력·에너지 저하 구간입니다. 과로와 무리한 일정을 피하세요.",
  사:   "활력이 낮은 시기입니다. 큰 결정·새 시작은 다음 달로 미루는 것이 좋습니다.",
  묘:   "에너지가 안으로 응축되는 시기입니다. 겉보다 내부 신호를 먼저 살피세요.",
  절:   "흐름이 끊기는 구간입니다. 연속성이 필요한 일은 특히 관리가 필요합니다.",
};

// ── 카테고리 도출 함수 ────────────────────────────────────────

/** 이달의 건강운 — 근거: twelveStage (매달 변동 보장) */
function deriveHealth(m: MonthlyFortuneEngineMonth): MonthCategory {
  const stage = (m.twelveStage || "").trim();
  const score: CategoryScore = STAGE_HEALTH[stage] ?? luckToScore(m.luckScore);

  // 1순위: 12운성 기반 건강 메시지 (매달 반드시 다름)
  const stageLine =
    HEALTH_MSG[stage] ??
    "이달 건강 관리는 일상 루틴을 유지하는 것이 핵심입니다.";

  const lines: string[] = [stageLine];

  // 2순위: 일간 월별 팁에 건강 관련 내용이 있으면 보조
  if (m.daymaster_monthly_tip) {
    const tip = m.daymaster_monthly_tip.trim();
    if (/건강|체력|몸|피로|수면|식사|운동/.test(tip)) {
      lines.push(clip(tip, 85));
    }
  }

  // monthRiskSlots에서 건강 관련 경고
  const healthSlot = (m.monthRiskSlots ?? []).find(
    (r) => r.found && /건강|질병|부상|체력/.test(r.label_ko ?? "") && r.warning
  );
  const caution = healthSlot?.warning;

  return { key: "health", title: "이달의 건강운", emoji: "🌿", score, lines, caution };
}

/** 이달의 애정운 — 근거: stemTenGod + interactionHints 합·충 */
function deriveLove(m: MonthlyFortuneEngineMonth): MonthCategory {
  const sipsin = (m.stemTenGod || "").trim();
  const score: CategoryScore = SIPSIN_LOVE[sipsin] ?? luckToScore(m.luckScore);

  const lines: string[] = [];

  // 1순위: interactionHints 중 관계 관련 합·충 힌트 (매달 변동)
  const loveHints = (m.interactionHints ?? []).filter((h) =>
    /합|충|형|인연|관계|배우자|이성|연애/.test(h)
  );
  if (loveHints.length) {
    lines.push(clip(loveHints[0], 90));
  }

  // 2순위: 십성 기반 애정 메시지 (매달 십성이 다름)
  const sipsinMsg = LOVE_MSG[sipsin];
  if (sipsinMsg) {
    lines.push(sipsinMsg);
  }

  if (!lines.length) {
    lines.push("이달의 애정 흐름은 일상적인 교류를 유지하며 자연스럽게 이어가는 것이 좋습니다.");
  }

  return { key: "love", title: "이달의 애정운", emoji: "💕", score, lines };
}

/** 이달의 재물운 — 근거: stemTenGod + oheng_monthly_strategy */
function deriveMoney(m: MonthlyFortuneEngineMonth): MonthCategory {
  const sipsin = (m.stemTenGod || "").trim();
  const score: CategoryScore = SIPSIN_MONEY[sipsin] ?? luckToScore(m.luckScore);

  const lines: string[] = [];

  // 1순위: 오행 월별 전략 (매달 다름, 재물·전략과 가장 직결)
  if (m.oheng_monthly_strategy) {
    lines.push(clip(m.oheng_monthly_strategy, 95));
  }

  // 2순위: 십성 기반 재물 메시지 (매달 십성이 다름)
  const sipsinMsg = MONEY_MSG[sipsin];
  if (sipsinMsg) {
    lines.push(sipsinMsg);
  }

  if (!lines.length) {
    lines.push("이달의 재물 흐름은 큰 변화 없이 유지하는 것이 중심입니다.");
  }

  return { key: "money", title: "이달의 재물운", emoji: "💰", score, lines };
}

/** 이달의 신살 — 근거: shinsalHighlights (중복 제거) */
function deriveShinsal(m: MonthlyFortuneEngineMonth): MonthCategory {
  // 중복 제거: "주의: 반안살" / "신살: 반안살" → "반안살" 로 통일
  const rawHighlights = [...new Set(
    (m.shinsalHighlights ?? [])
      .map((h) => h.replace(/^(귀인:|주의:|신살:)\s*/i, "").trim())
      .filter(Boolean)
  )];

  // 원본에서 귀인 여부 파악 (접두사 기준)
  const origHighlights = (m.shinsalHighlights ?? []).map((h) => h.trim());
  const isGoodSet = new Set(
    origHighlights
      .filter((h) => h.startsWith("귀인:"))
      .map((h) => h.replace(/^귀인:\s*/, "").trim())
  );

  const chips = rawHighlights.slice(0, 5);
  const lines: string[] = [];

  if (rawHighlights.length) {
    const goods = rawHighlights.filter((h) => isGoodSet.has(h));
    const risks = rawHighlights.filter((h) => !isGoodSet.has(h));

    if (goods.length) {
      lines.push(`이달 활성 귀인·길성: ${goods.join(", ")}`);
    }
    if (risks.length) {
      lines.push(`주의할 신살: ${risks.join(", ")}`);
    }
  } else {
    // monthRiskSlots 레이블 보조
    const riskLabels = [...new Set(
      (m.monthRiskSlots ?? [])
        .filter((r) => r.found && r.label_ko)
        .map((r) => r.label_ko as string)
    )];

    if (riskLabels.length) {
      chips.push(...riskLabels.slice(0, 3));
      lines.push(`이달 활성 신살: ${riskLabels.join(", ")}`);
    } else {
      lines.push("이달에 특별히 활성화된 신살이 없습니다. 안정적인 흐름입니다.");
    }
  }

  return { key: "shinsal", title: "이달의 신살", emoji: "✨", chips, lines };
}

/** 이달의 주의포인트 — 근거: monthRiskSlots + 충·형 힌트 + 십성·12운성 (매달 변동 필드만) */
function deriveCaution(m: MonthlyFortuneEngineMonth): MonthCategory {
  const sipsin = (m.stemTenGod || "").trim();
  const stage = (m.twelveStage || "").trim();
  const lines: string[] = [];
  const chips: string[] = [];

  // 1순위: monthRiskSlots 활성 항목 (shinsal 기반, 매달 다름)
  const activeRisks = (m.monthRiskSlots ?? []).filter((r) => r.found);
  const seenMsgs = new Set<string>();

  for (const r of activeRisks) {
    if (r.label_ko) chips.push(r.label_ko);
    const msg = r.warning ?? r.core_message;
    if (msg && !seenMsgs.has(msg)) {
      seenMsgs.add(msg);
      if (lines.length < 2) lines.push(clip(msg, 95));
    }
  }

  // 2순위: interactionHints 충·형 (매달 다름)
  const clashHints = (m.interactionHints ?? []).filter((h) => /충|형|파|해/.test(h));
  if (clashHints.length && lines.length < 2) {
    lines.push(clip(clashHints[0], 90));
    if (clashHints.length > 1 && lines.length < 2) {
      lines.push(clip(clashHints[1], 90));
    }
  }

  // 3순위: 위험 십성 주의 메시지 (매달 십성이 다름)
  const sipsinCaution = CAUTION_SIPSIN[sipsin];
  if (sipsinCaution) {
    chips.push(sipsinCaution.chip);
    if (lines.length < 2) lines.push(sipsinCaution.msg);
  }

  // 4순위: 위험 12운성 주의 메시지
  const stageCaution = CAUTION_STAGE[stage];
  if (stageCaution && lines.length < 2) {
    lines.push(stageCaution);
  }

  // 모두 없을 때 — 순조로운 달
  if (!lines.length) {
    lines.push("이달 특별히 주의할 신호가 없습니다. 계획한 대로 진행하면 좋습니다.");
    chips.push("안정");
  }

  // 위험 신호 건수 기반 점수 (많을수록 낮은 점수 = 더 주의 필요)
  const signals =
    activeRisks.length +
    clashHints.length +
    (sipsinCaution ? 1 : 0) +
    (stageCaution ? 1 : 0);
  const score: CategoryScore =
    signals === 0 ? 5 :
    signals === 1 ? 4 :
    signals === 2 ? 3 :
    signals === 3 ? 2 : 1;

  return {
    key: "caution",
    title: "이달의 주의포인트",
    emoji: "⚠️",
    score,
    chips: [...new Set(chips)].slice(0, 5),
    lines,
  };
}

/** 이달의 행운 — 근거: yongshinLine + good/opportunity + patternTop */
function deriveGoodLuck(m: MonthlyFortuneEngineMonth): MonthCategory {
  const score = luckToScore(m.luckScore);

  const lines: string[] = [];
  const chips = [...new Set((m.patternTop ?? []).slice(0, 4))];

  // 1순위: 용신 라인 (용희신 월간 활성도 — 행운과 직결)
  if (m.yongshinLine) {
    lines.push(clip(m.yongshinLine, 95));
  }

  // 2순위: opportunity / good 첫 번째 항목 (매달 다름)
  const opp = ((m.opportunity ?? m.good) || "").trim();
  const firstOpp = opp.split(/\n+/).find((l) => l.trim());
  if (firstOpp && firstOpp.replace(/^[\-•]\s*/, "").trim() !== lines[0]) {
    lines.push(clip(firstOpp.replace(/^[\-•]\s*/, ""), 90));
  }

  if (!lines.length) {
    lines.push("이달의 행운 흐름은 꾸준한 활동과 관계 유지에서 나옵니다.");
  }

  // 공망 주의 (고정이지만 해당 월에 한해 표시)
  const caution =
    m.gongmangLine && m.gongmangLine.trim()
      ? clip(m.gongmangLine, 80)
      : undefined;

  return {
    key: "goodluck",
    title: "이달의 행운",
    emoji: "🍀",
    score,
    chips,
    lines,
    caution,
  };
}

// ── 공개 API ─────────────────────────────────────────────────

/**
 * MonthlyFortuneEngineMonth → 6개 카테고리별 운세 배열
 * 순서: 건강운 · 애정운 · 재물운 · 신살 · 주의포인트 · 행운
 */
export function deriveMonthlyCategories(
  m: MonthlyFortuneEngineMonth
): MonthCategory[] {
  return [
    deriveHealth(m),
    deriveLove(m),
    deriveMoney(m),
    deriveShinsal(m),
    deriveCaution(m),
    deriveGoodLuck(m),
  ];
}
