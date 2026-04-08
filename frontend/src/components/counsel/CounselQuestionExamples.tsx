const EXAMPLES = [
  "올해 흐름을 사주 기준으로 자세히 알고 싶어요",
  "지금 움직여도 될까요?",
  "이 관계 계속 이어가도 될까요?",
  "지금 선택이 맞을까요?",
];

export function CounselQuestionExamples() {
  return (
    <section className="ai-counsel-examples" aria-label="질문 예시">
      <h3 className="ai-counsel-examples__title">이런 질문을 상담할 수 있어요</h3>
      <div className="ai-counsel-examples__list">
        {EXAMPLES.map((q) => (
          <p key={q} className="ai-counsel-examples__item">
            {q}
          </p>
        ))}
      </div>
    </section>
  );
}

