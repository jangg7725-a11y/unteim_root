import { useState } from "react";
import type { MonthlyFortuneEntry, YearlyMonthlyFortune } from "@/types/report";
import { MOCK_YEARLY_MONTHLY_FORTUNE } from "@/data/monthlyFortuneMock";
import "./monthly-fortune-premium.css";

type Props = {
  data?: YearlyMonthlyFortune;
};

function Stars({ score }: { score: MonthlyFortuneEntry["score"] }) {
  const filled = "★".repeat(score) + "☆".repeat(5 - score);
  return <span className="monthly-fortune-premium__stars">{filled}</span>;
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

export function MonthlyFortunePremium({ data = MOCK_YEARLY_MONTHLY_FORTUNE }: Props) {
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
        <div className="monthly-fortune-premium__grid">
          {(nextPreview ? [nextPreview, ...locked] : locked).map((m) => (
            <MonthCard key={m.month} entry={m} />
          ))}
        </div>
      )}
    </section>
  );
}
