import type { MonthlyFortuneEngineMonth, NarrativeSlots } from "@/types/report";
import { mergeMonthlyFortuneRisks } from "@/utils/mergeMonthlyFortuneRisks";

/**
 * "이달의 핵심" 박스의 문단을 만든다.
 *
 * 운트임 '근거 매핑' 비가역 룰:
 * - 모든 문단은 그 달의 사주 계산값(월간 십성 · 12운성 · 일간 팁 풀의 월별 인덱스 ·
 *   지배 오행 전략 풀의 월별 인덱스 · luck_score)에 직결되어야 한다.
 * - 관계 위험 패턴(ibyeolsu·ohae)은 월별 monthRiskSlots(+월 미부 여 시 원국 risk 슬롯)과 동일 병합 근거로
 *   한 줄 요약만 핵심 블록에 넣고, 월운 카드에서는 별도 카드로 빼지 않는다.
 * - 차트-fixed 슬롯(money_monthly / health_monthly / relation_advice / oheng_monthly_core 등)은
 *   12개월 동일 노출이 되므로 여기서 사용하지 않는다(차트 카드에서 별도 노출).
 * - 풀에 매핑이 없는 십성/운성은 빈 문단으로 두어, 근거 없는 일반 운세 문장으로 채우지 않는다.
 */

/** 월운 카드에서 「이달의 핵심」으로 옮기는 risk_type — RiskCautionCard omit 과 대응 */
const CORE_EMBED_RELATION_RISK_TYPES = ["ibyeolsu", "ohae"] as const;

function clipOneLine(text: string, max: number): string {
  const t = text.trim().replace(/\s+/g, " ");
  if (t.length <= max) return t;
  const slice = t.slice(0, max);
  const lastSpace = slice.lastIndexOf(" ");
  const stem = lastSpace > 40 ? slice.slice(0, lastSpace) : slice;
  return stem.trimEnd() + "…";
}

function appendMonthlyRelationRiskSummaries(
  m: MonthlyFortuneEngineMonth,
  narrativeSlots: NarrativeSlots | null | undefined,
  out: string[],
): void {
  const merged = mergeMonthlyFortuneRisks(
    narrativeSlots?.risk?.shinsal_risks,
    m.monthRiskSlots ?? undefined,
  );
  for (const rt of CORE_EMBED_RELATION_RISK_TYPES) {
    const slot = merged.find(
      (r) => r.found !== false && r.risk_type?.trim() === rt,
    );
    if (!slot) continue;
    const core = (slot.core_message || "").trim();
    const warn = (slot.warning || "").trim();
    const body = clipOneLine(core || warn, 130);
    if (!body) continue;
    const dup = out.some((p) => p.slice(0, 40) === body.slice(0, 40));
    if (!dup) out.push(body);
  }
}

const SIPSIN_MONTHLY_LINE: Record<string, string> = {
  비견: "이달은 동등한 협력이 잘 맞는 흐름입니다. 책임 범위를 처음에 글로 정해 두면 마찰이 줄어듭니다.",
  겁재: "이달은 분담·경쟁 구도가 두드러집니다. 큰 지출과 동업 결정은 한 박자 늦추는 편이 안전합니다.",
  식신: "이달은 표현·결과물 공개에 에너지가 잘 붙습니다. 평소 미뤄둔 마무리부터 꺼내 보세요.",
  상관: "이달은 표현력·아이디어가 강해지지만 권위·규칙과 부딪칠 수 있습니다. 톤을 한 단계 낮춰 전달하세요.",
  편재: "이달은 활동량이 많아지며 기회가 다양하게 들어옵니다. 분산보다 1~2개에 집중해 결과를 만드세요.",
  정재: "이달은 안정적인 관리·정리에 결과가 잘 붙습니다. 고정 지출과 일정부터 점검해 두세요.",
  편관: "이달은 책임·압박·결단이 늘어나는 흐름입니다. 핵심 결정 1개만 정해두고 나머지는 미루세요.",
  정관: "이달은 규칙·체계가 작동하는 달입니다. 보고·확인 절차를 빠뜨리지 않으면 평가가 좋아집니다.",
  편인: "이달은 직관·학습 흐름이 강합니다. 혼자 정리하는 시간을 따로 확보해 두세요.",
  정인: "이달은 안정·돌봄·재충전이 중심입니다. 휴식과 학습을 같은 비중으로 배치하세요.",
};

const TWELVE_STAGE_LINE: Record<string, string> = {
  장생: "12운성이 장생이라 새 시도가 잘 자리 잡는 시기입니다. 작은 시작 하나를 이달 안에 만드세요.",
  목욕: "12운성이 목욕이라 마음이 흔들리거나 노출되기 쉬운 시기입니다. 중요한 발언은 하루 묵혀 정리해서 내세요.",
  관대: "12운성이 관대라 형식·역할 정비가 잘 맞는 달입니다. 직책·계약·역할 범위를 다시 적어 두세요.",
  임관: "12운성이 임관이라 자립과 실행력이 올라옵니다. 미뤄둔 결정 1개를 이달 안에 처리하세요.",
  제왕: "12운성이 제왕이라 에너지가 정점입니다. 큰 결정을 해도 버틸 수 있지만 회복 루틴은 별도로 잡아두세요.",
  쇠: "12운성이 쇠라 한 박자 늦추는 운영이 맞는 달입니다. 새 일은 다음 달로 미루는 편이 결과가 좋습니다.",
  병: "12운성이 병이라 회복이 우선인 달입니다. 일정·약속을 평소보다 적게 잡아두세요.",
  사: "12운성이 사라 정리·마무리가 잘 맞는 달입니다. 진행 중인 일 중 끝낼 것 하나를 골라 마감하세요.",
  묘: "12운성이 묘라 보존·휴식·정리가 맞는 시기입니다. 새로 벌리지 말고 기존 자산을 정돈하세요.",
  절: "12운성이 절이라 전환·끊고 가는 흐름이 강합니다. 정리할 약속·관계 1개를 정해 두세요.",
  태: "12운성이 태라 시기가 무르익는 중입니다. 결과를 재촉하지 말고 준비 단계를 단단히 하세요.",
  양: "12운성이 양이라 성장 준비기입니다. 학습·연습·시뮬레이션에 시간을 더 배분하세요.",
};

function pickFirst(...slots: (string | undefined | null)[]): string {
  for (const s of slots) {
    const t = (s || "").trim();
    if (t) return t;
  }
  return "";
}

export function buildMonthlyFriendlyParagraphs(
  m: MonthlyFortuneEngineMonth,
  narrativeSlots?: NarrativeSlots | null,
): string[] {
  const out: string[] = [];

  // p1: 일간 월별 팁 — 일간 기질 × 이달 월 인덱스 → 매월 다른 사주 근거 문장
  const p1 = (m.daymaster_monthly_tip || "").trim();
  if (p1) out.push(p1);

  // p2: 오행 월별 전략 — 지배 오행 × 이달 인덱스 (p1과 다를 때만 추가)
  const p2 = (m.oheng_monthly_strategy || "").trim();
  if (p2 && p2 !== p1) out.push(p2);

  // p1·p2 모두 없을 때 fallback
  if (!p1 && !p2) {
    const fallback = pickFirst(m.overallFlow, m.flow);
    if (fallback) {
      // 첫 문장만 추출
      const first = fallback.split(/\n+/)[0].trim();
      if (first) out.push(first);
    }
  }

  // p3: 월간 십성 기반 한 줄 — 월주 천간이 일간에 대해 어떤 십성인지에서 직접 도출
  const sipsin = (m.stemTenGod || "").trim();
  const p3 = SIPSIN_MONTHLY_LINE[sipsin];
  if (p3) out.push(p3);

  // p4: 12운성 기반 한 줄 — 이달 일간이 처한 12운성 단계에서 직접 도출
  const stage = (m.twelveStage || "").trim();
  const p4 = TWELVE_STAGE_LINE[stage];
  if (p4) out.push(p4);

  appendMonthlyRelationRiskSummaries(m, narrativeSlots, out);

  // p5: overallFlow / flow 첫 단락 — 종합 흐름 보강 (기존 출력과 중복 방지)
  const flowRaw = pickFirst(m.overallFlow, m.flow);
  if (flowRaw) {
    const flowFirst = flowRaw.split(/\n+/)[0].trim();
    // 이미 out에 포함된 내용이면 스킵
    const isDup = out.some((p) => p.includes(flowFirst.slice(0, 18)));
    if (!isDup && flowFirst.length > 20) {
      out.push(flowFirst.endsWith(".") ? flowFirst : flowFirst + ".");
    }
  }

  return out;
}
