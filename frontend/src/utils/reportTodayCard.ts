import type { SajuReportData } from "@/types/report";
import type { TodayFortuneData } from "@/components/TodayFortuneCard";

export function deriveTodayFortuneFromReport(report: SajuReportData | null): TodayFortuneData | null {
  const months = report?.monthlyFortune?.months;
  if (!months?.length) return null;
  const cm = new Date().getMonth() + 1;
  const m = months.find((x) => x.month === cm);
  if (!m) return null;

  const flow = (m.overallFlow || m.flow || "").trim();
  const actionPoint = (
    m.oneLineConclusion ||
    m.actionGuide ||
    m.action ||
    m.behaviorGuide ||
    ""
  ).trim();
  const pt = Array.isArray(m.patternTop) ? m.patternTop.map((s) => String(s).trim()).filter(Boolean) : [];
  const keywords: [string, string, string] =
    pt.length >= 3
      ? [pt[0], pt[1], pt[2]]
      : pt.length === 2
        ? [pt[0], pt[1], "리듬"]
        : pt.length === 1
          ? [pt[0], "균형", "정리"]
          : ["균형", "리듬", "정리"];

  const emotion = (m.emotionCoaching || m.behaviorGuide || "").trim();

  return {
    flow: flow || "이번 달 월운 요약을 바탕으로 오늘의 리듬을 점검해 보세요.",
    stars: m.score,
    actionPoint: actionPoint || "한 가지 우선순위만 정하고, 나머지는 유연하게 조정해 보세요.",
    keywords,
    lucky: {
      color: "참고",
      number: String(cm),
      direction: "—",
      item: "기록",
    },
    emotionCoaching: emotion || "오늘은 속도보다 방향을 한 번 확인해 보는 것이 도움이 될 수 있어요.",
  };
}
