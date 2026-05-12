import type { SajuReportData } from "@/types/report";

export type TodayPointResult = {
  /** 메인 한 줄 요약 (굵게 표시) */
  headline: string;
  /** 보조 한 줄 — 있으면 표시 */
  sub?: string;
};

function trim(text: string, max: number): string {
  const t = text.trim();
  return t.length <= max ? t : t.slice(0, max) + "…";
}

/**
 * 카테고리 ID + 사주 원국 리포트 → 오늘의 짧은 포인트(1~2줄)
 * monthlyFortune(유료 월운)은 사용하지 않습니다.
 * 근거: narrativeSlots(원국 기반), sajuOverview(사주 기둥·대운), personality/work/money/health(분석 요약)
 */
export function deriveTodayPoint(
  categoryId: string,
  report: SajuReportData | null,
): TodayPointResult {
  if (!report) {
    return {
      headline: "사주 분석을 완료하면 오늘의 포인트를 확인할 수 있어요.",
      sub: "아래 '분석 시작'을 눌러보세요.",
    };
  }

  const slots = report.narrativeSlots;
  const overview = report.sajuOverview;

  switch (categoryId) {
    case "m2": {
      // 오늘의 리듬 — 일간·12운성 기반
      const day = overview?.pillars?.day;
      if (day?.gan && day?.ganOhaeng && day?.twelve) {
        return {
          headline: `일간 ${day.gan}(${day.ganOhaeng}) 기질 — 오늘은 '${day.twelve}' 에너지 단계입니다.`,
          sub: "내 흐름에 맞는 하루 배치를 확인해 보세요.",
        };
      }
      const p = report.personality;
      if (p) {
        return {
          headline: trim(p, 55),
          sub: "자세히 보면 오늘의 리듬이 보여요.",
        };
      }
      return { headline: "오늘 나의 에너지 리듬을 사주 기반으로 확인해 보세요." };
    }

    case "m3": {
      // 관계·인연 — narrativeSlots.relation
      const rel = slots?.relation;
      const hint =
        rel?.oheng?.core_theme ||
        rel?.oheng?.strength ||
        rel?.daymaster?.care_tip;
      if (hint) {
        return {
          headline: trim(hint, 60),
          sub: "지금 곁의 관계 흐름을 자세히 알아볼까요?",
        };
      }
      return { headline: "나의 관계 기질과 지금 인연의 흐름을 확인해 보세요." };
    }

    case "m4": {
      // 일·재물 — narrativeSlots.money + career
      const moneyHint =
        slots?.money?.daymaster?.money_trait ||
        slots?.money?.oheng?.strategy ||
        slots?.money?.oheng?.advice;
      const careerHint =
        slots?.career?.oheng?.strategy ||
        slots?.career?.daymaster?.care_tip;
      if (moneyHint) {
        return {
          headline: trim(moneyHint, 60),
          sub: careerHint ? trim(careerHint, 50) : "일과 재물 흐름을 더 자세히 확인해 보세요.",
        };
      }
      if (careerHint) {
        return { headline: trim(careerHint, 60), sub: "재물 흐름과 함께 자세히 살펴보세요." };
      }
      const w = report.work;
      if (w) return { headline: trim(w, 60), sub: "오늘 일·재물 흐름을 더 자세히 확인해 보세요." };
      return { headline: "오늘 일과 재물 흐름을 사주 기반으로 점검해 보세요." };
    }

    case "m5": {
      // 마음·성향 — personality + narrativeSlots.health(정서)
      const p = report.personality;
      const emotionHint =
        slots?.health?.daymaster?.health_tendency ||
        slots?.health?.oheng?.care;
      if (p) {
        return {
          headline: trim(p, 60),
          sub: emotionHint
            ? trim(emotionHint, 50)
            : "내 반응 패턴의 이유를 자세히 알아보세요.",
        };
      }
      return { headline: "나의 기질과 반응 패턴을 사주 기반으로 살펴보세요." };
    }

    case "m6": {
      // 실천 한 줄 — 원국 기반 행동 조언 (월운 X)
      const action =
        slots?.career?.oheng?.advice ||
        slots?.money?.oheng?.advice ||
        slots?.health?.oheng?.advice;
      const careTip =
        slots?.career?.daymaster?.care_tip ||
        slots?.health?.daymaster?.care_tip;
      if (action) {
        return { headline: trim(action, 65), sub: "오늘 딱 한 가지, 실천해 보세요." };
      }
      if (careTip) {
        return { headline: trim(careTip, 65), sub: "이것 하나만 챙겨도 흐름이 달라집니다." };
      }
      const p = report.personality;
      if (p) {
        return {
          headline: `오늘 ${trim(p, 40)} — 한 가지만 실천해 보세요.`,
        };
      }
      return { headline: "오늘 딱 하나, 내 사주 기질에 맞는 행동을 골라보세요." };
    }

    case "m7": {
      // 사주 개요 — 일간 기둥 요약
      const day = overview?.pillars?.day;
      if (day?.gan && day?.ji) {
        const elem = day.ganOhaeng ? ` · ${day.ganOhaeng}` : "";
        return {
          headline: `일간 ${day.gan}${day.ji}${elem} 기질의 사주입니다.`,
          sub: "네 기둥의 전체 흐름을 한눈에 확인해 보세요.",
        };
      }
      return { headline: "나의 사주 네 기둥과 오행 분포를 한눈에 확인해 보세요." };
    }

    case "m8": {
      // 신살 하이라이트 — narrativeSlots.risk
      const risks = slots?.risk?.shinsal_risks?.filter((r) => r.found);
      if (risks?.length) {
        const r0 = risks[0];
        const label = r0.label_ko ? `${r0.label_ko} 기운이 감지됩니다.` : "주목할 신살 기운이 있습니다.";
        const msg = r0.core_message ? trim(r0.core_message, 50) : "자세한 내용을 확인해 보세요.";
        return { headline: label, sub: msg };
      }
      // separation / movement 신호
      const sep = slots?.separation;
      if (sep?.found && sep.core_message) {
        return {
          headline: trim(sep.core_message, 60),
          sub: "관련 신살 흐름을 자세히 확인해 보세요.",
        };
      }
      return { headline: "내 사주 속 특별한 신살 에너지를 확인해 보세요." };
    }

    case "m9": {
      // 대운 스냅샷 — sajuOverview.daewoon 현재 대운
      const current = overview?.daewoon?.find((d) => d.isCurrent);
      if (current?.pillar) {
        const ageRange =
          current.startAge != null && current.endAge != null
            ? ` (${current.startAge}세~${current.endAge}세)`
            : "";
        return {
          headline: `현재 ${current.pillar} 대운${ageRange} 진행 중입니다.`,
          sub: "10년 큰 흐름의 방향과 기회를 확인해 보세요.",
        };
      }
      return { headline: "앞으로 10년 대운의 큰 흐름을 확인해 보세요." };
    }

    default:
      return { headline: "사주 기반 오늘의 포인트를 확인해 보세요." };
  }
}
