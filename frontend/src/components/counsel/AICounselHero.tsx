import type { ReactNode } from "react";
import { CounselCharacterCard } from "./CounselCharacterCard";
import { CounselQuestionExamples } from "./CounselQuestionExamples";
import "./ai-counsel-hero.css";

type HeroSectionKey = "copy" | "characters" | "examples";
type CharacterKey = "undol" | "unsuni";

type Props = {
  sectionOrder?: HeroSectionKey[];
  characterOrder?: CharacterKey[];
  characterLayout?: "row" | "column";
};

export function AICounselHero({
  sectionOrder = ["copy", "characters", "examples"],
  characterOrder = ["undol", "unsuni"],
  characterLayout = "row",
}: Props) {
  const copyBlock = (
    <div className="ai-counsel-copy">
      <h1 className="ai-counsel-copy__title">AI 상담 코너</h1>
      <p className="ai-counsel-copy__line">
        지금 느끼는 고민과 흐름,
        <br />
        혼자 풀어내기 어려우신가요?
      </p>
      <p className="ai-counsel-copy__line">
        운돌이와 운순이는
        <br />
        당신의 사주 흐름을 바탕으로
        <br />
        지금 필요한 답을 함께 찾아드립니다
      </p>
    </div>
  );

  const characterConfig = {
    undol: {
      name: "운돌이",
      description: "차분하게 흐름을 해석하는 분석형 상담자",
      imageSrc: "/characters/undol.png",
      imageFallbacks: ["/characters/undol.jpg", "/characters/undol.webp"],
      tone: "undol" as const,
    },
    unsuni: {
      name: "운순이",
      description: "따뜻하게 감정을 읽어주는 공감형 상담자",
      imageSrc: "/characters/unsun.png",
      imageFallbacks: ["/characters/unsuni.png", "/characters/unsun.jpg", "/characters/unsuni.jpg"],
      tone: "unsuni" as const,
    },
  };

  const charactersBlock = (
    <div className="ai-counsel-characters" data-character-layout={characterLayout} aria-label="캐릭터 소개">
      {characterOrder.map((key) => {
        const c = characterConfig[key];
        return (
          <CounselCharacterCard
            key={key}
            name={c.name}
            description={c.description}
            imageSrc={c.imageSrc}
            imageFallbacks={c.imageFallbacks}
            tone={c.tone}
          />
        );
      })}
    </div>
  );

  const blockMap: Record<HeroSectionKey, ReactNode> = {
    copy: copyBlock,
    characters: charactersBlock,
    examples: <CounselQuestionExamples />,
  };

  return (
    <section className="ai-counsel-hero" aria-label="AI 상담 코너 소개">
      {sectionOrder.map((k) => (
        <div key={k} className={`ai-counsel-hero__slot ai-counsel-hero__slot--${k}`}>
          {blockMap[k]}
        </div>
      ))}
    </section>
  );
}

