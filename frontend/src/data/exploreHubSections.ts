/**
 * 탐색 허브 카테고리 — 이후 라벨·설명·개수는 여기만 수정하면 됩니다.
 * layout: grid3(3열 아이콘), list(가로 행), grid2(2열 카드)
 */
export type ExploreHubBadge = "new" | "beta";

export type ExploreHubItem = {
  id: string;
  label: string;
  description?: string;
  icon: string;
  badge?: ExploreHubBadge;
};

export type ExploreHubSection = {
  id: string;
  eyebrow: string;
  title: string;
  layout: "grid3" | "list" | "grid2";
  items: ExploreHubItem[];
};

export const EXPLORE_HUB_SECTIONS: ExploreHubSection[] = [
  {
    id: "flow",
    eyebrow: "엔진 기반 코칭",
    title: "무엇이 궁금하세요?",
    layout: "grid3",
    items: [
      { id: "m1", label: "이번 달 흐름", icon: "📅", description: "월운·세운 요약" },
      { id: "m2", label: "오늘의 리듬", icon: "🌤️", description: "생활 점검" },
      { id: "m3", label: "관계·인연", icon: "💬", description: "대인·연애 경향" },
      { id: "m4", label: "일·재물", icon: "💼", description: "업무·재정 리듬" },
      { id: "m5", label: "마음·성향", icon: "🌙", description: "감정·결정 스타일" },
      { id: "m6", label: "실천 한 줄", icon: "✅", description: "작은 행동 제안" },
      { id: "m7", label: "사주 개요", icon: "🔮", description: "원국 스냅샷" },
      { id: "m8", label: "신살 하이라이트", icon: "✨", description: "요약 포인트" },
      { id: "m9", label: "대운 스냅샷", icon: "📿", description: "장기 흐름" },
    ],
  },
  {
    id: "life",
    eyebrow: "생활 맞춤",
    title: "더 알아보기",
    layout: "list",
    items: [
      { id: "l1", label: "궁합·관계", description: "두 사람의 반응 패턴을 비교해 봅니다.", icon: "🤝" },
      { id: "l2", label: "택일·일정", description: "중요한 일정을 잡을 때 참고할 수 있어요.", icon: "🗓️" },
      { id: "l3", label: "건강·휴식", description: "리듬과 회복에 대한 생활 코칭입니다.", icon: "🌿" },
      { id: "l4", label: "심리·습관", description: "반복되는 반응을 가볍게 짚어 봅니다.", icon: "🧠" },
    ],
  },
  {
    id: "quick",
    eyebrow: "바로 가기",
    title: "지금 필요한 것",
    layout: "grid2",
    items: [
      { id: "q1", label: "AI 상담", description: "입력·분석 후 이어서 질문", icon: "💭", badge: "beta" },
      { id: "q2", label: "리포트 열기", description: "생성된 요약 보기", icon: "📋" },
      { id: "q3", label: "사주 입력", description: "생년월일·시간 입력", icon: "✏️" },
      { id: "q4", label: "월별 카드", description: "월운 북 모드", icon: "📖" },
    ],
  },
];
