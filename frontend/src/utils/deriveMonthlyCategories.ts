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
import {
  SHINSAL_DB,
  parseShinsalChip,
  type ShinsalEntry,
} from "@/utils/shinsalMonthDb";

export type { ShinsalEntry };
export type CategoryScore = 1 | 2 | 3 | 4 | 5;

export type MonthCategory = {
  key: "health" | "love" | "money" | "shinsal" | "caution" | "goodluck";
  title: string;
  emoji: string;
  score?: CategoryScore;
  lines: string[];
  caution?: string;
  chips?: string[];
  /** 신살 전용: 각 신살별 구조화된 설명 */
  shinsalItems?: ShinsalEntry[];
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

// ── 건강운 전용 테이블 ────────────────────────────────────────

// 12운성 → 건강 점수
const STAGE_HEALTH_SCORE: Record<string, CategoryScore> = {
  제왕: 5, 임관: 5, 관대: 4, 장생: 4,
  양: 3, 태: 3,
  쇠: 2, 목욕: 2, 묘: 2, 절: 2,
  병: 1, 사: 1,
};

/**
 * 12운성 → 건강 경보 (직설적 주의 문구)
 * 단정이 아닌 "~하기 쉬운", "~가능성" 표현 사용
 */
const STAGE_HEALTH_WARN: Record<string, string> = {
  병:   "면역력이 크게 떨어지기 쉬운 달입니다. 잔병치레·통증 신호를 가볍게 넘기지 마세요.",
  사:   "에너지가 바닥으로 떨어지는 구간입니다. 과로·수면 부족이 큰 탈로 이어질 수 있습니다.",
  묘:   "만성 피로와 소화기 부담이 쌓이기 쉬운 달입니다. 속 불편함·무기력 신호를 주의하세요.",
  절:   "신체 리듬이 무너지기 쉬운 구간입니다. 수면 불규칙과 호르몬 이상 신호에 주의하세요.",
  목욕: "피부·호흡기·감정 기복이 올라오기 쉬운 달입니다. 예민해진 몸 신호에 귀 기울이세요.",
  쇠:   "체력이 점진적으로 떨어지는 구간입니다. 피로가 누적되기 전에 미리 회복 루틴을 챙기세요.",
  태:   "체력 변동이 생기기 쉬운 달입니다. 갑작스러운 컨디션 저하에 유의하세요.",
  양:   "에너지를 비축하는 흐름입니다. 무리한 활동보다 재충전에 집중하세요.",
  관대: "활기는 좋지만 에너지를 과소비하기 쉽습니다. 무리한 스케줄을 조심하세요.",
  장생: "회복력이 좋은 달입니다. 기초 체력 루틴으로 이 흐름을 유지하세요.",
  임관: "건강 흐름이 상승 중입니다. 새 운동 루틴을 시작하기 좋은 달입니다.",
  제왕: "체력이 최고조입니다. 과신하지 말고 꾸준히 관리하면 이 흐름이 오래 이어집니다.",
};

/** 월지 오행 → 담당 장기·부위 (五行 장기 배속) */
const BRANCH_OHAENG: Record<string, string> = {
  // 木 (목) — 간·담·눈·근육
  寅: "목", 卯: "목", 인: "목", 묘: "목",
  // 火 (화) — 심장·혈관·심리
  巳: "화", 午: "화", 사: "화", 오: "화",
  // 土 (토) — 비위·소화기·면역
  辰: "토", 戌: "토", 丑: "토", 未: "토",
  진: "토", 술: "토", 축: "토", 미: "토",
  // 金 (금) — 폐·대장·피부·호흡기
  申: "금", 酉: "금", 신: "금", 유: "금",
  // 水 (수) — 신장·방광·뼈·허리
  亥: "수", 子: "수", 해: "수", 자: "수",
};

/** 오행 → 이달 집중 건강 위험 요소 */
const OHAENG_HEALTH_RISK: Record<string, string> = {
  목: "간·담 기능 저하와 눈 피로·근육 뭉침이 생기기 쉬운 달입니다.",
  화: "혈압·심장 두근거림·열감이 올라오기 쉬운 달입니다. 심리 스트레스도 심혈관에 영향을 줄 수 있습니다.",
  토: "소화기 부담이 커지기 쉬운 달입니다. 속 더부룩함·식욕 저하·위장 이상 신호를 주의하세요.",
  금: "호흡기·폐 약화와 피부 트러블이 생기기 쉬운 달입니다. 건조한 환경·먼지에 주의하세요.",
  수: "신장·방광 부담과 허리·무릎 통증이 올 수 있는 달입니다. 냉기와 수분 부족을 조심하세요.",
};

/** 오행 → 건강 루틴 제안 */
const OHAENG_ROUTINE: Record<string, string> = {
  목: "알코올·기름진 음식을 줄이고, 눈 피로 해소(온찜질·멀리 보기)와 스트레칭 루틴을 챙기세요.",
  화: "격렬한 운동보다 가벼운 유산소·명상을 선택하고, 카페인·매운 음식 섭취를 줄이세요.",
  토: "밀가루·단음식·야식을 줄이고, 규칙적인 식사 시간과 따뜻한 음식으로 속을 달래세요.",
  금: "환기·가습기로 호흡 환경을 관리하고, 마스크 착용과 충분한 수분 섭취를 습관화하세요.",
  수: "따뜻한 무릎·허리 보온을 챙기고, 물을 하루 1.5L 이상 마시며 무리한 야간 활동을 피하세요.",
};

/** 십성 → 건강 관련 스트레스 유형 */
const SIPSIN_HEALTH_STRESS: Record<string, string> = {
  겁재:  "경쟁·갈등 스트레스가 심혈관과 소화기에 영향을 줄 수 있습니다.",
  편관:  "외부 압박·과부하로 두통·목 결림·불면이 생기기 쉬운 달입니다.",
  상관:  "에너지를 과소비하기 쉬운 달입니다. 목·후두와 신경 피로에 유의하세요.",
  편인:  "고독·반추 스트레스가 수면의 질을 떨어뜨릴 수 있습니다.",
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

/**
 * 이달의 건강운
 * ─ 월지 오행 → 담당 장기·부위별 위험 요소 (달마다 다름)
 * ─ 12운성 → 에너지 단계·경보 수준 (달마다 다름)
 * ─ 십성 → 스트레스 유형 추가 (해당 유형일 때)
 * ─ 충·형 발생 → 신체 충격 신호 경고
 * ─ 합성 결과: 구체적 주의 문구 + 루틴 제안
 */
function deriveHealth(m: MonthlyFortuneEngineMonth): MonthCategory {
  const stage = (m.twelveStage || "").trim();
  const sipsin = (m.stemTenGod || "").trim();
  const score: CategoryScore =
    STAGE_HEALTH_SCORE[stage] ?? luckToScore(m.luckScore);

  // ── 월지 오행 추출 ──────────────────────────────────────────
  // monthBranch: 예) "자", "子", "인", "寅" 등
  const branchRaw = (m.monthBranch || "").trim();
  // 월주에서 뒤 한 글자가 지지인 경우도 대비 (예: "경자" → "자")
  const branchChar =
    BRANCH_OHAENG[branchRaw] !== undefined
      ? branchRaw
      : branchRaw.slice(-1); // 마지막 글자 시도
  const ohaeng = BRANCH_OHAENG[branchChar] ?? BRANCH_OHAENG[branchRaw];

  const lines: string[] = [];

  // ── 1. 12운성 경보 (매달 반드시 다름) ──────────────────────
  const stageWarn =
    STAGE_HEALTH_WARN[stage] ??
    "이달 건강 흐름은 큰 이상 없이 유지 가능합니다.";
  lines.push(stageWarn);

  // ── 2. 월지 오행 기반 장기·부위 위험 요소 ──────────────────
  if (ohaeng) {
    const ohaengRisk = OHAENG_HEALTH_RISK[ohaeng];
    if (ohaengRisk) lines.push(ohaengRisk);
  }

  // ── 3. 십성 스트레스 유형 (겁재·편관·상관·편인만 추가) ──────
  const stressMsg = SIPSIN_HEALTH_STRESS[sipsin];
  if (stressMsg && lines.length < 3) {
    lines.push(stressMsg);
  }

  // ── 4. 충·형 발생 시 신체 충격 경고 ────────────────────────
  const hasConflict = (m.interactionHints ?? []).some((h) =>
    /충|형/.test(h)
  );
  if (hasConflict && lines.length < 3) {
    lines.push(
      "이달 충·형 작용으로 갑작스러운 신체 신호나 부상 위험에 주의가 필요합니다."
    );
  }

  // ── 5. 오행 기반 루틴 제안 (caution 영역에 배치) ────────────
  const routine = ohaeng
    ? OHAENG_ROUTINE[ohaeng]
    : undefined;

  // ── 6. health_monthly DB 슬롯 (원국 건강 기질, 보강용) ───────
  if (m.health_monthly && lines.length < 3) {
    lines.push(clip(m.health_monthly, 90));
  }

  // ── 7. monthRiskSlots 건강 신살 경고 ─────────────────────────
  const healthSlot = (m.monthRiskSlots ?? []).find(
    (r) =>
      r.found &&
      /건강|질병|부상|체력|혈/.test(r.label_ko ?? "") &&
      r.warning
  );
  const caution = healthSlot?.warning ?? (m.health_care ? clip(m.health_care, 80) : undefined) ?? routine;

  return {
    key: "health",
    title: "이달의 건강운",
    emoji: "🌿",
    score,
    lines,
    caution,
  };
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

  // 2순위: 원국 relation_advice 슬롯 (관계 패턴 근거)
  if (m.relation_advice) {
    lines.push(clip(m.relation_advice, 95));
  }

  // 3순위: 십성 기반 애정 메시지
  const sipsinMsg = LOVE_MSG[sipsin];
  if (sipsinMsg && lines.length < 2) {
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

  // 1순위: 원국 money_monthly 슬롯 (재물 기질 근거)
  if (m.money_monthly) {
    lines.push(clip(m.money_monthly, 95));
  }

  // 2순위: 오행 월별 전략 (매달 다름, 재물·전략 직결)
  if (m.oheng_monthly_strategy && lines.length < 2) {
    lines.push(clip(m.oheng_monthly_strategy, 95));
  }

  // 3순위: 십성 기반 재물 메시지
  const sipsinMsg = MONEY_MSG[sipsin];
  if (sipsinMsg && lines.length < 2) {
    lines.push(sipsinMsg);
  }

  if (!lines.length) {
    lines.push("이달의 재물 흐름은 큰 변화 없이 유지하는 것이 중심입니다.");
  }

  const caution = m.money_advice ? clip(m.money_advice, 80) : undefined;
  return { key: "money", title: "이달의 재물운", emoji: "💰", score, lines, caution };
}

/**
 * 이달의 신살
 * 근거: shinsalHighlights(칩) → SHINSAL_DB 설명 연결
 *       monthRiskSlots → core_message/warning 우선 사용 (있을 때)
 * 각 신살별로 이름 + 이달 영향 + 조언을 shinsalItems에 구조화하여 반환
 */
function deriveShinsal(m: MonthlyFortuneEngineMonth): MonthCategory {
  // ① shinsalHighlights 파싱 (중복 제거)
  const parsedChips = (m.shinsalHighlights ?? [])
    .map((h) => parseShinsalChip(h))
    .filter((p) => p.name.length > 0);

  // 이름 기준 중복 제거 (같은 신살이 "주의: 반안살" / "신살: 반안살" 두 번 나올 때)
  const seenNames = new Set<string>();
  const uniqueChips = parsedChips.filter((p) => {
    if (seenNames.has(p.name)) return false;
    seenNames.add(p.name);
    return true;
  });

  // ② monthRiskSlots → label_ko: core_message 맵 (엔진 계산 기반, 우선순위 높음)
  const riskMsgMap = new Map<string, string>();
  for (const slot of m.monthRiskSlots ?? []) {
    if (slot.found && slot.label_ko) {
      const msg = slot.warning ?? slot.core_message;
      if (msg) riskMsgMap.set(slot.label_ko, msg);
    }
  }

  // ③ shinsalHighlights에 없지만 monthRiskSlots에 있는 신살 보완
  for (const slot of m.monthRiskSlots ?? []) {
    if (slot.found && slot.label_ko && !seenNames.has(slot.label_ko)) {
      uniqueChips.push({ name: slot.label_ko, type: "caution" });
      seenNames.add(slot.label_ko);
    }
  }

  // ④ 각 신살 → ShinsalEntry 구성
  const shinsalItems: ShinsalEntry[] = uniqueChips
    .slice(0, 5)
    .map(({ name, type }) => {
      // DB에 있는 설명 우선
      const dbEntry = SHINSAL_DB[name];
      // monthRiskSlots의 엔진 계산 설명이 있으면 effect로 사용
      const engineEffect = riskMsgMap.get(name);

      if (dbEntry) {
        return {
          ...dbEntry,
          // 엔진이 구체적 메시지를 줬을 때는 보조로 붙임
          effect: engineEffect
            ? `${clip(engineEffect, 80)} ${dbEntry.effect}`
            : dbEntry.effect,
        };
      }

      // DB 미등재 신살 → 분류 추론 + 기본 메시지
      const category: ShinsalEntry["category"] =
        type === "good" ? "good" : type === "caution" ? "caution" : "caution";
      return {
        name,
        category,
        effect:
          engineEffect ??
          `이달 ${name}이 활성화됩니다. 에너지의 흐름에 주의를 기울이세요.`,
        advice: "신살의 영향을 참고해 이달 흐름을 조율하세요.",
      };
    });

  // ⑤ 칩: 표시용 이름 목록
  const chips = shinsalItems.map((s) => s.name);

  // ⑥ 신살이 하나도 없을 때
  const lines: string[] =
    shinsalItems.length === 0
      ? ["이달에 특별히 활성화된 신살이 없습니다. 안정적인 흐름입니다."]
      : [];

  return {
    key: "shinsal",
    title: "이달의 신살",
    emoji: "✨",
    chips,
    lines,
    shinsalItems: shinsalItems.length > 0 ? shinsalItems : undefined,
  };
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

  // 2순위: riskPoints 원문 (엔진 상담 기반 주의 문장)
  if (m.riskPoints && lines.length < 2) {
    const riskFirst = m.riskPoints.split(/\n+/)[0]?.trim();
    if (riskFirst) lines.push(clip(riskFirst, 95));
  }

  // 3순위: interactionHints 충·형 (매달 다름)
  const clashHints = (m.interactionHints ?? []).filter((h) => /충|형|파|해/.test(h));
  if (clashHints.length && lines.length < 2) {
    lines.push(clip(clashHints[0], 90));
    if (clashHints.length > 1 && lines.length < 2) {
      lines.push(clip(clashHints[1], 90));
    }
  }

  // 4순위: 위험 십성 주의 메시지 (매달 십성이 다름)
  const sipsinCaution = CAUTION_SIPSIN[sipsin];
  if (sipsinCaution) {
    chips.push(sipsinCaution.chip);
    if (lines.length < 2) lines.push(sipsinCaution.msg);
  }

  // 5순위: 위험 12운성 주의 메시지
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
