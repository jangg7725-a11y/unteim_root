import { useCallback, useEffect, useMemo, useState } from "react";
import type { MonthlyFortuneEnginePayload } from "@/types/report";
import { buildMonthlyFriendlyParagraphs } from "@/utils/monthlyFortuneFriendly";
import { buildCounselorEmotionText } from "@/utils/buildCounselorEmotionText";
import { deriveMonthlyCategories, type MonthCategory, type ShinsalEntry } from "@/utils/deriveMonthlyCategories";
import { LifeEventSignalCard } from "./LifeEventSignalCard";
import "./monthly-fortune-book.css";

function BoldInline({ text }: { text: string }) {
  const parts = text.split("**");
  return (
    <>
      {parts.map((part, i) => (i % 2 === 1 ? <strong key={i}>{part}</strong> : part))}
    </>
  );
}

type Props = {
  data: MonthlyFortuneEnginePayload;
  onGoCounsel: () => void;
  monthFocus: number | null;
  onShowFullYear?: () => void;
  supplementaryIntroLine?: string | null;
};

function Stars({ score }: { score: 1 | 2 | 3 | 4 | 5 }) {
  const filled = "★".repeat(score) + "☆".repeat(5 - score);
  return <span className="mfb__stars">{filled}</span>;
}

/* 카테고리 점수 — CategoryScore = 1|2|3|4|5 */

/* 신살 아이템 */
function ShinsalItem({ item }: { item: ShinsalEntry }) {
  const badgeCls =
    item.category === "good"
      ? "mfb__si-badge--good"
      : item.category === "risk"
      ? "mfb__si-badge--risk"
      : "mfb__si-badge--caution";
  return (
    <div className="mfb__si">
      <div className="mfb__si-header">
        <span className="mfb__si-name">{item.name}</span>
        <span className={`mfb__si-badge ${badgeCls}`}>
          {item.category === "good" ? "귀인" : item.category === "risk" ? "주의" : "조심"}
        </span>
      </div>
      {item.effect && <p className="mfb__si-effect">{item.effect}</p>}
      {item.advice && <p className="mfb__si-advice">→ {item.advice}</p>}
    </div>
  );
}

/* 카테고리 카드 */
function CategoryCard({ cat }: { cat: MonthCategory }) {
  const [open, setOpen] = useState(false);
  const colorMap: Record<string, string> = {
    health: "mfb__cat-card--health",
    love: "mfb__cat-card--love",
    money: "mfb__cat-card--money",
    shinsal: "mfb__cat-card--shinsal",
    caution: "mfb__cat-card--caution",
    goodluck: "mfb__cat-card--goodluck",
  };
  const cls = `mfb__cat-card ${colorMap[cat.key] ?? ""}`;
  return (
    <div className={cls}>
      <div className="mfb__cat-card-header" onClick={() => setOpen((v) => !v)}>
        <span>{cat.emoji} {cat.title}</span>
        {cat.score != null && (
          <span className="mfb__cat-score">
            {"★".repeat(cat.score)}{"☆".repeat(5 - cat.score)}
          </span>
        )}
        <span className="mfb__cat-toggle">{open ? "−" : "+"}</span>
      </div>
      <div className="mfb__cat-card-body">
        {cat.key === "shinsal" && cat.shinsalItems && cat.shinsalItems.length > 0 ? (
          <div className="mfb__si-list">
            {cat.shinsalItems.map((item, i) => (
              <ShinsalItem key={i} item={item} />
            ))}
          </div>
        ) : (
          <>
            {cat.lines.map((line, i) => <p key={i}>{line}</p>)}
            {open && cat.caution && (
              <p className="mfb__cat-caution">{cat.caution}</p>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export function MonthlyFortuneEngine({
  data,
  onGoCounsel,
  monthFocus,
  onShowFullYear,
  supplementaryIntroLine,
}: Props) {
  const monthsSorted = useMemo(
    () => [...data.months].sort((a, b) => a.month - b.month),
    [data.months]
  );
  const total = monthsSorted.length;
  const [idx, setIdx] = useState(0);

  const focusIndex = useMemo(() => {
    if (monthFocus == null) return null;
    const i = monthsSorted.findIndex((x) => x.month === monthFocus);
    return i >= 0 ? i : null;
  }, [monthFocus, monthsSorted]);

  const singleMonthView = monthFocus != null && focusIndex != null;

  useEffect(() => {
    if (focusIndex == null) return;
    setIdx(focusIndex);
  }, [focusIndex, monthFocus]);

  const safeIdx = Math.min(idx, Math.max(0, total - 1));
  const m = monthsSorted[safeIdx];
  const pageNum = safeIdx + 1;

  const goPrev = useCallback(() => setIdx((i) => Math.max(0, i - 1)), []);
  const goNext = useCallback(() => setIdx((i) => Math.min(total - 1, i + 1)), [total]);
  const goMonth = useCallback(
    (month: number) => {
      const i = monthsSorted.findIndex((x) => x.month === month);
      if (i >= 0) setIdx(i);
    },
    [monthsSorted]
  );

  useEffect(() => {
    if (singleMonthView) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft") goPrev();
      if (e.key === "ArrowRight") goNext();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [goPrev, goNext, singleMonthView]);

  if (!m || total === 0) return null;

  const opportunityText = (m.opportunity || m.good).trim();
  const behaviorGuide = (m.behaviorGuide || "").trim();
  const elementPractice = (m.elementPractice || "").trim();
  const oneLineConclusion = (m.oneLineConclusion || "").trim();
  const bridgeText = (m.aiCounselBridge || "").trim();
  const bridgeLines = bridgeText
    .split(/\n+/)
    .map((line) => line.trim())
    .filter(Boolean);
  const shinsalHighlights = Array.isArray(m.shinsalHighlights)
    ? m.shinsalHighlights.map((x) => x.trim()).filter(Boolean).slice(0, 2)
    : [];
  const friendlyParagraphs = useMemo(() => buildMonthlyFriendlyParagraphs(m), [m]);
  const counselorLines = useMemo(() => buildCounselorEmotionText(m), [m]);
  const monthCategories = useMemo(() => deriveMonthlyCategories(m), [m]);
  const goodBullets = (m.opportunity || m.good)
    .split(/\n+/)
    .map((x) => x.replace(/^[\-\u2022]\s*/, "").trim())
    .filter(Boolean)
    .slice(0, 3);

  return (
    <section className={`mfb${singleMonthView ? " mfb--single-month" : ""}`} aria-labelledby="mfb-title">
      <div className="mfb__intro">
        <h2 id="mfb-title" className="mfb__title">
          {singleMonthView ? `${monthFocus}월의 흐름 (${data.year}년)` : `월별 운세 리포트 (${data.year}년)`}
        </h2>
        {supplementaryIntroLine ? (
          <div className="mfb__supplementary" role="note">
            <span className="mfb__supplementary-label">참고 한 줄</span>
            <p className="mfb__supplementary-text">{supplementaryIntroLine}</p>
          </div>
        ) : null}
        <p className="mfb__year-sum">{data.yearSummary}</p>
        {singleMonthView ? (
          <div className="mfb__single-banner">
            <p className="mfb__single-banner-text">
              탐색 카드 기준으로 <strong>{monthFocus}월</strong> 월운만 보여 드립니다. 연간 흐름을 보려면 아래를 눌러 주세요.
            </p>
            {onShowFullYear && (
              <button type="button" className="mfb__full-year-btn" onClick={onShowFullYear}>
                {data.year}년 전체 월운 보기
              </button>
            )}
          </div>
        ) : (
          <div className="mfb__highlights">
            <p>
              <span className="mfb__badge mfb__badge--best">기회에 유리한 달</span>
              <strong>{data.bestMonth}월</strong>
            </p>
            <p>
              <span className="mfb__badge mfb__badge--caution">점검·주의 달</span>
              <strong>{data.cautionMonth}월</strong>
            </p>
          </div>
        )}
        {!singleMonthView ? (
          <div className="mfb__month-jump" role="navigation" aria-label="월별 바로가기">
            {monthsSorted.map((x, i) => (
              <button
                key={`jump-${x.month}`}
                type="button"
                className={`mfb__month-jump-btn${i === safeIdx ? " mfb__month-jump-btn--on" : ""}`}
                onClick={() => goMonth(x.month)}
                aria-current={i === safeIdx ? "page" : undefined}
              >
                {x.month}월
              </button>
            ))}
          </div>
        ) : null}
      </div>

      <div className="mfb__book-wrap">
        <div className="mfb__book">
          <div className="mfb__book-spine" aria-hidden />
          <div className="mfb__book-inner">
            <div className="mfb__progress">
              <span>
                {singleMonthView ? `${m.month}월` : `${pageNum} / ${total} 장 · ${m.month}월`}
              </span>
              {!singleMonthView && (
                <div className="mfb__progress-dots" aria-hidden>
                  {monthsSorted.map((x, i) => (
                    <span key={x.month} className={`mfb__dot${i === safeIdx ? " mfb__dot--on" : ""}`} />
                  ))}
                </div>
              )}
            </div>

            <header className="mfb__page-head">
              <div>
                <h3 className="mfb__page-month">
                  {m.month}월
                  <span className="mfb__page-year">{data.year}년</span>
                </h3>
              </div>
              <Stars score={m.score} />
            </header>

            {/* ── 월주 기본 정보 줄 ── */}
            <p className="mfb__pillar-line">
              월주 <strong>{m.monthPillar || "—"}</strong> · 월간 십신 <strong>{m.stemTenGod}</strong> · 지지
              본기 십신 <strong>{m.branchTenGodMain}</strong> · 12운성 <strong>{m.twelveStage}</strong>
            </p>

            {/* ── 격국 ── */}
            {m.geukgukName ? (
              <div className="mfb__geukguk">
                <span className="mfb__geukguk-label">격국</span>
                <strong className="mfb__geukguk-name">{m.geukgukName}</strong>
                {m.geukgukCore ? <p className="mfb__geukguk-core">{m.geukgukCore}</p> : null}
                {m.geukgukBehavior ? <p className="mfb__geukguk-behavior">{m.geukgukBehavior}</p> : null}
              </div>
            ) : null}

            {/* ── 대운 흐름 ── */}
            {m.daewoonFlowLabel ? (
              <div className="mfb__daewoon-flow">
                <span className="mfb__daewoon-flow-label">대운 흐름</span>
                <strong>{m.daewoonFlowLabel}</strong>
                {m.daewoonFlowEra ? <p>{m.daewoonFlowEra}</p> : null}
                {m.daewoonFlowEnergy ? <p>{m.daewoonFlowEnergy}</p> : null}
              </div>
            ) : null}

            {/* ── 삼재 경고 ── */}
            {m.samjaeStatus?.is_samjae ? (
              <div className="mfb__samjae">
                <span className="mfb__samjae-badge">⚠️ 삼재</span>
                <span className="mfb__samjae-stage">{m.samjaeStatus.stage ?? "일반"} 삼재년</span>
                {m.samjaeStatus.bok_samjae && <span className="mfb__samjae-bok">복삼재</span>}
              </div>
            ) : null}

            {/* ── 공망 ── */}
            {m.gongmangLine ? (
              <p className="mfb__gongmang-line">🌀 {m.gongmangLine}</p>
            ) : null}

            {/* ── 신살 칩 ── */}
            {shinsalHighlights.length > 0 ? (
              <div className="mfb__shinsal-chips" aria-label="이번 달 신살 핵심">
                {shinsalHighlights.map((chip, i) => {
                  const isGood = chip.startsWith("귀인:");
                  const cls = isGood ? "mfb__shinsal-chip mfb__shinsal-chip--good" : "mfb__shinsal-chip mfb__shinsal-chip--risk";
                  return (
                    <span key={`${chip}-${i}`} className={cls}>
                      {chip}
                    </span>
                  );
                })}
              </div>
            ) : null}

            {/* ── 이달의 핵심 ── */}
            <div className="mfb__friendly" aria-label="이달의 핵심">
              <p className="mfb__section-title mfb__section-title--friendly">이달의 핵심</p>
              {friendlyParagraphs.map((para, i) => (
                <p key={i} className="mfb__friendly-text">
                  <BoldInline text={para} />
                </p>
              ))}
              {m.interactionHints && m.interactionHints.length > 0 && (
                <div className="mfb__interaction-hints">
                  {m.interactionHints.slice(0, 3).map((hint, i) => (
                    <span key={i} className="mfb__interaction-chip">{hint}</span>
                  ))}
                </div>
              )}
            </div>

            {/* ── 인생 사건 신호 ── */}
            {m.life_event_signals && m.life_event_signals.length > 0 && (
              <LifeEventSignalCard events={m.life_event_signals} month={m.month} />
            )}

            {/* ── 이달의 한줄 결론 ── */}
            {oneLineConclusion ? (
              <p className="mfb__one-line">
                <strong>이달의 한줄 결론</strong> {oneLineConclusion}
              </p>
            ) : null}

            {/* ── 이달의 카테고리별 운세 ── */}
            <div className="mfb__cat-section">
              <p className="mfb__cat-title">이달의 카테고리별 운세</p>
              <div className="mfb__cat-grid">
                {monthCategories.map((cat) => (
                  <CategoryCard key={cat.key} cat={cat} />
                ))}
              </div>
            </div>

            {/* ── 행동 가이드 (잘 풀리는 방향 포함) ── */}
            {(goodBullets.length > 0 || opportunityText || behaviorGuide) ? (
              <div className="mfb__behavior">
                <p className="mfb__section-title">행동 가이드</p>
                <div className="mfb__good-bullets">
                  {(goodBullets.length > 0
                    ? goodBullets
                    : opportunityText.split(/\n+/).map((x) => x.replace(/^[\-•]\s*/, "").trim()).filter(Boolean)
                  ).map((line, i) => (
                    <p key={`gb-${i}`} className="mfb__good-bullet-item">
                      <span className="mfb__good-check" aria-hidden="true">✓</span>
                      {line}
                    </p>
                  ))}
                </div>
                {behaviorGuide ? (
                  <div className="mfb__narrative mfb__narrative--behavior">
                    {behaviorGuide.split(/\n+/).map((line, i) => (
                      <p key={i}>{line}</p>
                    ))}
                  </div>
                ) : null}
              </div>
            ) : null}

            {/* ── 감정 코칭 (상담가 어투) ── */}
            {counselorLines.length > 0 ? (
              <div className="mfb__emotion">
                <p className="mfb__section-title mfb__section-title--counsel">💬 감정 코칭</p>
                <div className="mfb__counsel-body">
                  {counselorLines.map((line, i) => (
                    <p key={i} className={`mfb__counsel-line mfb__counsel-line--${
                      i === 0 ? "open" :
                      i === counselorLines.length - 1 ? "close" : "mid"
                    }`}>
                      {line}
                    </p>
                  ))}
                </div>
              </div>
            ) : null}

            {/* ── 오행 실천법 ── */}
            {elementPractice ? (
              <div className="mfb__element">
                <p className="mfb__section-title">오행 실천법</p>
                <div className="mfb__narrative mfb__narrative--element">
                  {elementPractice.split(/\n+/).map((line, i) => (
                    <p key={i}>{line}</p>
                  ))}
                </div>
              </div>
            ) : null}

            {/* ── AI 상담 연결 ── */}
            {bridgeText ? (
              <div className="mfb__bridge" role="note">
                <p className="mfb__section-title">AI 상담 연결</p>
                {bridgeLines.map((line, i) => (
                  <p key={i}>{line}</p>
                ))}
                <button type="button" className="mfb__counsel-btn" onClick={onGoCounsel}>
                  AI 상담 시작하기
                </button>
              </div>
            ) : null}

            {!singleMonthView ? (
              <nav className="mfb__nav" aria-label="월 넘기기">
                <button type="button" className="mfb__nav-btn" onClick={goPrev} disabled={safeIdx <= 0}>
                  ← 이전 달
                </button>
                <button type="button" className="mfb__nav-btn" onClick={goNext} disabled={safeIdx >= total - 1}>
                  다음 달 →
                </button>
              </nav>
            ) : null}
          </div>
        </div>
      </div>
    </section>
  );
}
