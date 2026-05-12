/**
 * deriveMonthlyCategories.ts
 * MonthlyFortuneEngineMonth 데이터 → 6개 카테고리별 운세 도출
 * 건강운 · 애정운 · 재물운 · 신살 · 액운 · 행운
 *
 * 근거 필드: stemTenGod, branchTenGodMain, twelveStage, shinsalHighlights,
 *           monthRiskSlots, interactionHints, yongshinLine, gongmangLine,
 *           emotionCoaching, elementPractice, daymaster_monthly_tip,
 *           oheng_monthly_strategy, opportunity, good, riskPoints, caution,
 *           luckScore, patternTop
 */

import type { MonthlyFortuneEngineMonth } from "@/types/report";

export type CategoryScore = 1 | 2 | 3 | 4 | 5;

export type MonthCategory = {
  /** 카테고리 키 */
  key: "health" | "love" | "money" | "shinsal" | "badluck" | "goodluck";
  /** 표시 제목 */
  title: string;
  /** 대표 이모지 */
  emoji: string;
  /** 1~5점 점수 (신살은 없음) */
  score?: CategoryScore;
  /** 본문 텍스트 1~2개 */
  lines: string[];
  /** 경고 · 주의 문장 */
  caution?: string;
  /** 태그 칩 (신살명, 패턴 키워드 등) */
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

// 12운성 → 건강 기본 점수
const STAGE_HEALTH: Record<string, CategoryScore> = {
  제왕: 5,
  임관: 5,
  관대: 4,
  장생: 4,
  양: 3,
  태: 3,
  쇠: 2,
  목욕: 2,
  병: 1,
  사: 1,
  묘: 2,
  절: 2,
};

// 십성 → 애정운 기본 점수
const SIPSIN_LOVE: Record<string, CategoryScore> = {
  정재: 5,
  정인: 4,
  편재: 4,
  식신: 3,
  정관: 3,
  비견: 3,
  겁재: 2,
  상관: 2,
  편관: 2,
  편인: 2,
};

// 십성 → 재물운 기본 점수
const SIPSIN_MONEY: Record<string, CategoryScore> = {
  편재: 5,
  정재: 4,
  식신: 4,
  상관: 3,
  정관: 3,
  정인: 3,
  비견: 2,
  편관: 2,
  편인: 2,
  겁재: 1,
};

// 십성 기반 애정 메시지
const LOVE_BY_SIPSIN: Record<string, string> = {
  정재: "안정적인 관계에서 교류가 깊어지는 달입니다. 진지한 약속이나 대화가 잘 맞습니다.",
  편재: "새로운 만남이나 감정 변화가 생기기 쉬운 달입니다. 설렘은 좋지만 충동적 결정은 조심하세요.",
  정인: "상대에게 배려·지지받기 좋은 달입니다. 먼저 감사 표현을 건네보세요.",
  식신: "편안하고 즐거운 교류가 잘 이어지는 달입니다. 함께하는 취미나 식사가 관계를 깊게 합니다.",
  비견: "독립적인 흐름이라 거리 두기가 자연스러울 수 있습니다. 서로의 공간을 존중하는 것이 좋습니다.",
  겁재: "경쟁심이나 오해가 생기기 쉬운 달입니다. 중요한 대화 전 감정을 가라앉히세요.",
  상관: "표현이 강해지지만 예민해지기 쉽습니다. 말투와 뉘앙스에 신경 쓰세요.",
  편관: "외부 압박으로 관계에 긴장이 생길 수 있습니다. 서로 여유를 주는 것이 도움이 됩니다.",
  정관: "책임감 있는 관계 흐름입니다. 신뢰가 쌓이기 좋은 시기입니다.",
  편인: "감정 표현보다 혼자 생각하는 시간이 많아질 수 있습니다. 의도적 교류를 늘려보세요.",
};

// 십성 기반 재물 메시지
const MONEY_BY_SIPSIN: Record<string, string> = {
  편재: "재물 기회가 들어오는 달입니다. 투자·소비 결정은 충동보다 계획으로 하세요.",
  정재: "안정적인 수입·관리가 잘 되는 달입니다. 고정 지출을 점검해 두세요.",
  식신: "노력에 대한 결과가 잘 연결되는 달입니다. 꾸준한 활동이 수입으로 이어질 수 있습니다.",
  상관: "수입은 생기지만 지출도 늘어나기 쉽습니다. 예산을 미리 정해 두세요.",
  비견: "혼자 진행하는 프로젝트가 유리한 달입니다. 동업·공동 투자는 조심하세요.",
  겁재: "지출·분쟁·투자 손실 가능성이 높은 달입니다. 큰 재정 결정은 다음 달로 미루세요.",
  편관: "부담·압박이 재정에도 영향을 미칠 수 있습니다. 고정비를 줄이는 것이 도움이 됩니다.",
  정관: "재정 관리가 안정적으로 유지되는 달입니다. 계획한 대로 실행하면 좋습니다.",
  정인: "큰 흐름보다 유지에 초점을 두는 달입니다. 수익보다 비용 관리가 핵심입니다.",
  편인: "재물보다 배움·정보 취득에 집중하는 달입니다. 직접 투자보다 준비에 무게를 두세요.",
};

// 12운성 기반 건강 메시지
const HEALTH_BY_STAGE: Record<string, string> = {
  제왕: "체력과 활력이 최고조입니다. 운동이나 활동적 스케줄을 잡아도 버팁니다.",
  임관: "건강 흐름이 좋은 시기입니다. 새 건강 루틴을 시작하기에 적합합니다.",
  관대: "활기차고 자신감이 넘치는 달입니다. 꾸준한 루틴으로 체력을 쌓으세요.",
  장생: "활기차고 회복력이 좋은 달입니다. 기초 체력 루틴을 유지하세요.",
  양: "회복과 준비의 흐름입니다. 과도한 소비보다 에너지를 비축하는 것이 좋습니다.",
  태: "새 출발의 기운이 있지만 체력 변동이 생기기 쉽습니다. 규칙적 수면을 챙기세요.",
  쇠: "회복과 정비가 맞는 달입니다. 새 운동보다 유지에 집중하세요.",
  목욕: "에너지가 불안정할 수 있습니다. 감정 기복과 함께 피로감이 올 수 있으니 주의하세요.",
  병: "체력이 쉽게 떨어질 수 있습니다. 무리한 일정은 피하고 수면과 식사를 챙기세요.",
  사: "활력이 낮은 시기입니다. 새 일보다 회복에 집중하는 것이 유리합니다.",
  묘: "에너지를 아끼는 흐름입니다. 과로를 피하고 규칙적 휴식을 확보하세요.",
  절: "신체 리듬이 흔들릴 수 있습니다. 스트레스 관리에 특히 신경 쓰세요.",
};

// ── 카테고리 도출 함수 ────────────────────────────────────────

/** 이달의 건강운 */
function deriveHealth(m: MonthlyFortuneEngineMonth): MonthCategory {
  const stage = (m.twelveStage || "").trim();
  const baseScore: CategoryScore =
    STAGE_HEALTH[stage] ?? luckToScore(m.luckScore);

  const lines: string[] = [];

  // 감정 코칭(건강·정서 포함)
  if (m.emotionCoaching) {
    lines.push(clip(m.emotionCoaching, 95));
  }

  // 12운성 기반 메시지 (emotionCoaching 없을 때)
  if (!lines.length) {
    lines.push(
      HEALTH_BY_STAGE[stage] ??
        "이달 건강 관리는 큰 무리 없이 일상 루틴을 유지하는 것이 핵심입니다."
    );
  }

  // 오행 실천법 첫 줄 보조
  if (m.elementPractice) {
    const ep = m.elementPractice.trim().split(/\n+/)[0];
    if (ep && ep !== lines[0]) lines.push(clip(ep, 80));
  }

  // monthRiskSlots에서 건강 관련 경고
  const healthSlot = (m.monthRiskSlots ?? []).find(
    (r) =>
      r.found &&
      /건강|질병|부상|체력|몸/.test(r.label_ko ?? "") &&
      r.warning
  );
  const caution = healthSlot?.warning;

  return {
    key: "health",
    title: "이달의 건강운",
    emoji: "🌿",
    score: baseScore,
    lines,
    caution,
  };
}

/** 이달의 애정운 */
function deriveLove(m: MonthlyFortuneEngineMonth): MonthCategory {
  const sipsin = (m.stemTenGod || "").trim();
  const baseScore: CategoryScore =
    SIPSIN_LOVE[sipsin] ?? luckToScore(m.luckScore);

  const lines: string[] = [];

  // interactionHints에서 합·충 관계 힌트 추출
  const loveHints = (m.interactionHints ?? []).filter(
    (h) => /합|충|형|인연|관계|배우자|이성/.test(h)
  );
  if (loveHints.length) {
    lines.push(clip(loveHints[0], 90));
  }

  // 십성 기반 메시지
  const sipsinMsg = LOVE_BY_SIPSIN[sipsin];
  if (sipsinMsg && !lines.length) {
    lines.push(sipsinMsg);
  }

  // daymaster_monthly_tip이 애정 관련이면 추가
  if (m.daymaster_monthly_tip && lines.length < 2) {
    const tip = m.daymaster_monthly_tip.trim();
    if (/관계|인연|배우자|연애|이성/.test(tip)) {
      lines.push(clip(tip, 85));
    }
  }

  if (!lines.length) {
    lines.push(
      "이달의 애정 흐름은 일상적인 교류를 유지하며 자연스럽게 이어가는 것이 좋습니다."
    );
  }

  return {
    key: "love",
    title: "이달의 애정운",
    emoji: "💕",
    score: baseScore,
    lines,
  };
}

/** 이달의 재물운 */
function deriveMoney(m: MonthlyFortuneEngineMonth): MonthCategory {
  const sipsin = (m.stemTenGod || "").trim();
  const baseScore: CategoryScore =
    SIPSIN_MONEY[sipsin] ?? luckToScore(m.luckScore);

  const lines: string[] = [];

  // 용신 라인(이달 용희신 활성도 — 재물 기운과 연결)
  if (m.yongshinLine) {
    lines.push(clip(m.yongshinLine, 90));
  }

  // 오행 월별 전략
  if (m.oheng_monthly_strategy && lines.length < 2) {
    lines.push(clip(m.oheng_monthly_strategy, 90));
  }

  // 십성 기반 재물 메시지
  if (!lines.length) {
    lines.push(
      MONEY_BY_SIPSIN[sipsin] ??
        "이달의 재물 흐름은 큰 변화 없이 유지하는 것이 중심입니다."
    );
  }

  // opportunity/good 보조 (있을 때 2번째 줄로)
  if (lines.length < 2) {
    const opp = ((m.opportunity ?? m.good) || "").trim();
    if (opp) lines.push(clip(opp, 85));
  }

  return {
    key: "money",
    title: "이달의 재물운",
    emoji: "💰",
    score: baseScore,
    lines,
  };
}

/** 이달의 신살 */
function deriveShinsal(m: MonthlyFortuneEngineMonth): MonthCategory {
  const rawHighlights = (m.shinsalHighlights ?? [])
    .map((h) => h.trim())
    .filter(Boolean);

  const chips = rawHighlights.slice(0, 5);
  const lines: string[] = [];

  if (rawHighlights.length) {
    const goods = rawHighlights.filter((h) => h.startsWith("귀인:"));
    const risks = rawHighlights.filter((h) => !h.startsWith("귀인:"));

    if (goods.length) {
      lines.push(
        `이달 활성 귀인·길성: ${goods
          .map((g) => g.replace("귀인:", "").trim())
          .join(", ")}`
      );
    }
    if (risks.length) {
      lines.push(`주의할 신살: ${risks.join(", ")}`);
    }
  } else {
    // shinsalHighlights 없으면 monthRiskSlots 레이블 사용
    const riskLabels = (m.monthRiskSlots ?? [])
      .filter((r) => r.found && r.label_ko)
      .map((r) => r.label_ko as string);

    if (riskLabels.length) {
      chips.push(...riskLabels.slice(0, 3));
      lines.push(`이달 활성 신살: ${riskLabels.join(", ")}`);
    } else {
      lines.push("이달에 특별히 활성화된 신살이 없습니다. 안정적인 흐름입니다.");
    }
  }

  return {
    key: "shinsal",
    title: "이달의 신살",
    emoji: "✨",
    chips,
    lines,
  };
}

/** 이달의 액운 — 관재·사고·이별·시비 */
function deriveBadLuck(m: MonthlyFortuneEngineMonth): MonthCategory {
  const riskSlots = (m.monthRiskSlots ?? []).filter((r) => r.found);

  const lines: string[] = [];
  const chips: string[] = [];

  if (riskSlots.length) {
    riskSlots.forEach((r) => {
      if (r.label_ko) chips.push(r.label_ko);
      const msg = r.warning ?? r.core_message;
      if (msg && lines.length < 2) lines.push(clip(msg, 95));
    });
  }

  // riskPoints 필드 (엔진 v2)
  if (m.riskPoints && lines.length < 2) {
    lines.push(clip(m.riskPoints, 95));
  }

  // caution 필드 보조
  if (m.caution && lines.length < 2) {
    const cautionLine = m.caution.trim().split(/\n+/)[0];
    if (cautionLine) lines.push(clip(cautionLine, 90));
  }

  if (!lines.length) {
    lines.push(
      "이달 특별히 주의할 액운은 감지되지 않습니다. 일상적인 주의를 유지하세요."
    );
    chips.push("안정");
  }

  // 위험 건수 기반 중증도 점수 (많을수록 낮은 점수 = 더 위험)
  const severity = riskSlots.length;
  const score: CategoryScore =
    severity === 0
      ? 5
      : severity === 1
        ? 4
        : severity === 2
          ? 3
          : severity === 3
            ? 2
            : 1;

  return {
    key: "badluck",
    title: "이달의 액운",
    emoji: "⚠️",
    score,
    chips,
    lines,
  };
}

/** 이달의 행운 */
function deriveGoodLuck(m: MonthlyFortuneEngineMonth): MonthCategory {
  const score = luckToScore(m.luckScore);

  const lines: string[] = [];
  // 패턴 키워드 칩
  const chips = (m.patternTop ?? []).slice(0, 4);

  // 용신 라인
  if (m.yongshinLine) {
    lines.push(clip(m.yongshinLine, 90));
  }

  // opportunity / good 필드
  const opp = ((m.opportunity ?? m.good) || "").trim().split(/\n+/)[0];
  if (opp && opp !== lines[0]) {
    lines.push(clip(opp, 90));
  }

  // oheng_monthly_strategy 보조
  if (m.oheng_monthly_strategy && lines.length < 2) {
    lines.push(clip(m.oheng_monthly_strategy, 85));
  }

  if (!lines.length) {
    lines.push(
      "이달의 행운 흐름은 꾸준한 활동과 관계 유지에서 나옵니다."
    );
  }

  // 공망 경고
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
 * MonthlyFortuneEngineMonth → 6개 카테고리별 운세 배열 반환
 * 순서: 건강운 · 애정운 · 재물운 · 신살 · 액운 · 행운
 */
export function deriveMonthlyCategories(
  m: MonthlyFortuneEngineMonth
): MonthCategory[] {
  return [
    deriveHealth(m),
    deriveLove(m),
    deriveMoney(m),
    deriveShinsal(m),
    deriveBadLuck(m),
    deriveGoodLuck(m),
  ];
}
