import type { MonthlyFortuneEngineMonth } from "@/types/report";

function isPlaceholderPillar(s: string | undefined): boolean {
  const t = (s || "").replace(/\s/g, "").trim();
  return !t || t === "—" || t === "-" || t === "–";
}

/**
 * 엔진 원문(세운·합충·공망·용신 등) 대신, 사용자용 짧은 설명 문단을 만든다.
 * 기술 용어·원문은 노출하지 않고, 데이터 유무만 반영한다.
 */
export function buildMonthlyFriendlyParagraphs(m: MonthlyFortuneEngineMonth): string[] {
  const out: string[] = [];
  const hasSeun = !isPlaceholderPillar(m.seunPillar);
  const hasDae = !isPlaceholderPillar(m.daewoonPillar);

  if (!hasSeun && !hasDae) {
    out.push(
      "올해·장기 운의 흐름과 직접 겹치는 신호는 이번 달에는 크게 드러나지 않는 편이에요. 그래서 연간 이야기보다는 **위에 적힌 이 달의 월주**를 기준으로 삼펴보시면 됩니다."
    );
  } else {
    out.push(
      "이번 달에는 **이전 해의 기운**과 **지금의 큰 운의 흐름**이 함께 겹쳐 읽혀요. 한 달만의 이야기보다 **조금 더 긴 호흡**으로 받아들이시면 좋습니다."
    );
  }

  const hasHints = m.interactionHints.some((h) => h.trim());
  if (hasHints) {
    out.push(
      "이번 달에는 **사람·환경과의 맞물림**이 조금 더 드러날 수 있어요. 구체적인 흐름은 아래 **전체 흐름**과 **명리 해석**에서 풀어 드립니다."
    );
  } else {
    out.push(
      "사람·일·관계에서 갑자기 부딪히거나 묶이는 신호는 약한 편이라, 상황이 급격히 바뀌기보다는 **지금까지의 패턴**을 유지하는 쪽에 가깝습니다."
    );
  }

  const gm = (m.gongmangLine || "").trim();
  if (gm) {
    out.push(
      "가끔 ‘허전함’이나 ‘미뤄짐’이 느껴질 수 있어요. 이런 달에는 **지연**보다는 **이미 나타난 흐름과 역할**을 먼저 보는 편이 이해하기 쉽습니다."
    );
  }

  const ys = (m.yongshinLine || "").trim();
  if (ys) {
    out.push(
      "이번 달에는 **나에게 맞는 큰 방향**을 먼저 정한 뒤, 그보다 작은 보조 행동을 얹는 식이 잘 맞습니다. 아래 기회·행동 안내에서도 이어집니다."
    );
  }

  return out;
}
