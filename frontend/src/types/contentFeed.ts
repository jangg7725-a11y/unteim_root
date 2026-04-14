export type FeedTabTarget = "input" | "report" | "counsel";

export type FeedItemAction =
  | {
      type: "tab";
      target: FeedTabTarget;
      /** 리포트 월운: 해당 달만 먼저 보기 (1–12) */
      focusMonth?: number;
      reportAnchor?: string;
    }
  | { type: "none"; target?: undefined };

/** 피드·탐색에서 리포트 탭으로 이동 시 함께 전달 (월 포커스·스크롤 앵커) */
export type FeedNavigateMeta = {
  /** 1–12: 월운 북에서 해당 월만 먼저 표시 */
  focusMonth?: number;
  /** 리포트 화면 내 섹션 id — 로드 후 스크롤 */
  reportAnchor?: string;
};

export type FeedCategory = {
  id: string;
  label: string;
  icon: string;
};

export type FeedItem = {
  id: string;
  categoryIds: string[];
  theme: string;
  badge?: string;
  bannerTitle?: string;
  title: string;
  description: string;
  likes?: number | null;
  views?: number | null;
  points?: number | null;
  action: FeedItemAction;
};

export type ContentFeedData = {
  _comment?: string;
  feedVersion: string;
  updatedAt?: string;
  categories: FeedCategory[];
  items: FeedItem[];
};
