// frontend/src/components/LifeEventSignalCard.tsx
// 월운에서 감지된 인생 사건 신호 표시 — 상복·우환·수술·사고·이별 등

import type { MonthlyFortuneEngineMonth } from "@/types/report";
import "./life-event-signal-card.css";

type LifeEvent = NonNullable<MonthlyFortuneEngineMonth["life_event_signals"]>[number];

type Props = {
  events: LifeEvent[];
  month: number;
};

export function LifeEventSignalCard({ events, month }: Props) {
  if (!events || events.length === 0) return null;

  const cautionEvents = events.filter((e) => e.category === "caution");
  const positiveEvents = events.filter((e) => e.category === "positive");

  return (
    <div className="life-event-card">
      {cautionEvents.length > 0 && (
        <div className="life-event-card__section life-event-card__section--caution">
          <div className="life-event-card__header">
            <span className="life-event-card__header-icon">🔍</span>
            <span className="life-event-card__header-title">
              {month}월 주의 신호
            </span>
          </div>
          <div className="life-event-card__items">
            {cautionEvents.map((event) => (
              <div key={event.event_id} className="life-event-card__item life-event-card__item--caution">
                <div className="life-event-card__item-head">
                  <span className="life-event-card__item-icon" aria-hidden>{event.icon}</span>
                  <span className="life-event-card__item-label">{event.label_ko}</span>
                </div>
                {event.signal && (
                  <p className="life-event-card__item-signal">{event.signal}</p>
                )}
                {event.action && (
                  <div className="life-event-card__item-action">
                    <span className="life-event-card__action-badge">행동</span>
                    <p className="life-event-card__action-text">{event.action}</p>
                  </div>
                )}
                {event.reframe && (
                  <p className="life-event-card__item-reframe">{event.reframe}</p>
                )}
              </div>
            ))}
          </div>
          <p className="life-event-card__note">
            사주 충극·신살 구조 기반 경향 안내입니다. 단정이 아닌 참고 정보로 활용하세요.
          </p>
        </div>
      )}

      {positiveEvents.length > 0 && (
        <div className="life-event-card__section life-event-card__section--positive">
          <div className="life-event-card__header">
            <span className="life-event-card__header-icon">🌟</span>
            <span className="life-event-card__header-title">
              {month}월 좋은 기운
            </span>
          </div>
          <div className="life-event-card__items">
            {positiveEvents.map((event) => (
              <div key={event.event_id} className="life-event-card__item life-event-card__item--positive">
                <div className="life-event-card__item-head">
                  <span className="life-event-card__item-icon" aria-hidden>{event.icon}</span>
                  <span className="life-event-card__item-label">{event.label_ko}</span>
                </div>
                {event.signal && (
                  <p className="life-event-card__item-signal">{event.signal}</p>
                )}
                {event.action && (
                  <div className="life-event-card__item-action">
                    <span className="life-event-card__action-badge life-event-card__action-badge--positive">활용</span>
                    <p className="life-event-card__action-text">{event.action}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
