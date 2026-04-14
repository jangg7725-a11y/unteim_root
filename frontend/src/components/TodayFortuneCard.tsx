import { formatKoreanDisplayDate } from "@/utils/formatKoreanDate";
import "./today-fortune-card.css";

export type TodayFortuneData = {
  flow: string;
  stars: 1 | 2 | 3 | 4 | 5;
  actionPoint: string;
  keywords: [string, string, string];
  lucky: {
    color: string;
    number: string;
    direction: string;
    item: string;
  };
  emotionCoaching: string;
};

const MOCK_TODAY_FORTUNE: TodayFortuneData = {
  flow: "오늘은 속도를 조금 낮추고, 정리된 선택이 빛날 가능성이 큽니다.",
  stars: 4,
  actionPoint: "오전에는 우선순위 1가지만 확정하고, 오후에 실행으로 연결해 보세요.",
  keywords: ["정리", "균형", "집중"],
  lucky: {
    color: "라벤더",
    number: "7",
    direction: "동남",
    item: "작은 노트",
  },
  emotionCoaching:
    "마음이 흔들려도 괜찮아요. 오늘은 완벽보다 한 걸음의 꾸준함이 운을 부드럽게 열어줄 수 있어요.",
};

type Props = {
  data?: TodayFortuneData;
  /** 엔진·목 데이터와 구분되는 참고 문장(문장 DB) */
  supplementaryLine?: string | null;
};

export function TodayFortuneCard({ data = MOCK_TODAY_FORTUNE, supplementaryLine }: Props) {
  const stars = "★★★★★".slice(0, data.stars) + "☆☆☆☆☆".slice(0, 5 - data.stars);
  const todayLabel = formatKoreanDisplayDate();

  return (
    <section id="report-anchor-today" className="today-fortune" aria-label="오늘의 운세 카드">
      <div className="today-fortune__head">
        <div className="today-fortune__title-wrap">
          <h2 className="today-fortune__title">오늘의 운세 카드</h2>
          <p className="today-fortune__date" aria-label="기준일">
            {todayLabel}
          </p>
        </div>
        <p className="today-fortune__stars">{stars}</p>
      </div>

      {supplementaryLine ? (
        <div className="today-fortune__supplementary" role="note">
          <span className="today-fortune__supplementary-label">참고 한 줄</span>
          <p className="today-fortune__supplementary-text">{supplementaryLine}</p>
        </div>
      ) : null}

      <p className="today-fortune__flow">{data.flow}</p>

      <div className="today-fortune__block">
        <h3 className="today-fortune__label">행동 포인트</h3>
        <p className="today-fortune__text">{data.actionPoint}</p>
      </div>

      <div className="today-fortune__block">
        <h3 className="today-fortune__label">키워드</h3>
        <div className="today-fortune__chips">
          {data.keywords.map((k) => (
            <span key={k} className="today-fortune__chip">
              {k}
            </span>
          ))}
        </div>
      </div>

      <div className="today-fortune__block">
        <h3 className="today-fortune__label">행운 요소</h3>
        <p className="today-fortune__text">
          색상 {data.lucky.color} · 숫자 {data.lucky.number} · 방향 {data.lucky.direction} · 아이템 {data.lucky.item}
        </p>
      </div>

      <div className="today-fortune__coach">
        <strong>운순이 코칭</strong>
        <p>{data.emotionCoaching}</p>
      </div>
    </section>
  );
}

