/**
 * 탐색 허브 카테고리 — 이후 라벨·설명·개수는 여기만 수정하면 됩니다.
 * layout: cards(2열 그라데이션 카드), list(가로 행), grid2(2열 카드)
 */
export type ExploreHubBadge = "new" | "beta";

/** 카드 배너 그라데이션 테마 — feed.css 테마와 동일 */
export type HubCardTheme =
  | "violet"
  | "rose"
  | "amber"
  | "slate"
  | "teal"
  | "pink"
  | "indigo"
  | "green";

export type ExploreHubItem = {
  id: string;
  label: string;
  description?: string;
  icon: string;
  badge?: ExploreHubBadge;
  /** 카드 배너 그라데이션 테마 */
  theme?: HubCardTheme;
  /** 우측 상단 영역 레이블 */
  areaLabel?: string;
};

export type ExploreHubSection = {
  id: string;
  eyebrow: string;
  title: string;
  layout: "cards" | "action" | "grid3" | "list" | "grid2";
  items: ExploreHubItem[];
};

export const EXPLORE_HUB_SECTIONS: ExploreHubSection[] = [
  {
    id: "flow",
    eyebrow: "엔진 기반 코칭",
    title: "사주로 알아보는 나의 오늘",
    layout: "cards",
    items: [
      { id: "m2", label: "오늘의 운세",     icon: "🌤️", description: "오늘 내 에너지, 어디에 쓸까?",    theme: "teal",   areaLabel: "오늘" },
      { id: "m3", label: "관계·인연",        icon: "💬", description: "지금 내 곁의 사람, 괜찮을까?",   theme: "rose",   areaLabel: "오늘" },
      { id: "m4", label: "일·재물",          icon: "💼", description: "돈과 일, 지금 흐름이 맞나요?",   theme: "amber",  areaLabel: "오늘" },
      { id: "m5", label: "마음·성향",        icon: "🌙", description: "내가 반응하는 방식, 왜 그럴까?", theme: "indigo", areaLabel: "오늘" },
      { id: "m6", label: "실천 한 줄",       icon: "✅", description: "오늘 딱 하나만 해야 한다면?",    theme: "violet", areaLabel: "오늘" },
      { id: "m7", label: "사주 개요",        icon: "🔮", description: "내 사주, 한눈에 보기",           theme: "slate",  areaLabel: "사주" },
      { id: "m8", label: "신살 하이라이트",  icon: "✨", description: "내 사주 속 숨은 특별한 기운",   theme: "pink",   areaLabel: "사주" },
      { id: "m9", label: "대운 스냅샷",      icon: "📿", description: "앞으로 10년, 큰 흐름은?",       theme: "slate",  areaLabel: "대운" },
    ],
  },
  {
    id: "life",
    eyebrow: "생활 맞춤",
    title: "내 사주 영역별 운세 읽기",
    layout: "cards",
    items: [
      { id: "m1", label: "이번 달 흐름",      icon: "📅", description: "이달, 나를 도와줄 기운은?",              theme: "amber",  areaLabel: "이번 달" },
      { id: "l1", label: "궁합·관계",         icon: "🤝", description: "우리 둘, 잘 맞는 편일까요?",            theme: "rose",   areaLabel: "관계" },
      { id: "l2", label: "택일·일정",         icon: "🗓️", description: "이날, 시작해도 괜찮을까요?",           theme: "teal",   areaLabel: "택일" },
      { id: "l3", label: "건강·휴식",         icon: "🌿", description: "내 몸이 지금 보내는 신호는?",          theme: "green",  areaLabel: "건강" },
      { id: "l4", label: "심리·습관",         icon: "🧠", description: "나도 모르게 반복하는 패턴은?",         theme: "violet", areaLabel: "심리" },
      { id: "m10", label: "성격·기질",       icon: "🧭", description: "나는 어떤 사람일까?",                 theme: "violet", areaLabel: "성향" },
      { id: "f1", label: "사람 앞의 나",      icon: "💕", description: "대인·연애에서 드러나는 패턴",          theme: "rose",   areaLabel: "이번 달" },
      { id: "f2", label: "일과 재물의 리듬",  icon: "💼", description: "업무·재물 흐름을 보는 관점",           theme: "amber",  areaLabel: "사주" },
    ],
  },
  {
    id: "quick",
    eyebrow: "바로 가기",
    title: "지금 알아 볼까요?",
    layout: "action",
    items: [
      { id: "q1", label: "AI 상담",    icon: "💭", description: "지금 바로 물어보세요",     theme: "violet", areaLabel: "상담",   badge: "beta" },
      { id: "q2", label: "리포트 열기", icon: "📋", description: "내 사주 분석 전체 보기",  theme: "slate",  areaLabel: "리포트" },
      { id: "q3", label: "사주 입력",  icon: "✏️", description: "1분이면 충분해요",         theme: "indigo", areaLabel: "사주" },
      { id: "q4", label: "월별 카드",  icon: "📖", description: "이달의 흐름을 한 장으로", theme: "amber",  areaLabel: "이번 달" },
    ],
  },
];
