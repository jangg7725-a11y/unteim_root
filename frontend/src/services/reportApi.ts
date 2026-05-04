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

function simplifyReportCopy(text: string, month?: number): string {
  let out = String(text || "").trim();
  if (!out) return out;

  const mo = month && month >= 1 && month <= 12 ? `${month}월` : "이번 달";
  // 과거 '지지' 일괄 치환 잔재 문구 정리
  out = out.replace(/생활 패턴 관계로는/g, "이번 달의 기운과 나의 흐름을 함께 보면");

  // 사용자가 이해하기 어려운 명리 용어 패턴을 생활어로 변환(월 표기로 달별 구분)
  out = out.replace(
    /월간을 일간이 십신으로 보면\s*([^\s.]+)\s*에 해당합니다\.?/g,
    `${mo}에는 책임·관계·성과 중 어디에 힘이 실리는지가 분명해질 수 있습니다.`
  );
  out = out.replace(
    /지지를 일간에 대해 보면\s*12운성은\s*([^\s.]+)\s*에 놓입니다\.?/g,
    () => monthlyEnergyLine(month)
  );
  out = out.replace(
    /용신·희신·기신 관점에서는[^.]*\./g,
    `${mo}에는 나에게 맞는 방식은 살리고, 무리한 선택은 줄이는 운영이 유리합니다.`
  );
  out = out.replace(
    /용신\([^)]+\)·희신\([^)]+\)·기신\([^)]+\)와의 관계를 보면,?/g,
    "나에게 맞는 흐름과 주의할 흐름을 함께 보면,"
  );

  // 용어명 대신 '역할'이 먼저 보이도록 치환
  out = out.replace(
    /오행/g,
    "에너지 균형(무엇이 과하고 부족한지 보여주는 기준)"
  );
  out = out.replace(/월간 십신/g, "이번 달 핵심 성향");
  out = out.replace(
    /십신/g,
    "행동 성향 신호(어떤 방식으로 반응하는지 보여주는 기준)"
  );
  out = out.replace(
    /신살/g,
    "상황 신호(도움·주의가 들어오기 쉬운 장면을 알려주는 기준)"
  );
  out = out.replace(
    /12운성/g,
    "에너지 단계(지금 밀어붙일지 정리할지 알려주는 기준)"
  );
  out = out.replace(/월간/g, "이번 달 흐름");
  out = out.replace(/용신/g, "도움 되는 방향");
  out = out.replace(/희신/g, "보조되는 방향");
  out = out.replace(/기신/g, "주의할 방향");
  out = out.replace(/지장간/g, "숨은 패턴");
  out = out.replace(/이 호흡에 맞춰 속도를 조절할수록/g, "일정을 촘촘히 잡기보다 중요한 일 1~2개에 집중할수록");
  out = out.replace(/이 호흡에 맞춰/g, `${mo} 흐름에 맞춰`);
  out = out.replace(/속도 조절이 중요합니다\./g, "무리하게 밀어붙이기보다 우선순위를 줄여 진행하는 것이 중요합니다.");
  out = out.replace(/^이번 달은 에너지의 오르내림이 뚜렷해/g, `${mo}에는 에너지와 컨디션이 오르내리기 쉽습니다`);
  out = out.replace(
    /이번 달은 체력과 집중의 오르내림이 비교적 뚜렷할 수 있어, 일정을 촘촘히 잡기보다 중요한 일 1~2개에 집중하는 편이 유리합니다\./g,
    monthlyEnergyLine(month)
  );
  out = out.replace(
    /이번 달은 일정을 촘촘히 잡기보다 중요한 일 1~2개에 집중할수록 성과와 컨디션의 균형이 맞아갑니다\./g,
    monthlyEnergyLine(month)
  );
  out = out.replace(
    /말 한마디에 [‘'"]?역할[’'"]?을 붙이면 오해가 줄어듭니다\./g,
    "말을 시작할 때 이 말의 목적을 먼저 밝혀주세요. 예를 들어 지시인지, 부탁인지, 공유인지 먼저 말하면 상대가 의도를 바로 이해해 오해가 줄어듭니다."
  );
  out = out.replace(
    /대화 창구를 맞추면/g,
    "연락 방식(전화/메신저/대면)과 대화 목적을 먼저 맞추면"
  );
  out = out.replace(
    /관계 장면을 보면/g,
    "관계에서는 먼저 상황을 정리해서 보면"
  );
  out = out.replace(
    /감정보다 역할·우선순위를 먼저 정리하면 실수가 줄어들 수 있습니다\./g,
    "감정이 올라와도 바로 반응하지 말고, 지금 무엇을 먼저 해야 하는지부터 정리해 보세요. 이 순서만 지켜도 실수가 크게 줄어듭니다."
  );
  out = out.replace(
    /조건을 분명히가 신뢰를 만듭니다\./g,
    "조건을 말할 때는 기간, 금액, 책임 범위를 구체적으로 확인해 주세요. 이렇게 해야 서로 기대가 맞고 신뢰가 유지됩니다."
  );
  const gmStableLine = "이번 달은 흐름이 끊기기보다 사람·관계·일의 변화가 더 크게 작용하며, 새로운 사람이 들어오거나 기존 관계가 정리될 수 있습니다.";
  const gmMonthlyMap: Record<number, string> = {
    1: "1월은 사람·일정 변화가 함께 들어오는 달이라, 새 연결이 생기거나 기존 관계 정리가 나타날 수 있습니다.",
    2: "2월은 협업·관계 조정 이슈가 먼저 올라오기 쉬워, 새 인연이 붙거나 역할 정리가 진행될 수 있습니다.",
    3: "3월은 사람과 일의 속도가 빨라져 관계 온도 변화가 크게 느껴질 수 있어, 기존 연결 재정리가 필요할 수 있습니다.",
    4: "4월은 일정 재배치와 함께 관계 변화도 같이 들어오기 쉬워, 새 인연 형성 또는 기존 흐름 정리가 생길 수 있습니다.",
    5: "5월은 관계 피로와 업무 변화가 겹치기 쉬워, 사람 정리와 역할 재조정이 동시에 나타날 수 있습니다.",
    6: "6월은 결정 이슈가 늘면서 사람·일 변화가 함께 작동해, 연결 구조가 다시 짜이는 장면이 생길 수 있습니다.",
    7: "7월은 성과 기회와 함께 관계 재정렬도 들어오는 달이라, 새로운 협업이나 기존 관계 정리가 나타날 수 있습니다.",
    8: "8월은 핵심 과제 집중 구간이면서 사람·일 변화도 크게 체감되어, 연결 구조 재정리가 나타날 수 있습니다.",
    9: "9월은 변수 대응 과정에서 사람·관계·일 변화가 크게 느껴져, 관계 거리 조정이나 재정리가 나타날 수 있습니다.",
    10: "10월은 마감·정리 흐름과 함께 사람 관계도 정돈되는 달이라, 기존 연결 정리가 자연스럽게 진행될 수 있습니다.",
    11: "11월은 체력 리듬 변화와 함께 대인 관계도 재조정되기 쉬워, 필요한 관계만 남기고 정리하는 흐름이 생길 수 있습니다.",
    12: "12월은 한 해 마무리와 함께 사람·일 관계도 정리되는 달이라, 새 연결보다 기존 흐름 정돈이 두드러질 수 있습니다.",
  };
  out = out.replace(
    new RegExp(gmStableLine.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "g"),
    gmMonthlyMap[month ?? 0] || `${mo}에는 사람·관계·일 변화가 함께 들어와 연결 구조가 재정리될 수 있습니다.`
  );
  out = out.replace(
    /이번 달은\s*흐름이\s*끊기기보다\s*사람·관계·일의\s*변화가\s*더\s*크게\s*작용하며,\s*새로운\s*사람이\s*들어오거나\s*기존\s*관계가\s*정리될\s*수\s*있습니다\./g,
    gmMonthlyMap[month ?? 0] || `${mo}에는 사람·관계·일 변화가 함께 들어와 연결 구조가 재정리될 수 있습니다.`
  );

  // 같은 문장이 반복될 때 1회만 남긴다.
  const sentenceParts = out
    .split(/(?<=[.!?])\s+/)
    .map((s) => s.trim())
    .filter(Boolean);
  if (sentenceParts.length > 1) {
    const deduped: string[] = [];
    const seen = new Set<string>();
    for (const s of sentenceParts) {
      const key = s.replace(/\s+/g, " ");
      if (!seen.has(key)) {
        seen.add(key);
        deduped.push(s);
      }
    }
    out = deduped.join(" ");
  }

  return out;
}

function monthlyEnergyLine(month?: number): string {
  const m = Number(month || 0);
  const lines: Record<number, string> = {
    1: "1월은 리듬을 새로 만드는 달이라, 시작한 일을 짧게 끊어 완료하는 방식이 잘 맞습니다.",
    2: "2월은 협업·약속이 늘기 쉬워, 중요한 일정을 먼저 확정해 두면 피로를 줄일 수 있습니다.",
    3: "3월은 속도가 붙는 만큼 실수도 늘기 쉬워, 검토 시간을 미리 확보하는 편이 유리합니다.",
    4: "4월은 일정이 겹치기 쉬우니, 하루 핵심 1~2개만 끝내는 운영이 더 안정적입니다.",
    5: "5월은 대인 피로가 쌓이기 쉬워, 집중 시간과 회복 시간을 명확히 나눠 쓰는 것이 좋습니다.",
    6: "6월은 판단해야 할 일이 많아지는 달이라, 결정을 서두르지 않고 순서를 정하는 편이 맞습니다.",
    7: "7월은 성과를 만들기 좋은 달이지만 과로도 쉬워, 집중 뒤 짧은 회복 루틴을 꼭 넣어야 합니다.",
    8: "8월은 중요한 일에 힘을 모을수록 성과가 잘 나는 구간이라, 우선순위 축소가 핵심입니다.",
    9: "9월은 변수 대응이 잦을 수 있어, 여유 시간 블록을 남겨두면 컨디션을 지키기 쉽습니다.",
    10: "10월은 마감·정리 비중이 커지는 달이라, 빠르게 벌리기보다 끝내는 순서가 중요합니다.",
    11: "11월은 체력 기복이 올라오기 쉬워, 수면·식사 같은 기본 루틴 고정이 성과를 지켜줍니다.",
    12: "12월은 정리와 마무리 비중이 큰 달이라, 욕심을 줄이고 핵심 과제 완결에 집중하는 편이 좋습니다.",
  };
  return lines[m] || "이번 달은 집중과 피로의 간격을 잘 나누는 운영이 중요합니다.";
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
      const monthNum = Number(x.month) || 0;
      const moArg = monthNum >= 1 && monthNum <= 12 ? monthNum : undefined;
      return {
        month: monthNum,
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
        narrative: simplifyReportCopy(String(x.narrative ?? ""), moArg),
        flow: simplifyReportCopy(String(x.flow ?? ""), moArg),
        good: simplifyReportCopy(String(x.good ?? ""), moArg),
        caution: simplifyReportCopy(String(x.caution ?? ""), moArg),
        action: simplifyReportCopy(String(x.action ?? ""), moArg),
        overallFlow: simplifyReportCopy(pickText(x.overallFlow), moArg),
        mingliInterpretation: simplifyReportCopy(pickText(x.mingliInterpretation), moArg),
        realityChanges: simplifyReportCopy(pickText(x.realityChanges), moArg),
        coreEvents: simplifyReportCopy(pickText(x.coreEvents), moArg),
        opportunity: simplifyReportCopy(pickText(x.opportunity), moArg),
        riskPoints: simplifyReportCopy(pickText(x.riskPoints), moArg),
        actionGuide: simplifyReportCopy(pickText(x.actionGuide), moArg),
        behaviorGuide: simplifyReportCopy(pickText(x.behaviorGuide), moArg),
        emotionCoaching: simplifyReportCopy(pickText(x.emotionCoaching), moArg),
        elementPractice: simplifyReportCopy(pickText(x.elementPractice), moArg),
        oneLineConclusion: simplifyReportCopy(pickText(x.oneLineConclusion), moArg),
        aiCounselBridge: simplifyReportCopy(pickText(x.aiCounselBridge), moArg),
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

/** `/api/analyze` 타임아웃 등으로 partial 인데 12개월 엔진이 없을 때 */
export function isAnalyzeTimedOutWithoutMonthly(api: Record<string, unknown> | null | undefined): boolean {
  if (!api) return false;
  const meta = asRecord(api.meta);
  const partial = api.partial === true || meta?.partial === true;
  if (!partial) return false;
  const mf = parseMonthlyFortune(api);
  return !mf || mf.months.length === 0 || Boolean(mf.error);
}

/** localStorage 등에 남은 리포트가 ‘지연 기본본’만 있을 때 — 다시 받아야 함 */
export function isStoredReportTimedOutWithoutMonthly(report: SajuReportData | null | undefined): boolean {
  return isAnalyzeTimedOutWithoutMonthly(asRecord(report?.raw));
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

  const total2 = simplifyReportCopy(enrichHealingCard(total, dominantTenGod, "total"));
  const personality2 = simplifyReportCopy(enrichHealingCard(personality, dominantTenGod, "personality"));
  const work2 = simplifyReportCopy(enrichHealingCard(work, dominantTenGod, "work"));
  const money2 = simplifyReportCopy(enrichHealingCard(money, dominantTenGod, "money"));
  const health2 = simplifyReportCopy(enrichHealingCard(health, dominantTenGod, "health"));

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

/**
 * 로컬(vite proxy) 단일 POST용 — 길어도 같은 오리진이라 상대적으로 안정적.
 */
const ANALYZE_SYNC_TIMEOUT_MS = 480_000;

/** 원격(Render) — 짧은 POST로 job 받은 뒤 GET 폴링(프록시·브라우저 장시간 단일 연결 제한 완화) */
const ANALYZE_POLL_INTERVAL_MS = 2_000;
const ANALYZE_POLL_MAX_MS = 12 * 60 * 1_000;

function analyzeFetchAbortSignal(ms: number): { signal: AbortSignal; cancelTimer: () => void } {
  const AS = globalThis.AbortSignal;
  if (typeof AS !== "undefined" && typeof AS.timeout === "function") {
    return { signal: AS.timeout(ms), cancelTimer: () => {} };
  }
  const ac = new AbortController();
  const tid = globalThis.setTimeout(() => ac.abort(), ms);
  return {
    signal: ac.signal,
    cancelTimer: () => globalThis.clearTimeout(tid),
  };
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => globalThis.setTimeout(resolve, ms));
}

/** Chrome 등에서 흔한 `TypeError: Failed to fetch` — CORS·DNS·SSL·오프라인 등 */
function remoteNetError(apiBase: string, e: unknown): Error {
  const name = e instanceof Error ? e.name : "";
  const msg = e instanceof Error ? e.message : String(e);
  if (name === "TimeoutError" || name === "AbortError") {
    return new Error(
      "요청 시간이 초과되었습니다. Render 무료 플랜은 첫 응답이 매우 느릴 수 있습니다. 잠시 후 다시 시도해 주세요."
    );
  }
  const low = msg.toLowerCase();
  if (e instanceof TypeError || low.includes("failed to fetch") || low.includes("networkerror")) {
    return new Error(
      `브라우저가 API(${apiBase})에 연결하지 못했습니다. ` +
        `로컬(localhost)은 Vite가 같은 주소로 프록시해 주지만, Pages는 **다른 도메인(Render)** 으로 요청합니다. ` +
        `Render 웹 서비스 환경 변수 **CORS_ORIGINS**에 **정확히** 이 사이트 주소를 넣었는지 확인하세요. 예: https://unteim-root.pages.dev ` +
        `(끝 슬래시 없음, 여러 개면 쉼표로 구분). 배포 후 API를 재시작·재배포했는지도 확인해 주세요.`
    );
  }
  return e instanceof Error ? e : new Error("리포트 요청 중 오류가 발생했습니다.");
}

async function parseAnalyzeOkResponse(res: Response): Promise<SajuReportData> {
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
  return finalizeAnalyzeRecord(asRecord(json));
}

function buildAnalyzeBody(birth: BirthInputPayload): AnalyzeRequest {
  return {
    name: "",
    sex: birth.gender === "male" ? "남자" : "여자",
    birth: `${birth.date} ${birth.time}`,
    calendar: birth.calendarApi,
  };
}

function finalizeAnalyzeRecord(record: Record<string, unknown> | null): SajuReportData {
  if (!record) {
    throw new Error("리포트 응답 형식이 올바르지 않습니다.");
  }
  if (isAnalyzeTimedOutWithoutMonthly(record)) {
    throw new Error(
      "상세 분석이 시간 안에 끝나지 않아 월별 리포트를 받지 못했습니다. 잠시 후 다시 시도하거나 「리포트 다시 생성」을 눌러 주세요. 호스팅(Render 등) API에 환경 변수 ANALYZE_FULL_TIMEOUT_SEC=420 을 권장합니다."
    );
  }
  return pickSection(record);
}

/** Vite 프록시 → 로컬 API, 한 번의 POST */
async function fetchSajuReportLocalSync(birth: BirthInputPayload): Promise<SajuReportData> {
  const body = buildAnalyzeBody(birth);
  const { signal, cancelTimer } = analyzeFetchAbortSignal(ANALYZE_SYNC_TIMEOUT_MS);
  let res: Response;
  try {
    res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal,
    });
  } catch (e) {
    const name = e instanceof Error ? e.name : "";
    if (name === "TimeoutError" || name === "AbortError") {
      throw new Error(
        "요청 시간이 초과되어 리포트를 받지 못했습니다. 잠시 후 「리포트 다시 생성」을 눌러 주세요."
      );
    }
    throw e instanceof Error ? e : new Error("리포트 요청 중 오류가 발생했습니다.");
  } finally {
    cancelTimer();
  }
  return parseAnalyzeOkResponse(res);
}

/** 구버전 Render(비동기 엔드포인트 없음) — 긴 단일 POST */
async function fetchSajuReportRemoteSinglePost(birth: BirthInputPayload, base: string): Promise<SajuReportData> {
  const body = buildAnalyzeBody(birth);
  const url = `${base}/api/analyze`;
  const { signal, cancelTimer } = analyzeFetchAbortSignal(ANALYZE_SYNC_TIMEOUT_MS);
  let res: Response;
  try {
    res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal,
    });
  } catch (e) {
    throw remoteNetError(base, e);
  } finally {
    cancelTimer();
  }
  return parseAnalyzeOkResponse(res);
}

/** Render 등 원격 — 비동기 job + 폴링 */
async function fetchSajuReportRemotePolling(birth: BirthInputPayload): Promise<SajuReportData> {
  const base = getApiBase();
  if (typeof window !== "undefined" && window.location.protocol === "https:" && base.startsWith("http:")) {
    throw new Error(
      "VITE_API_BASE_URL 이 http 로 되어 있어 HTTPS 사이트에서 차단됩니다. Render 주소를 https://… 로 바꾼 뒤 Pages를 다시 빌드하세요."
    );
  }
  const body = buildAnalyzeBody(birth);
  const startUrl = `${base}/api/analyze-async`;
  const postSig = analyzeFetchAbortSignal(90_000);
  let startRes: Response;
  try {
    startRes = await fetch(startUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: postSig.signal,
    });
  } catch (e) {
    throw remoteNetError(base, e);
  } finally {
    postSig.cancelTimer();
  }

  const startText = await startRes.text();
  let startJson: unknown = null;
  try {
    startJson = startText ? JSON.parse(startText) : null;
  } catch {
    startJson = null;
  }
  if (!startRes.ok) {
    if (startRes.status === 404) {
      return fetchSajuReportRemoteSinglePost(birth, base);
    }
    throw new Error(
      typeof startJson === "object" && startJson && "detail" in startJson
        ? String((startJson as { detail: unknown }).detail)
        : startText || "분석 작업을 시작하지 못했습니다."
    );
  }
  const startRec = asRecord(startJson);
  const jobId = String(startRec?.job_id ?? "").trim();
  if (!jobId) {
    throw new Error("서버가 작업 ID를 주지 않았습니다. API를 최신 버전으로 배포했는지 확인해 주세요.");
  }

  const deadline = Date.now() + ANALYZE_POLL_MAX_MS;
  while (Date.now() < deadline) {
    await sleep(ANALYZE_POLL_INTERVAL_MS);
    const pollSig = analyzeFetchAbortSignal(60_000);
    let pollRes: Response;
    try {
      pollRes = await fetch(`${base}/api/analyze-job/${jobId}`, {
        method: "GET",
        signal: pollSig.signal,
      });
    } catch (e) {
      throw remoteNetError(base, e);
    } finally {
      pollSig.cancelTimer();
    }
    const pollText = await pollRes.text();
    let pollJson: unknown = null;
    try {
      pollJson = pollText ? JSON.parse(pollText) : null;
    } catch {
      pollJson = null;
    }
    if (!pollRes.ok) {
      throw new Error(
        typeof pollJson === "object" && pollJson && "detail" in pollJson
          ? String((pollJson as { detail: unknown }).detail)
          : pollText || "분석 상태를 확인하지 못했습니다."
      );
    }
    const pr = asRecord(pollJson);
    const st = String(pr?.status ?? "");
    if (st === "pending") {
      continue;
    }
    if (st === "error") {
      throw new Error(String(pr?.detail ?? "분석 중 오류가 발생했습니다."));
    }
    if (st === "done") {
      const result = asRecord(pr?.result);
      return finalizeAnalyzeRecord(result);
    }
    throw new Error(`알 수 없는 분석 상태: ${st}`);
  }

  throw new Error(
    "분석이 제한 시간 안에 끝나지 않았습니다. Render 무료 플랜은 첫 요청이 매우 느릴 수 있습니다. 잠시 후 「리포트 다시 생성」을 눌러 주세요."
  );
}

export async function fetchSajuReport(birth: BirthInputPayload): Promise<SajuReportData> {
  const base = getApiBase();
  if (!base) {
    return fetchSajuReportLocalSync(birth);
  }
  return fetchSajuReportRemotePolling(birth);
}

