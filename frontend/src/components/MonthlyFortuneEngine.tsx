import { useCallback, useEffect, useMemo, useState } from "react";
import type { MonthlyFortuneEnginePayload } from "@/types/report";
import { buildMonthlyFriendlyParagraphs } from "@/utils/monthlyFortuneFriendly";
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
  /** 피드 카드 등에서 지정한 달만 먼저 표시 */
  monthFocus: number | null;
  /** 해당 연도 12개월 전체 보기로 전환 */
  onShowFullYear?: () => void;
};

function Stars({ score }: { score: 1 | 2 | 3 | 4 | 5 }) {
  const filled = "★".repeat(score) + "☆".repeat(5 - score);
  return <span className="mfb__stars">{filled}</span>;
}

export function MonthlyFortuneEngine({ data, onGoCounsel, monthFocus, onShowFullYear }: Props) {
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

  const flowText = (m.overallFlow || m.flow).trim();
  const mingli = (m.mingliInterpretation || "").trim();
  const reality = (m.realityChanges || "").trim();
  const coreEvents = (m.coreEvents || "").trim();
  const hasCounselSections = Boolean(mingli);
  const opportunityText = (m.opportunity || m.good).trim();
  const riskText = (m.riskPoints || m.caution).trim();
  const actionText = (m.actionGuide || m.action).trim();
  const behaviorGuide = (m.behaviorGuide || "").trim();
  const emotionText = (m.emotionCoaching || "").trim();
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

  return (
    <section className={`mfb${singleMonthView ? " mfb--single-month" : ""}`} aria-labelledby="mfb-title">
      <div className="mfb__intro">
        <h2 id="mfb-title" className="mfb__title">
          {singleMonthView ? `${monthFocus}월의 흐름 (${data.year}년)` : `월별 운세 리포트 (${data.year}년)`}
        </h2>
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

            <p className="mfb__pillar-line">
              월주 <strong>{m.monthPillar || "—"}</strong> · 월간 십신 <strong>{m.stemTenGod}</strong> · 지지
              본기 십신 <strong>{m.branchTenGodMain}</strong> · 12운성 <strong>{m.twelveStage}</strong>
            </p>
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

            <div className="mfb__friendly" aria-label="이번 달 쉬운 설명">
              <p className="mfb__section-title mfb__section-title--friendly">이번 달 쉬운 설명</p>
              {friendlyParagraphs.map((para, i) => (
                <p key={i} className="mfb__friendly-text">
                  <BoldInline text={para} />
                </p>
              ))}
            </div>

            <p className="mfb__section-title">전체 흐름</p>
            <p className="mfb__narrative" style={{ marginBottom: "0.85rem" }}>
              {flowText}
            </p>

            {hasCounselSections ? (
              <>
                <p className="mfb__section-title">명리학 해석</p>
                <div className="mfb__narrative">
                  {mingli.split("\n\n").map((para, i) => (
                    <p key={i}>{para}</p>
                  ))}
                </div>

                <p className="mfb__section-title">현실 변화 예측</p>
                <div className="mfb__narrative mfb__narrative--reality">
                  {reality
                    .split(/\n+/)
                    .map((line) => line.trim())
                    .filter(Boolean)
                    .map((line, i) => (
                      <p key={i}>{line}</p>
                    ))}
                </div>

                {coreEvents ? (
                  <>
                    <p className="mfb__section-title">핵심 사건 예측</p>
                    <div className="mfb__narrative mfb__narrative--events">
                      {coreEvents.split(/\n+/).map((line, i) => (
                        <p key={i}>{line}</p>
                      ))}
                    </div>
                  </>
                ) : null}
              </>
            ) : (
              <>
                <p className="mfb__section-title">풀 해석</p>
                <div className="mfb__narrative">
                  {m.narrative.split("\n\n").map((para, i) => (
                    <p key={i}>{para}</p>
                  ))}
                </div>
              </>
            )}

            <div className="mfb__short-grid">
              <p>
                <strong>기회 포인트</strong> {opportunityText}
              </p>
              <p>
                <strong>주의 포인트</strong> {riskText}
              </p>
              <p>
                <strong>명리학 해석의 현실 행동</strong> {actionText}
              </p>
            </div>

            {behaviorGuide ? (
              <div className="mfb__behavior">
                <p className="mfb__section-title">행동 가이드 (지금 해야 할 3가지 / 피해야 할 2가지)</p>
                <div className="mfb__narrative mfb__narrative--behavior">
                  {behaviorGuide.split(/\n+/).map((line, i) => (
                    <p key={i}>{line}</p>
                  ))}
                </div>
              </div>
            ) : null}

            {emotionText ? (
              <div className="mfb__emotion">
                <p className="mfb__section-title">감정 코칭</p>
                <p className="mfb__emotion-text">{emotionText}</p>
              </div>
            ) : null}

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

            {oneLineConclusion ? (
              <p className="mfb__one-line">
                <strong>한 줄 결론</strong> {oneLineConclusion}
              </p>
            ) : null}

            {bridgeText ? (
              <div className="mfb__bridge" role="note">
                <p className="mfb__section-title">AI 상담 연결</p>
                {bridgeLines.map((line, i) => (
                  <p key={i}>{line}</p>
                ))}
              </div>
            ) : null}

            {!singleMonthView ? (
              <nav className="mfb__nav" aria-label="월 넘기기">
                <button type="button" className="mfb__nav-btn" onClick={goPrev} disabled={safeIdx <= 0}>
                  ← 이전 달
                </button>
                <p className="mfb__nav-hint">
                  좌우 방향키로 넘길 수 있어요.
                  <br />
                  {safeIdx >= total - 1 ? "12월까지 모두 읽으셨어요." : "다음 달을 눌러 계속 읽어 보세요."}
                </p>
                <button
                  type="button"
                  className="mfb__nav-btn mfb__nav-btn--primary"
                  onClick={goNext}
                  disabled={safeIdx >= total - 1}
                >
                  다음 달 →
                </button>
              </nav>
            ) : null}
          </div>
        </div>
      </div>

      <div className="mfb__cta">
        <p className="mfb__cta-text">
          월별 해석은 가능성·경향을 돕는 참고용입니다. 내 인연·일·재정 상황에 맞게 풀고 싶다면 AI 상담으로 자연스럽게 이어가 보세요.
        </p>
        <button type="button" className="mfb__cta-btn" onClick={onGoCounsel}>
          이 흐름을 내 상황에 맞게 풀어보기 → AI 상담
        </button>
        <p className="mfb__end-note">상담에서는 위 월별 리포트와 대화가 이어지도록 맥락을 유지할 수 있습니다.</p>
      </div>
    </section>
  );
}
