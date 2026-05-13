import type { FeedNavigateMeta } from "@/types/contentFeed";

/** 클라이언트 로컬 달력 기준 현재 월(1–12) */
export function getCurrentCalendarMonth(): number {
  return new Date().getMonth() + 1;
}

export type ExploreCategoryAction =
  | { type: "report"; meta: FeedNavigateMeta }
  | { type: "counsel" }
  | { type: "input" };

/**
 * 탐색 허브 카테고리 id → 리포트 메타(월 포커스·스크롤 앵커) 또는 다른 탭.
 * 스크롤 앵커는 현재 사주 리포트 탭 DOM과 일치해야 함(미존재 시 스크롤 무반응).
 */
export function exploreActionForCategoryId(id: string): ExploreCategoryAction {
  const m = getCurrentCalendarMonth();

  switch (id) {
    case "m1":
      return { type: "report", meta: { focusMonth: m } };

    case "m2":
      return { type: "report", meta: { focusMonth: m, reportAnchor: "report-anchor-monthly" } };
    case "m3":
      return { type: "report", meta: { reportAnchor: "report-section-relation" } };
    case "m4":
      return { type: "report", meta: { focusMonth: m, reportAnchor: "report-anchor-monthly" } };
    case "m5":
    case "m6":
    case "m10":
      return { type: "report", meta: { focusMonth: m, reportAnchor: "report-anchor-monthly" } };
    case "m7":
    case "m8":
    case "m9":
      return { type: "report", meta: { focusMonth: m, reportAnchor: "report-anchor-monthly" } };

    case "l1":
      return { type: "report", meta: { reportAnchor: "report-section-relation" } };
    case "l2":
      return { type: "report", meta: { focusMonth: m } };
    case "l3":
      return { type: "report", meta: { focusMonth: m, reportAnchor: "report-anchor-monthly" } };
    case "l4":
      return { type: "report", meta: { focusMonth: m, reportAnchor: "report-anchor-monthly" } };
    case "f1":
      return { type: "report", meta: { reportAnchor: "report-section-relation" } };
    case "f2":
      return { type: "report", meta: { focusMonth: m, reportAnchor: "report-anchor-monthly" } };

    case "q1":
      return { type: "counsel" };
    case "q2":
      return { type: "report", meta: { focusMonth: m } };
    case "q3":
      return { type: "input" };
    case "q4":
      return { type: "report", meta: { focusMonth: m } };

    default:
      return { type: "report", meta: { focusMonth: m } };
  }
}
