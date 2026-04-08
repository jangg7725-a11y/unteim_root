import { useState } from "react";
import type { CounselSessionCardPayload } from "@/types/counsel";
import "./counsel-session-card.css";

type Props = {
  card: CounselSessionCardPayload;
};

/**
 * 상담 직후 핵심 요약 + CTA — 캐릭터 도크(우하단) 옆에 고정
 */
export function CounselSessionCard({ card }: Props) {
  const [hint, setHint] = useState<string | null>(null);

  const onCta = (label: string) => {
    setHint(`「${label}」 기능은 곧 연결될 예정입니다.`);
    window.setTimeout(() => setHint(null), 4000);
  };

  return (
    <aside className="counsel-session-card" aria-label="이번 상담 요약">
      <h2 className="counsel-session-card__title">이번 상담 요약</h2>

      <section className="counsel-session-card__block">
        <h3 className="counsel-session-card__label">핵심 흐름</h3>
        <p className="counsel-session-card__text">{card.flow}</p>
      </section>

      <section className="counsel-session-card__block">
        <h3 className="counsel-session-card__label">주의 포인트</h3>
        <p className="counsel-session-card__text counsel-session-card__text--caution">{card.cautions}</p>
      </section>

      <section className="counsel-session-card__block">
        <h3 className="counsel-session-card__label">추천 행동</h3>
        <ul className="counsel-session-card__actions">
          {card.actions.map((a, i) => (
            <li key={i}>{a}</li>
          ))}
        </ul>
      </section>

      <div className="counsel-session-card__cta" role="group" aria-label="다음 단계">
        <button type="button" className="counsel-session-card__cta-btn" onClick={() => onCta("오늘 운세")}>
          오늘 운세 보기
        </button>
        <button type="button" className="counsel-session-card__cta-btn" onClick={() => onCta("월운")}>
          월운 자세히 보기
        </button>
        <button type="button" className="counsel-session-card__cta-btn" onClick={() => onCta("궁합")}>
          궁합 보기
        </button>
      </div>

      {hint && (
        <p className="counsel-session-card__hint" role="status">
          {hint}
        </p>
      )}
    </aside>
  );
}
