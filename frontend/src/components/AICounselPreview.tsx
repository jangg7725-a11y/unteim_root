import "./ai-counsel-preview.css";

type Props = {
  onClick: () => void;
};

export function AICounselPreview({ onClick }: Props) {
  return (
    <section className="ai-counsel-preview" aria-label="AI 상담 안내">
      <button type="button" className="ai-counsel-preview__cta" onClick={onClick}>
        👉 내 상황 지금 상담으로 풀어보기
      </button>
    </section>
  );
}

