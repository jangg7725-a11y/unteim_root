import { useCallback, useEffect, useMemo, useState } from "react";
import type { MonthlyFortuneEntry, YearlyMonthlyFortune } from "@/types/report";
import { MOCK_YEARLY_MONTHLY_FORTUNE } from "@/data/monthlyFortuneMock";
import { UNLOCK_PREMIUM_CONTENT } from "@/config/featureFlags";
import "./monthly-fortune-premium.css";
import "./monthly-fortune-book.css";

type Props = {
  data?: YearlyMonthlyFortune;
  /** 목 데모에서도 AI 상담으로 이어가기 (선택) */
  onGoCounsel?: () => void;
};

function Stars({ score }: { score: MonthlyFortuneEntry["score"] }) {
  const filled = "★".repeat(score) + "☆".repeat(5 - score);
  return <span className="mfb__stars">{filled}</span>;
}

function MonthCard({ entry }: { entry: MonthlyFortuneEntry }) {
  return (
    <article className="monthly-fortune-premium__card" aria-label={`${entry.month}월 운세`}>
      <div className="monthly-fortune-premium__card-head">
        <h3 className="monthly-fortune-premium__month">{entry.month}월</h3>
        <Stars score={entry.score} />
      </div>
      <dl className="monthly-fortune-premium__dl">
        <div>
          <dt>흐름</dt>
          <dd>{entry.flow}</dd>
        </div>
        <div>
          <dt>기회</dt>
          <dd>{entry.good}</dd>
        </div>
        <div>
          <dt>주의</dt>
          <dd>{entry.caution}</dd>
        </div>
        <div>
          <dt>행동 가이드</dt>
          <dd>{entry.action}</dd>
        </div>
      </dl>
    </article>
  );
}

function pickFirstSentence(text: string): string {
  const s = text.trim();
  if (!s) return "";
  const m = s.match(/^(.+?[.!?。]|.+)$/);
  return m ? m[1].trim() : s;
}

function MonthEntriesBook({
  entries,
  bestMonth,
  cautionMonth,
  onGoCounsel,
}: {
  entries: MonthlyFortuneEntry[];
  bestMonth: number;
  cautionMonth: number;
  onGoCounsel?: () => void;
}) {
  const sorted = useMemo(() => [...entries].sort((a, b) => a.month - b.month), [entries]);
  const total = sorted.length;
  const [idx, setIdx] = useState(0);
  const safeIdx = Math.min(idx, Math.max(0, total - 1));
  const e = sorted[safeIdx];

  const goPrev = useCallback(() => setIdx((i) => Math.max(0, i - 1)), []);
  const goNext = useCallback(() => setIdx((i) => Math.min(total - 1, i + 1)), [total]);

  useEffect(() => {
    const onKey = (ev: KeyboardEvent) => {
      if (ev.key === "ArrowLeft") goPrev();
      if (ev.key === "ArrowRight") goNext();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [goPrev, goNext]);

  if (!e || total === 0) return null;

  return (
    <>
      <div className="mfb__book-wrap">
        <div className="mfb__book">
          <div className="mfb__book-spine" aria-hidden />
          <div className="mfb__book-inner">
            <div className="mfb__progress">
              <span>
                {safeIdx + 1} / {total} 장 · {e.month}월
              </span>
              <div className="mfb__progress-dots" aria-hidden>
                {sorted.map((x, i) => (
                  <span key={x.month} className={`mfb__dot${i === safeIdx ? " mfb__dot--on" : ""}`} />
                ))}
              </div>
            </div>
            <header className="mfb__page-head">
              <h3 className="mfb__page-month">
                {e.month}월
                <span className="mfb__page-year">요약 리포트 (데모)</span>
              </h3>
              <Stars score={e.score} />
            </header>
            <dl className="mfb__signals">
              <div>
                <dt>이 해의 참고 달</dt>
                <dd>
                  기회 {bestMonth}월 · 주의 {cautionMonth}월
                </dd>
              </div>
            </dl>
            <p className="mfb__section-title">흐름</p>
            <div className="mfb__narrative">
              <p>{e.flow}</p>
            </div>
            <div className="mfb__short-grid">
              <p>
                <strong>기회</strong> {e.good}
              </p>
              <p>
                <strong>주의</strong> {e.caution}
              </p>
              <p>
                <strong>행동 가이드</strong> {e.action}
              </p>
            </div>
            <nav className="mfb__nav" aria-label="월 넘기기">
              <button type="button" className="mfb__nav-btn" onClick={goPrev} disabled={safeIdx <= 0}>
                ← 이전 달
              </button>
              <p className="mfb__nav-hint">
                좌우 방향키로 넘길 수 있어요.
                <br />
                {safeIdx >= total - 1 ? "마지막 장입니다." : "다음 달로 계속 읽어 보세요."}
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
          </div>
        </div>
      </div>
      {onGoCounsel && (
        <div className="mfb__cta">
          <p className="mfb__cta-text">월별 요약을 읽으셨다면, 내 상황에 맞게 AI 상담으로 이어가 보세요.</p>
          <button type="button" className="mfb__cta-btn" onClick={onGoCounsel}>
            AI 상담으로 이어가기
          </button>
        </div>
      )}
    </>
  );
}

export function MonthlyFortunePremium({ data = MOCK_YEARLY_MONTHLY_FORTUNE, onGoCounsel }: Props) {
  const [unlocked, setUnlocked] = useState(false);
  const currentMonth = new Date().getMonth() + 1;
  const nextMonth = currentMonth + 1;

  const preview = data.monthly.filter((m) => m.month <= currentMonth);
  const nextPreview = data.monthly.find((m) => m.month === nextMonth);
  const locked = data.monthly.filter((m) => m.month > nextMonth);

  return (
    <section className="monthly-fortune-premium" aria-labelledby="monthly-fortune-heading">
      <div className="monthly-fortune-premium__intro">
        <h2 id="monthly-fortune-heading" className="monthly-fortune-premium__title">
          월별 운세 (1~12월)
        </h2>
        <p className="monthly-fortune-premium__year-sum">{data.yearSummary}</p>
        <div className="monthly-fortune-premium__highlights">
          <p>
            <span className="monthly-fortune-premium__badge monthly-fortune-premium__badge--best">
              중요한 달 (기회)
            </span>
            <strong>{data.bestMonth}월</strong>
          </p>
          <p>
            <span className="monthly-fortune-premium__badge monthly-fortune-premium__badge--caution">
              주의 달
            </span>
            <strong>{data.cautionMonth}월</strong>
          </p>
        </div>
      </div>

      {UNLOCK_PREMIUM_CONTENT ? (
        <MonthEntriesBook
          entries={data.monthly}
          bestMonth={data.bestMonth}
          cautionMonth={data.cautionMonth}
          onGoCounsel={onGoCounsel}
        />
      ) : (
        <>
      <div className="monthly-fortune-premium__grid">
        {preview.map((m) => (
          <MonthCard key={m.month} entry={m} />
        ))}
      </div>

      {!unlocked && nextPreview && (
        <div className="monthly-fortune-premium__next-preview" aria-label="다음 달 미리보기">
          <div className="monthly-fortune-premium__next-head">
            <span className="monthly-fortune-premium__next-badge">다음 달 미리보기</span>
            <h3 className="monthly-fortune-premium__month">{nextPreview.month}월</h3>
          </div>
          <p className="monthly-fortune-premium__next-flow">
            <strong>흐름</strong> {pickFirstSentence(nextPreview.flow)}
          </p>
          <div className="monthly-fortune-premium__next-locked">
            <div className="monthly-fortune-premium__blur" aria-hidden>
              <dl className="monthly-fortune-premium__dl">
                <div>
                  <dt>기회</dt>
                  <dd>{nextPreview.good}</dd>
                </div>
                <div>
                  <dt>주의</dt>
                  <dd>{nextPreview.caution}</dd>
                </div>
                <div>
                  <dt>행동 가이드</dt>
                  <dd>{nextPreview.action}</dd>
                </div>
              </dl>
            </div>
            <div className="monthly-fortune-premium__next-overlay">
              <p>핵심 일부만 공개되었습니다</p>
            </div>
          </div>
          <button
            type="button"
            className="monthly-fortune-premium__unlock monthly-fortune-premium__unlock--next"
            onClick={() => setUnlocked(true)}
          >
            이후 흐름 전체 보기 → 올해 전체 운세 확인하기
          </button>
        </div>
      )}

      {!unlocked && locked.length > 0 && (
        <div className="monthly-fortune-premium__lock-wrap">
          <div className="monthly-fortune-premium__blur" aria-hidden>
            <div className="monthly-fortune-premium__grid monthly-fortune-premium__grid--fake">
              {locked.map((m) => (
                <MonthCard key={m.month} entry={m} />
              ))}
            </div>
          </div>
          <div className="monthly-fortune-premium__lock-overlay">
            <p className="monthly-fortune-premium__lock-text">
              다음 달부터 중요한 흐름이 시작됩니다
            </p>
            <p className="monthly-fortune-premium__lock-subtext">이 이후 흐름은 유료 리포트에서 확인 가능합니다</p>
            <button
              type="button"
              className="monthly-fortune-premium__unlock"
              onClick={() => setUnlocked(true)}
            >
              올해 전체 운세 확인하기
            </button>
            <p className="monthly-fortune-premium__lock-hint">(데모: 클릭 시 전체 공개)</p>
          </div>
        </div>
      )}

      {unlocked && (
        <MonthEntriesBook
          entries={nextPreview ? [nextPreview, ...locked] : locked}
          bestMonth={data.bestMonth}
          cautionMonth={data.cautionMonth}
          onGoCounsel={onGoCounsel}
        />
      )}
        </>
      )}
    </section>
  );
}
