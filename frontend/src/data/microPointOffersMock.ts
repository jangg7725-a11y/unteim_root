export type MicroPointOfferItem = {
  question: string;
  description: string;
  price: number;
  type: "single" | "pair";
};

export type MicroPointOfferCategory = {
  id: string;
  title: string;
  items: MicroPointOfferItem[];
};

export const MICRO_POINT_OFFERS: MicroPointOfferCategory[] = [
  {
    id: "love-fate",
    title: "연애/인연",
    items: [
      { question: "우리 사랑할까요?", description: "두 사람의 감정선이 어디까지 이어질지 확인해요.", price: 900, type: "pair" },
      { question: "우리 인연 맞나요?", description: "스쳐 가는 인연인지, 깊어질 인연인지 짚어봐요.", price: 900, type: "pair" },
      { question: "우리 결혼까지 갈까요?", description: "관계의 현실성과 장기 흐름을 함께 봐요.", price: 1200, type: "pair" },
    ],
  },
  {
    id: "partner-mind",
    title: "상대 마음",
    items: [
      { question: "상대의 마음은?", description: "겉으로 보이지 않는 속마음을 차분히 읽어봐요.", price: 900, type: "pair" },
      { question: "연락 안 하는 이유는?", description: "지금 멈춘 이유와 감정의 온도를 확인해요.", price: 900, type: "pair" },
      { question: "다시 연락 올까요?", description: "재접점이 생길 가능성과 시기를 가볍게 점검해요.", price: 1000, type: "pair" },
    ],
  },
  {
    id: "reunion",
    title: "재회",
    items: [
      { question: "다시 만날 수 있을까요?", description: "재회 가능성과 관계 회복의 조건을 살펴봐요.", price: 1000, type: "pair" },
      { question: "기다리면 돌아올까요?", description: "기다림이 의미 있는지 지금 판단해봐요.", price: 900, type: "pair" },
    ],
  },
  {
    id: "timing",
    title: "타이밍",
    items: [
      { question: "지금 연락해도 될까요?", description: "먼저 다가가도 좋은 흐름인지 확인해요.", price: 700, type: "single" },
      { question: "지금 움직여도 될까요?", description: "결정의 타이밍을 놓치지 않게 도와드려요.", price: 700, type: "single" },
    ],
  },
  {
    id: "emotion",
    title: "감정",
    items: [
      { question: "나의 마음 상태는?", description: "흔들리는 감정의 중심을 부드럽게 정리해요.", price: 700, type: "single" },
      { question: "이 감정 진짜일까요?", description: "순간 감정인지 진심인지 구분해봐요.", price: 700, type: "single" },
    ],
  },
  {
    id: "compatibility",
    title: "궁합",
    items: [
      { question: "우리 궁합은?", description: "성향·리듬의 맞물림을 쉽게 확인해요.", price: 1200, type: "pair" },
      { question: "결혼 궁합은?", description: "생활 궁합과 장기 안정성을 함께 점검해요.", price: 1500, type: "pair" },
    ],
  },
];

