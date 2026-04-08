/**
 * AI 상담 코너 UI 배치 설정.
 * 값을 바꾸면 코드 수정 없이 영역 순서/배치를 조정할 수 있습니다.
 */
export const COUNSEL_LAYOUT = {
  /** hero 내부 블록 순서 */
  heroSectionOrder: ["copy", "characters", "examples"] as const,
  /** 캐릭터 카드 순서 */
  characterOrder: ["undol", "unsuni"] as const,
  /** 캐릭터 영역 배치: row(가로), column(세로) */
  characterLayout: "row" as "row" | "column",
  /** 입력 영역 위치: top(상단), bottom(하단) */
  inputSectionPosition: "bottom" as "top" | "bottom",
} as const;

export type HeroSectionKey = (typeof COUNSEL_LAYOUT.heroSectionOrder)[number];
export type CharacterKey = (typeof COUNSEL_LAYOUT.characterOrder)[number];

