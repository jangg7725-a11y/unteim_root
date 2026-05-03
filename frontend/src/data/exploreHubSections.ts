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
    title: "사주가 말하는 나의 오늘",
    layout: "grid3",
    items: [
      { id: "m1", label: "이번 달 흐름", icon: "📅", description: "이달, 나를 도와줄 기운은?" },
      { id: "m2", label: "오늘의 리듬", icon: "🌤️", description: "오늘 내 에너지, 어디에 쓸까?" },
      { id: "m3", label: "관계·인연", icon: "💬", description: "지금 내 곁의 사람, 괜찮을까?" },
      { id: "m4", label: "일·재물", icon: "💼", description: "돈과 일, 지금 흐름이 맞나요?" },
      { id: "m5", label: "마음·성향", icon: "🌙", description: "내가 반응하는 방식, 왜 그럴까?" },
      { id: "m6", label: "실천 한 줄", icon: "✅", description: "오늘 딱 하나만 해야 한다면?" },
      { id: "m7", label: "사주 개요", icon: "🔮", description: "내 사주, 한눈에 보기" },
      { id: "m8", label: "신살 하이라이트", icon: "✨", description: "내 사주 속 숨은 특별한 기운" },
      { id: "m9", label: "대운 스냅샷", icon: "📿", description: "앞으로 10년, 큰 흐름은?" },
    ],
  },
  {
    id: "life",
    eyebrow: "생활 맞춤",
    title: "내 사주 영역별 운세 읽기",
    layout: "list",
    items: [
      { id: "l1", label: "궁합·관계", description: "우리 둘, 잘 맞는 편일까요?", icon: "🤝" },
      { id: "l2", label: "택일·일정", description: "이날, 시작해도 괜찮을까요?", icon: "🗓️" },
      { id: "l3", label: "건강·휴식", description: "내 몸이 지금 보내는 신호는?", icon: "🌿" },
      { id: "l4", label: "심리·습관", description: "나도 모르게 반복하는 패턴은?", icon: "🧠" },
    ],
  },
  {
    id: "quick",
    eyebrow: "바로 가기",
    title: "지금 바로 시작해볼까요?",
    layout: "grid2",
    items: [
      { id: "q1", label: "AI 상담", description: "지금 바로 물어보세요", icon: "💭", badge: "beta" },
      { id: "q2", label: "리포트 열기", description: "내 사주 분석 전체 보기", icon: "📋" },
      { id: "q3", label: "사주 입력", description: "1분이면 충분해요", icon: "✏️" },
      { id: "q4", label: "월별 카드", description: "이달의 흐름을 한 장으로", icon: "📖" },
    ],
  },
];
