import { useEffect, useMemo, useState } from "react";
import type { ContentFeedData, FeedItem, FeedNavigateMeta, FeedTabTarget } from "@/types/contentFeed";
import type { FortuneLinesData } from "@/types/fortuneLines";
import { loadContentFeed } from "@/services/contentFeedApi";
import { loadFortuneLines } from "@/services/fortuneLinesApi";
import { FeedDetailModal } from "./FeedDetailModal";
import "./feed.css";

const ICON_MAP: Record<string, string> = {
  sparkle: "✨",
  calendar: "📅",
  saju: "🔮",
  heart: "💕",
  work: "💼",
  mind: "🌙",
};

type Props = {
  hasBirth: boolean;
  hasReport: boolean;
  onNavigateTab: (tab: FeedTabTarget, meta?: FeedNavigateMeta) => void;
  /** 탐색 허브 안에 넣을 때 상단 안내·판본 문구 숨김 */
  embedded?: boolean;
};

export function ContentFeedPage({ hasBirth, hasReport, onNavigateTab, embedded }: Props) {
  const [data, setData] = useState<ContentFeedData | null>(null);
  const [fortuneLines, setFortuneLines] = useState<FortuneLinesData | null>(null);
  const [loadError, setLoadError] = useState(false);
  const [cat, setCat] = useState<string>("all");
  const [catExpanded, setCatExpanded] = useState(false);
  const [modalItem, setModalItem] = useState<FeedItem | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const [d, fl] = await Promise.all([loadContentFeed(), loadFortuneLines()]);
      if (!cancelled) {
        setData(d);
        setFortuneLines(fl);
        setLoadError(d.items.length === 0 && d.feedVersion === "fallback");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const filtered = useMemo(() => {
    if (!data?.items) return [];
    if (cat === "all") return data.items;
    return data.items.filter((it) => it.categoryIds.includes(cat));
  }, [data, cat]);

  return (
    <div className={`feed-page${embedded ? " feed-page--embedded" : ""}`}>
      {!embedded && (
        <p className="feed-page__intro">
          매달 바뀌는 주제 카드입니다. 카드를 누르면 안내와 함께 사주 입력·리포트·상담으로 이동할 수 있습니다.
        </p>
      )}
      {data && !embedded && (
        <p className="feed-page__version">
          콘텐츠 판본 {data.feedVersion}
          {data.updatedAt ? ` · ${data.updatedAt}` : ""}
        </p>
      )}

      {data && data.categories.length > 0 && (
        <div className="feed-cat-wrap">
          {!catExpanded ? (
            <div className="feed-cat-bar">
              <div
                className="feed-cat feed-cat--strip"
                role="tablist"
                aria-label="카테고리"
              >
                {data.categories.map((c) => (
                  <button
                    key={c.id}
                    type="button"
                    role="tab"
                    aria-selected={cat === c.id}
                    className={`feed-cat__btn${cat === c.id ? " feed-cat__btn--on" : ""}`}
                    onClick={() => setCat(c.id)}
                  >
                    <span className="feed-cat__ico" aria-hidden>
                      {ICON_MAP[c.icon] ?? "·"}
                    </span>
                    {c.label}
                  </button>
                ))}
              </div>
              <button
                type="button"
                className="feed-cat-expand"
                aria-expanded={false}
                aria-label="카테고리 전체 보기"
                onClick={() => setCatExpanded(true)}
              >
                <span className="feed-cat-expand__chev" aria-hidden>
                  ▼
                </span>
              </button>
            </div>
          ) : (
            <div
              id="feed-cat-panel"
              className="feed-cat-panel"
              role="region"
              aria-label="카테고리 전체"
            >
              <button
                type="button"
                className="feed-cat-collapse"
                aria-expanded={true}
                aria-label="카테고리 접기"
                onClick={() => setCatExpanded(false)}
              >
                <span className="feed-cat-collapse__chev" aria-hidden>
                  ▲
                </span>
              </button>
              <div className="feed-cat-grid" role="tablist" aria-label="카테고리">
                {data.categories.map((c) => (
                  <button
                    key={c.id}
                    type="button"
                    role="tab"
                    aria-selected={cat === c.id}
                    className={`feed-cat__btn feed-cat__btn--grid${cat === c.id ? " feed-cat__btn--on" : ""}`}
                    onClick={() => {
                      setCat(c.id);
                      setCatExpanded(false);
                    }}
                  >
                    <span className="feed-cat__ico" aria-hidden>
                      {ICON_MAP[c.icon] ?? "·"}
                    </span>
                    {c.label}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {loadError && (
        <p className="feed-empty">콘텐츠 목록을 불러오지 못했습니다. <code>public/data/content_feed.json</code> 파일을 확인해 주세요.</p>
      )}

      <div className="feed-list">
        {filtered.map((item) => (
          <button
            key={item.id}
            type="button"
            className="feed-card"
            onClick={() => setModalItem(item)}
          >
            <div className={`feed-card__banner feed-card__banner--${item.theme || "violet"}`}>
              {item.badge && <span className="feed-card__badge">{item.badge}</span>}
              <h3 className="feed-card__overlay-title">{item.bannerTitle || item.title}</h3>
            </div>
            <div className="feed-card__body">
              <p className="feed-card__title">{item.title}</p>
              <div className="feed-card__meta">
                {item.views != null && item.views > 0 && (
                  <span aria-label="조회">
                    👁 {item.views.toLocaleString("ko-KR")}
                  </span>
                )}
                {item.likes != null && item.likes > 0 && (
                  <span aria-label="좋아요">
                    ♥ {item.likes.toLocaleString("ko-KR")}
                  </span>
                )}
                {item.points != null && item.points > 0 && (
                  <span aria-label="포인트">
                    🪙 {item.points.toLocaleString("ko-KR")}
                  </span>
                )}
              </div>
            </div>
          </button>
        ))}
      </div>

      {data && filtered.length === 0 && !loadError && (
        <p className="feed-empty">이 카테고리에 표시할 카드가 없습니다.</p>
      )}

      <FeedDetailModal
        item={modalItem}
        open={modalItem != null}
        onClose={() => setModalItem(null)}
        onGoTab={onNavigateTab}
        hasBirth={hasBirth}
        hasReport={hasReport}
        fortuneLines={fortuneLines}
      />
    </div>
  );
}
