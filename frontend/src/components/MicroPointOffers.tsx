import { MICRO_POINT_OFFERS, type MicroPointOfferItem } from "@/data/microPointOffersMock";
import { UNLOCK_PREMIUM_CONTENT } from "@/config/featureFlags";
import "./micro-point-offers.css";

type Props = {
  onSelectSingle: (item: MicroPointOfferItem) => void;
  onSelectPair: (item: MicroPointOfferItem) => void;
};

export function MicroPointOffers({ onSelectSingle, onSelectPair }: Props) {
  return (
    <section className="micro-point-offers" aria-label="소액 포인트 질문">
      <header className="micro-point-offers__head">
        <h2 className="micro-point-offers__title">소액 포인트 질문</h2>
        <p className="micro-point-offers__sub">지금 가장 궁금한 질문을 바로 눌러 확인해 보세요.</p>
      </header>

      <div className="micro-point-offers__categories">
        {MICRO_POINT_OFFERS.map((cat) => (
          <section key={cat.id} className="micro-point-offers__category" aria-label={cat.title}>
            <h3 className="micro-point-offers__category-title">{cat.title}</h3>
            <div className="micro-point-offers__items">
              {cat.items.map((item, idx) => (
                <button
                  key={`${cat.id}-${idx}`}
                  type="button"
                  className="micro-point-offers__item"
                  onClick={() => {
                    if (item.type === "pair") onSelectPair(item);
                    else onSelectSingle(item);
                  }}
                >
                  <p className="micro-point-offers__q">{item.question}</p>
                  <p className="micro-point-offers__desc">{item.description}</p>
                  {!UNLOCK_PREMIUM_CONTENT && (
                    <p className="micro-point-offers__price">{item.price.toLocaleString()}P</p>
                  )}
                </button>
              ))}
            </div>
          </section>
        ))}
      </div>
    </section>
  );
}

