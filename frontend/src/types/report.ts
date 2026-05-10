/** 사주 기반 narrative DB 슬롯 — /api/analyze 응답의 narrative_slots */
export type NarrativeSlot = {
  found: boolean;
  label_ko?: string;
  daymaster?: { found: boolean; label_ko?: string; money_trait?: string; health_tendency?: string; care_tip?: string; element?: string };
  oheng?: { found: boolean; label_ko?: string; core_theme?: string; strength?: string; weakness?: string; advice?: string; care?: string; strategy?: string; monthly?: string; monthly_hint?: string; organ_system?: string };
};

export type NarrativeSlots = {
  money?: NarrativeSlot;
  health?: NarrativeSlot;
  career?: NarrativeSlot;
  relation?: NarrativeSlot;
  risk?: { shinsal_risks?: Array<{ found: boolean; label_ko?: string; core_message?: string; warning?: string; action?: string }> };
};

export type SajuReportData = {
  total: string;
  personality: string;
  work: string;
  money: string;
  health: string;
  sajuOverview?: SajuOverviewPayload | null;
  /** 엔진 기반 월별 상세(있으면 월별 카드에 우선 사용) */
  monthlyFortune?: MonthlyFortuneEnginePayload | null;
  raw?: Record<string, unknown>;
  /** 사주 맞춤 narrative DB 슬롯 */
  narrativeSlots?: NarrativeSlots | null;
};

export type SajuOverviewPillar = {
  gan: string;
  ji: string;
  ganOhaeng: string;
  jiOhaeng: string;
  sipsin: string;
  twelve: string;
  shinsal: string[];
  hiddenStems: Array<{ stem: string; role: string; sipsin: string }>;
};

export type SajuOverviewPayload = {
  pillars: {
    hour: SajuOverviewPillar;
    day: SajuOverviewPillar;
    month: SajuOverviewPillar;
    year: SajuOverviewPillar;
  };
  fiveElements: {
    counts: Record<string, number>;
    yinYangCounts: Record<string, number>;
  };
  gongmang: {
    dayBase: string;
    yearBase: string;
    engineVoidBranches: string[];
  };
  daewoon: Array<{
    pillar: string;
    startAge: number | string | null;
    endAge: number | string | null;
    direction: string;
    isCurrent: boolean;
  }>;
  calcMeta?: {
    monthTerm?: string;
    monthTermTimeKst?: string;
  };
};

/** 백엔드 monthly_fortune — 십신·12운성·합충·공망·세운·대운·용희·패턴 */
export type MonthlyFortuneEngineMonth = {
  month: number;
  year: number;
  monthPillar: string;
  monthStem: string;
  monthBranch: string;
  stemTenGod: string;
  branchTenGodMain: string;
  twelveStage: string;
  seunPillar: string;
  daewoonPillar: string;
  interactionHints: string[];
  gongmangLine: string;
  yongshinLine: string;
  patternTop: string[];
  shinsalHighlights?: string[];
  narrative: string;
  flow: string;
  good: string;
  caution: string;
  action: string;
  /** 상담형 섹션(엔진 v2) — 없으면 flow·narrative·good 등으로 대체 */
  overallFlow?: string;
  mingliInterpretation?: string;
  realityChanges?: string;
  coreEvents?: string;
  opportunity?: string;
  riskPoints?: string;
  actionGuide?: string;
  behaviorGuide?: string;
  emotionCoaching?: string;
  elementPractice?: string;
  oneLineConclusion?: string;
  aiCounselBridge?: string;
  score: 1 | 2 | 3 | 4 | 5;
  luckScore?: number;
  /** 월별 narrative 슬롯 — 일간 풀과 지배 오행 풀의 월별 인덱스 순환 결과 (월별 사주값에 직결) */
  daymaster_monthly_tip?: string;
  oheng_monthly_strategy?: string;
};

export type MonthlyFortuneEnginePayload = {
  year: number;
  yearSummary: string;
  bestMonth: number;
  cautionMonth: number;
  months: MonthlyFortuneEngineMonth[];
  error?: string;
};

/** 월별 운세 1개월 — 유료 리포트용 */
export type MonthlyFortuneEntry = {
  month: 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12;
  flow: string;
  /** 기회 */
  good: string;
  caution: string;
  action: string;
  score: 1 | 2 | 3 | 4 | 5;
};

/** 올해 월별 운세 묶음 — 이후 GPT/backend에서 동일 스키마로 주입 */
export type YearlyMonthlyFortune = {
  yearSummary: string;
  bestMonth: 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12;
  cautionMonth: 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12;
  monthly: MonthlyFortuneEntry[];
};

