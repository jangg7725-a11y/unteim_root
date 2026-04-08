import type { YearlyMonthlyFortune } from "@/types/report";

/** 데모용 — 이후 API/GPT 연동 시 동일 스키마로 교체 */
export const MOCK_YEARLY_MONTHLY_FORTUNE = {
  yearSummary:
    "올해는 상반기에 정리와 재정비, 하반기에 확장과 관계의 균형이 맞물릴 수 있는 흐름입니다. 무리한 확장보다 리듬을 지키는 것이 유리할 수 있습니다.",
  bestMonth: 5,
  cautionMonth: 8,
  monthly: [
    { month: 1, flow: "새해 출발 — 계획을 다듬고 체력을 챙기는 달.", good: "작은 목표 완수", caution: "과로·야근 누적", action: "주간 루틴 한 가지만 고정하기", score: 3 },
    { month: 2, flow: "대인 관계에서 소통이 강해질 수 있는 달.", good: "협업·제안", caution: "말이 앞서는 순간", action: "중요한 약속은 글로 남기기", score: 4 },
    { month: 3, flow: "변화의 기운 — 환경 정리에 유리.", good: "정리·이직·이사 준비", caution: "충동 결정", action: "큰 결정은 일주일 숙성", score: 3 },
    { month: 4, flow: "성장과 학습에 집중하기 좋은 달.", good: "자격·스킬", caution: "산만함", action: "한 과목만 끝까지", score: 4 },
    { month: 5, flow: "기회의 달 — 노력이 눈에 띄게 드러날 수 있음.", good: "인정·보상", caution: "과신", action: "감사 표현과 기록 남기기", score: 5 },
    { month: 6, flow: "반기 정리 — 관계와 재정 점검.", good: "협상·정산", caution: "지출 증가", action: "예산 한 줄만 매일 기록", score: 4 },
    { month: 7, flow: "휴식과 재충전 — 속도 조절.", good: "휴가·취미", caution: "무기력", action: "짧은 산책 루틴", score: 3 },
    { month: 8, flow: "주의가 필요한 달 — 감정 기복·오해 가능.", good: "내면 성찰", caution: "말다툼·과로", action: "중요 대화는 다음 날 아침에", score: 2 },
    { month: 9, flow: "가을 정리 — 실무 집중.", good: "마무리·성과", caution: "완벽주의", action: "80%에서 제출하고 다듬기", score: 4 },
    { month: 10, flow: "대외 활동·네트워크에 유리.", good: "모임·소개", caution: "약속 과다", action: "주 1회만 새 인맥", score: 4 },
    { month: 11, flow: "마무리와 내년 준비.", good: "회고·저축", caution: "스트레스", action: "감사 일기 3줄", score: 3 },
    { month: 12, flow: "한 해 정리 — 가족·휴식.", good: "관계 회복", caution: "과식·음주", action: "수면 시간 우선 확보", score: 4 },
  ],
} satisfies YearlyMonthlyFortune;
