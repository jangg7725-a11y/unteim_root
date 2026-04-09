import type { ContentFeedData } from "@/types/contentFeed";

const FALLBACK: ContentFeedData = {
  feedVersion: "fallback",
  categories: [{ id: "all", label: "전체", icon: "sparkle" }],
  items: [],
};

/**
 * `/data/content_feed.json` — `public/data/content_feed.json`을 월별로 교체하면 피드가 갱신됩니다.
 */
export async function loadContentFeed(): Promise<ContentFeedData> {
  const base = import.meta.env.BASE_URL || "/";
  const root = base.endsWith("/") ? base : `${base}/`;
  const url = `${root}data/content_feed.json`;
  try {
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) return FALLBACK;
    const data = (await res.json()) as ContentFeedData;
    if (!data?.items || !data?.categories) return FALLBACK;
    return data;
  } catch {
    return FALLBACK;
  }
}
