import { MICRO_POINT_OFFERS, type MicroPointOfferItem } from "@/data/microPointOffersMock";
import { UNLOCK_PREMIUM_CONTENT } from "@/config/featureFlags";
import "./micro-point-offers.css";

type Props = {
  onSelectSingle: (item: MicroPointOfferItem) => void;
  onSelectPair: (item: MicroPointOfferItem) => void;
};

export function MicroPointOffers({ onSelectSingle, onSelectPair }: Props) {
  return (
    <section id="report-anchor-compatibility" className="mpo" aria-label="소액 포인트 질문">
      <header className="mpo__head">
        <h2 className="mpo__title">소액 포인트 질문</h2>
        <p className="mpo__sub">지금 가장 궁금한 질문을 바로 눌러 확인해 보세요.</p>
      </header>

      <div className="mpo__list">
        {MICRO_POINT_OFFERS.map((cat) =>
          cat.items.map((item, idx) => (
            <button
              key={`${cat.id}-${idx}`}
              type="button"
              className="mpo__row"
              onClick={() => {
                if (item.type === "pair") onSelectPair(item);
                else onSelectSingle(item);
              }}
            >
              <span className="mpo__ico" aria-hidden="true">{cat.icon}</span>
              <span className="mpo__text">
                <span className="mpo__area">{cat.title}</span>
                <span className="mpo__q">{item.question}</span>
                <span className="mpo__desc">{item.description}</span>
              </span>
              <span className="mpo__arrow" aria-hidden="true">›</span>
              {!UNLOCK_PREMIUM_CONTENT && (
                <span className="mpo__price">{item.price.toLocaleString()}P</span>
              )}
            </button>
          ))
        )}
      </div>
    </section>
  );
}
