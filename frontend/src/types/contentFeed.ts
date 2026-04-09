export type FeedTabTarget = "input" | "report" | "counsel";

export type FeedItemAction =
  | { type: "tab"; target: FeedTabTarget; /** 리포트 월운: 해당 달만 먼저 보기 (1–12) */ focusMonth?: number }
  | { type: "none"; target?: undefined };

/** 피드에서 탭 이동 시 함께 전달 (월 단위 월운 포커스 등) */
export type FeedNavigateMeta = {
  focusMonth?: number;
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
