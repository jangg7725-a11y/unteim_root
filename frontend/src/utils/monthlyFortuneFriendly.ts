import type { MonthlyFortuneEngineMonth } from "@/types/report";

function isPlaceholderPillar(s: string | undefined): boolean {
  const t = (s || "").replace(/\s/g, "").trim();
  return !t || t === "—" || t === "-" || t === "–";
}

function monthNo(v: unknown): number {
  const n = Number(v || 0);
  return n >= 1 && n <= 12 ? n : 1;
}

function pickSlot(...slots: (string | undefined)[]): string {
  for (const s of slots) {
    const t = (s || "").trim();
    if (t) return t;
  }
  return "";
}

/**
 * 사주 맞춤 narrative DB 슬롯을 우선 사용하고,
 * 없으면 기존 하드코딩 문장으로 폴백.
 */
export function buildMonthlyFriendlyParagraphs(m: MonthlyFortuneEngineMonth): string[] {
  const out: string[] = [];
  const hasSeun = !isPlaceholderPillar(m.seunPillar);
  const month = monthNo(m.month);
  const score = Number(m.luckScore || 0);
  const hasHints = m.interactionHints.some((h) => h.trim());
  const hasGongmang = Boolean((m.gongmangLine || "").trim());
  const hasSupport = Boolean((m.yongshinLine || "").trim());

  // ── 1문단: 이달 핵심 전략 (새 슬롯 우선) ──────────────────
  const p1 = pickSlot(
    m.daymaster_monthly_tip,    // 일간별 맞춤 팁 (최우선)
    m.oheng_monthly_strategy,   // 오행 전략
  );
  if (p1) {
    out.push(p1);
  } else {
    // 폴백: 기존 하드코딩
    const monthFocus: Record<number, string> = {
      1: "시작한 일을 짧게라도 끝내며 리듬 만들기",
      2: "약속·협업 기준 먼저 맞추기",
      3: "속도보다 정확도 챙기기",
      4: "일정 재배치로 과부하 줄이기",
      5: "관계 피로 관리 + 핵심 업무 유지",
      6: "결정·지출 서두르지 않고 검토",
      7: "성과는 올리고 과로는 줄이기",
      8: "중요한 일 1~2개 집중",
      9: "변수 대응 여유시간 확보",
      10: "마감·정리 우선",
      11: "체력 회복 루틴 고정",
      12: "한 해 정리 + 다음 달 준비",
    };
    const focusLine = monthFocus[month] || "핵심 우선순위 정하고 작은 실행 이어가기";
    const monthDecisionLine: Record<number, string> = {
      1: "작게 끝내는 습관을 만들면 다음 달이 훨씬 편해집니다.",
      2: "약속을 줄이고 핵심 일정만 고정하면 피로가 눈에 띄게 줄어듭니다.",
      3: "빠른 판단보다 한 번 더 확인하는 선택이 실수를 줄입니다.",
      4: "일정을 비워두는 시간이 있어야 갑작스런 변수에 버틸 수 있습니다.",
      5: "관계 대응 에너지를 아끼면 업무 집중도가 다시 올라옵니다.",
      6: "결정은 하루 유예 후 확정하는 방식이 더 안전합니다.",
      7: "성과 욕심보다 회복 루틴을 함께 잡아야 흐름이 이어집니다.",
      8: "핵심 1~2개만 끝내도 결과 체감이 크게 올라옵니다.",
      9: "여유시간 블록이 있으면 변수가 와도 컨디션을 지킬 수 있습니다.",
      10: "새로 벌리기보다 마감 완료를 먼저 하면 부담이 빠르게 줄어듭니다.",
      11: "수면과 식사 시간을 고정하면 집중력 흔들림이 줄어듭니다.",
      12: "남은 과제를 정리해 두면 다음 달 출발이 가벼워집니다.",
    };
    out.push(
      hasSeun
        ? `${month}월은 단기 흐름과 장기 흐름이 함께 움직입니다. **${focusLine}** 같은 운영이 중요합니다. ${monthDecisionLine[month]}`
        : `${month}월은 당장 눈앞의 선택이 결과를 더 많이 좌우합니다. 핵심은 **${focusLine}**입니다. ${monthDecisionLine[month]}`
    );
  }

  // ── 2문단: 재물 또는 직업 슬롯 ──────────────────────────────
  const p2 = pickSlot(
    m.money_monthly,    // 재물 이달 힌트 (최우선)
    m.money_advice,     // 재물 조언
    m.career_strategy,  // 취업/직업 전략
  );
  if (p2) {
    out.push(p2);
  } else {
    const monthChangeLine: Record<number, string> = {
      1: "1월은 시작 단계라 계획보다 실행 체크가 중요합니다.",
      2: "2월은 사람·일정 조율이 늘어 약속 정리가 성패를 가릅니다.",
      3: "3월은 속도는 붙지만 실수도 늘기 쉬워 확인이 필수입니다.",
      4: "4월은 일정이 겹치기 쉬워 선택과 집중이 특히 중요합니다.",
      5: "5월은 관계 피로가 누적되기 쉬워 거리 조절이 필요합니다.",
      6: "6월은 결정이 많아져 검토 순서를 정하면 흔들림이 줄어듭니다.",
      7: "7월은 성과 기회가 커지지만 과로 신호도 함께 올라옵니다.",
      8: "8월은 핵심 과제 집중이 잘 먹히는 달이라 분산이 손해입니다.",
      9: "9월은 변수 대응이 많아 여유시간을 남겨야 안정적입니다.",
      10: "10월은 마감·정리 이슈가 커져 완료 중심 운영이 유리합니다.",
      11: "11월은 체력 기복이 올라 쉬는 루틴이 성과를 지켜줍니다.",
      12: "12월은 마무리 비중이 커 정리 우선이 결과를 좌우합니다.",
    };
    out.push(
      hasHints
        ? `${monthChangeLine[month]} 사람·일정·환경 이슈가 맞물리기 쉬우니 약속과 일정을 미리 정리하는 편이 좋습니다.`
        : `${monthChangeLine[month]} 큰 충돌보다 기존 패턴 유지 쪽으로 흐르기 쉬워 무리한 확장보다 안정적인 진행이 더 유리합니다.`
    );
  }

  // ── 3문단: 건강 또는 관계 슬롯 ──────────────────────────────
  const p3 = pickSlot(
    m.health_monthly,   // 건강 이달 힌트 (최우선)
    m.health_care,      // 건강 관리법
    m.relation_advice,  // 관계 조언
  );
  if (p3) {
    out.push(p3);
  } else if (hasGongmang) {
    const monthDecisionLine: Record<number, string> = {
      1: "작게 끝내는 습관을 만들면 다음 달이 훨씬 편해집니다.",
      2: "약속을 줄이고 핵심 일정만 고정하면 피로가 눈에 띄게 줄어듭니다.",
      3: "빠른 판단보다 한 번 더 확인하는 선택이 실수를 줄입니다.",
      4: "일정을 비워두는 시간이 있어야 갑작스런 변수에 버틸 수 있습니다.",
      5: "관계 대응 에너지를 아끼면 업무 집중도가 다시 올라옵니다.",
      6: "결정은 하루 유예 후 확정하는 방식이 더 안전합니다.",
      7: "성과 욕심보다 회복 루틴을 함께 잡아야 흐름이 이어집니다.",
      8: "핵심 1~2개만 끝내도 결과 체감이 크게 올라옵니다.",
      9: "여유시간 블록이 있으면 변수가 와도 컨디션을 지킬 수 있습니다.",
      10: "새로 벌리기보다 마감 완료를 먼저 하면 부담이 빠르게 줄어듭니다.",
      11: "수면과 식사 시간을 고정하면 집중력 흔들림이 줄어듭니다.",
      12: "남은 과제를 정리해 두면 다음 달 출발이 가벼워집니다.",
    };
    out.push(`${month}월은 계획이 한 번에 확정되지 않고 수정될 수 있어요. ${monthDecisionLine[month]}`);
  }

  // ── 4문단: 전체 페이스 조언 ──────────────────────────────────
  const p4 = pickSlot(
    m.oheng_monthly_core,  // 오행 핵심 메시지
    m.money_trait,         // 재물 성향
    m.career_strength,     // 직업 강점
  );
  const scoreHint =
    score >= 72
      ? "흐름이 받쳐주는 편이라 실행력을 올려도 버틸 가능성이 큽니다."
      : score >= 55
        ? "기회와 부담이 함께 들어오는 구간이라 균형 운영이 핵심입니다."
        : "무리하면 빨리 지치기 쉬운 구간이라 업무량을 줄여 가는 편이 좋습니다.";

  if (p4) {
    out.push(`${p4} ${scoreHint}`);
  } else {
    const monthlyPaceLine: Record<number, string> = {
      1: "1월은 출발 에너지가 올라와도 페이스를 너무 빨리 올리지 않는 운영이 좋습니다.",
      2: "2월은 약속·협업이 늘어 쉬는 시간 없이 달리면 금방 지칠 수 있습니다.",
      3: "3월은 속도가 붙는 달이라 중간 점검 시간을 꼭 넣어야 합니다.",
      4: "4월은 일정이 겹치기 쉬워 하루 처리량을 줄여 가는 편이 더 안정적입니다.",
      5: "5월은 관계 피로가 쌓이기 쉬워 업무와 회복 리듬을 분리하는 것이 중요합니다.",
      6: "6월은 판단 피로가 커질 수 있어 결정을 나눠 처리하는 방식이 맞습니다.",
      7: "7월은 성과 기회가 크지만 과열되기 쉬워 짧은 회복 루틴이 꼭 필요합니다.",
      8: "8월은 집중 효율이 좋은 편이라 핵심 과제에 힘을 모으는 운영이 잘 맞습니다.",
      9: "9월은 변수 대응이 많아 체력 소모가 커질 수 있으니 여유시간을 남겨두는 편이 좋습니다.",
      10: "10월은 마감 부담이 누적되기 쉬워 속도보다 마무리 순서가 중요합니다.",
      11: "11월은 컨디션 기복이 올라올 수 있어 생활 리듬 고정이 성과를 지켜줍니다.",
      12: "12월은 마무리 업무가 몰리기 쉬워 일정을 넉넉히 잡는 편이 더 유리합니다.",
    };
    out.push(
      hasSupport
        ? `${monthlyPaceLine[month]} ${scoreHint} ${month}월은 중요한 일부터 처리하고 지치기 전에 짧게 쉬는 리듬이 잘 맞습니다.`
        : `${monthlyPaceLine[month]} ${scoreHint} ${month}월은 일정 간격을 넉넉히 두고 한 번에 많은 일을 벌이지 않는 편이 좋습니다.`
    );
  }

  return out;
}
