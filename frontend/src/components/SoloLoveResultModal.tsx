import { useEffect, useId, useRef } from "react";
import type { SoloLoveInsightResult } from "@/services/soloLoveInsightApi";
import "./solo-love-result-modal.css";

type Props = {
  open: boolean;
  data: SoloLoveInsightResult | null;
  loading?: boolean;
  error?: string | null;
  onClose: () => void;
  /** AI 상담 탭 */
  onGoCounsel: () => void;
  /** 상담 입력창에 질문 문장 넣기 */
  onPrefillCounsel: (text: string) => void;
};

export function SoloLoveResultModal({
  open,
  data,
  loading,
  error,
  onClose,
  onGoCounsel,
  onPrefillCounsel,
}: Props) {
  const titleId = useId();
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
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
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="solo-love__backdrop" role="presentation">
      <button type="button" className="solo-love__clickout" aria-label="닫기" onClick={onClose} />
      <div className="solo-love" role="dialog" aria-modal="true" aria-labelledby={titleId}>
        <header className="solo-love__head">
          <h3 id={titleId} className="solo-love__title">
            본인 사주 기반 인연 참고
          </h3>
          <button ref={closeRef} type="button" className="solo-love__close" onClick={onClose} aria-label="닫기">
            ×
          </button>
        </header>

        {loading ? (
          <p className="solo-love__state" role="status">
            사주를 불러와 해석 문장을 준비하고 있습니다…
          </p>
        ) : null}
        {error ? (
          <p className="solo-love__err" role="alert">
            {error}
          </p>
        ) : null}

        {!loading && !error && data ? (
          <div className="solo-love__body">
            <p className="solo-love__summary">{data.summary}</p>
            <section className="solo-love__block">
              <h4 className="solo-love__label">끌림·반응 패턴</h4>
              <p>{data.pullsIn}</p>
            </section>
            <section className="solo-love__block">
              <h4 className="solo-love__label">인연·만남 흐름 (참고)</h4>
              <p>{data.likelyBond}</p>
            </section>
            <section className="solo-love__block">
              <h4 className="solo-love__label">연애 에너지·감정 축</h4>
              <p>{data.energy}</p>
            </section>
            <section className="solo-love__block solo-love__block--muted">
              <h4 className="solo-love__label">오행 균형 (참고)</h4>
              <p>{data.balanceNote}</p>
            </section>
            <section className="solo-love__block solo-love__block--muted">
              <h4 className="solo-love__label">이번 달 흐름</h4>
              <p>{data.monthlyFlow}</p>
            </section>
            {data.topicNote ? (
              <section className="solo-love__block">
                <p>{data.topicNote}</p>
              </section>
            ) : null}
            <p className="solo-love__disclaimer" role="note">
              {data.disclaimer}
            </p>
          </div>
        ) : null}

        <div className="solo-love__actions">
          <button type="button" className="solo-love__ghost" onClick={onClose}>
            닫기
          </button>
          <button
            type="button"
            className="solo-love__secondary"
            onClick={() => {
              onPrefillCounsel(
                "위 해석을 바탕으로 제 연애 흐름을 더 구체적으로 질문하고 싶어요. (사주 근거로 답변 부탁드려요.)",
              );
              onClose();
              onGoCounsel();
            }}
          >
            질문 이어가기
          </button>
          <button
            type="button"
            className="solo-love__primary"
            onClick={() => {
              onClose();
              onGoCounsel();
            }}
          >
            AI 상담으로 자세히 상담받기 (유료)
          </button>
        </div>
      </div>
    </div>
  );
}
