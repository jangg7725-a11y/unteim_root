// frontend/src/components/RelationFortuneCard.tsx
// 인연·궁합 슬롯 기반 카드 — narrative_slots.relation 데이터 출력

import type { NarrativeSlots } from "@/types/report";
import "./relation-fortune-card.css";

type Props = {
  narrativeSlots?: NarrativeSlots | null;
};

export function RelationFortuneCard({ narrativeSlots }: Props) {
  const rel = narrativeSlots?.relation;
  if (!rel?.found) return null;

  const oh = rel.oheng;
  const dm = rel.daymaster;

  // 출력할 항목 구성
  const items: { label: string; text: string }[] = [];

  if (oh?.label_ko && oh?.core_theme) {
    items.push({ label: oh.label_ko, text: oh.core_theme });
  }
  if (oh?.strength) {
    items.push({ label: "관계 강점", text: oh.strength });
  }
  if (oh?.advice) {
    items.push({ label: "인연 조언", text: oh.advice });
  }
  if (dm?.health_tendency && !oh?.advice) {
    // daymaster 정보 보완 (oheng advice 없을 때)
    items.push({ label: "성향", text: dm.health_tendency });
  }

  if (items.length === 0) return null;

  return (
    <section
      id="report-section-relation"
      className="report-page__card relation-card"
      aria-label="인연운 카드"
    >
      <h3 className="report-page__card-title relation-card__title">
        <span className="relation-card__icon" aria-hidden>🌿</span>
        인연운
      </h3>

      <div className="relation-card__body">
        {items.map((item, i) => (
          <div key={i} className="relation-card__item">
            <span className="relation-card__label">{item.label}</span>
            <p className="relation-card__text">{item.text}</p>
          </div>
        ))}
      </div>

      <p className="relation-card__note">
        사주 오행 구조를 바탕으로 한 관계 경향 참고 정보입니다.
      </p>
    </section>
  );
}
