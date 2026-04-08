import { useState } from "react";

type Props = {
  name: string;
  description: string;
  imageSrc: string;
  imageFallbacks?: string[];
  tone: "undol" | "unsuni";
};

export function CounselCharacterCard({ name, description, imageSrc, imageFallbacks = [], tone }: Props) {
  const [broken, setBroken] = useState(false);
  const [idx, setIdx] = useState(0);
  const candidates = [imageSrc, ...imageFallbacks];
  const currentSrc = candidates[idx] ?? imageSrc;

  return (
    <article className={`counsel-character-card counsel-character-card--${tone}`} aria-label={`${name} 소개`}>
      <div className="counsel-character-card__thumb">
        {!broken ? (
          <img
            src={currentSrc}
            alt={`${name} 캐릭터`}
            className="counsel-character-card__img"
            onError={() => {
              if (idx < candidates.length - 1) {
                setIdx((n) => n + 1);
              } else {
                setBroken(true);
              }
            }}
          />
        ) : (
          <span className="counsel-character-card__fallback">{name}</span>
        )}
      </div>
      <div className="counsel-character-card__body">
        <h3 className="counsel-character-card__name">{name}</h3>
        <p className="counsel-character-card__desc">{description}</p>
      </div>
    </article>
  );
}

