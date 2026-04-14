import { useEffect, useId, useRef, useState } from "react";
import type { BirthInputPayload } from "@/types/birthInput";
import type { MicroPointOfferItem } from "@/data/microPointOffersMock";
import { postSoloLoveInsight, type SoloLoveInsightResult } from "@/services/soloLoveInsightApi";
import "./micro-point-single-modal.css";

const PREFILL_KEY = "unteim_counsel_prefill";

type Props = {
  item: MicroPointOfferItem | null;
  birth: BirthInputPayload | null;
  onClose: () => void;
  onGoCounsel: () => void;
};

export function MicroPointSingleModal({ item, birth, onClose, onGoCounsel }: Props) {
  const titleId = useId();
  const closeRef = useRef<HTMLButtonElement>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [insight, setInsight] = useState<SoloLoveInsightResult | null>(null);

  useEffect(() => {
    if (!item) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    closeRef.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = prev;
      window.removeEventListener("keydown", onKey);
    };
  }, [item, onClose]);

  useEffect(() => {
    if (!item || !birth) {
      setInsight(null);
      setErr(null);
      return;
    }
    let cancelled = false;
    const topic = item.topicHint ?? "general";
    setLoading(true);
    setErr(null);
    setInsight(null);
    postSoloLoveInsight(birth, topic)
      .then((d) => {
        if (!cancelled) setInsight(d);
      })
      .catch((e) => {
        if (!cancelled) setErr(e instanceof Error ? e.message : "불러오기에 실패했습니다.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [item, birth]);

  const prefillAndGo = (text: string) => {
    try {
      sessionStorage.setItem(PREFILL_KEY, text);
    } catch {
      /* */
    }
    onClose();
    onGoCounsel();
  };

  if (!item) return null;

  return (
    <div className="micro-single-modal__backdrop" role="presentation">
      <button type="button" className="micro-single-modal__clickout" aria-label="닫기" onClick={onClose} />
      <div className="micro-single-modal" role="dialog" aria-modal="true" aria-labelledby={titleId}>
        <header className="micro-single-modal__head">
          <h3 id={titleId} className="micro-single-modal__title">
            {item.question}
          </h3>
          <button ref={closeRef} type="button" className="micro-single-modal__close" onClick={onClose} aria-label="닫기">
            ×
          </button>
        </header>

        {!birth ? (
          <p className="micro-single-modal__body micro-single-modal__body--warn" role="alert">
            사주 정보가 없습니다. 사주 입력 탭에서 저장한 뒤 다시 시도해 주세요.
          </p>
        ) : loading ? (
          <p className="micro-single-modal__state" role="status">
            사주 기반 해석 문장을 준비하고 있습니다…
          </p>
        ) : err ? (
          <p className="micro-single-modal__body micro-single-modal__body--warn" role="alert">
            {err}
          </p>
        ) : insight ? (
          <div className="micro-single-modal__insight">
            <p className="micro-single-modal__lead">{insight.summary}</p>
            <section>
              <h4 className="micro-single-modal__subh">핵심 (참고)</h4>
              <p className="micro-single-modal__para">{insight.pullsIn}</p>
            </section>
            <section>
              <p className="micro-single-modal__para">{insight.energy}</p>
            </section>
            {insight.topicNote ? <p className="micro-single-modal__para">{insight.topicNote}</p> : null}
            <p className="micro-single-modal__fine">{insight.disclaimer}</p>
          </div>
        ) : null}

        <div className="micro-single-modal__actions">
          <button type="button" className="micro-single-modal__ghost" onClick={onClose}>
            닫기
          </button>
          {birth && insight ? (
            <>
              <button
                type="button"
                className="micro-single-modal__secondary"
                onClick={() =>
                  prefillAndGo(
                    `${item.question} 에 대해, 위 1차 해석을 바탕으로 더 구체적으로 사주 근거를 알고 싶어요.`,
                  )
                }
              >
                질문 이어가기
              </button>
              <button
                type="button"
                className="micro-single-modal__primary"
                onClick={() => {
                  onClose();
                  onGoCounsel();
                }}
              >
                AI 상담으로 자세히 상담받기 (유료)
              </button>
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}
