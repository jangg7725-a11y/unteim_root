import { useMemo, useState, type Dispatch, type FormEvent, type SetStateAction } from "react";
import type { CounselMessage as CounselMessageModel } from "@/types/counsel";
import { useSajuSession } from "@/context/SajuSessionContext";
import { CharacterCounselProvider, useCharacterCounsel } from "@/counsel/CharacterCounselContext";
import { CounselMessage } from "@/components/counsel/CounselMessage";
import { CounselSessionCard } from "@/components/counsel/CounselSessionCard";
import { AICounselHero } from "@/components/counsel/AICounselHero";
import { CharacterStageConnected } from "@/components/character/CharacterStageConnected";
import { postCounsel } from "@/services/counselApi";
import type { CounselSessionCardPayload } from "@/types/counsel";
import { COUNSEL_LAYOUT } from "@/config/counselLayout";
import { formatDualCalendarSegment } from "@/utils/calendarDualLabel";
import "./counsel-corner.css";

type InnerProps = {
  draft: string;
  setDraft: Dispatch<SetStateAction<string>>;
  sending: boolean;
  setSending: Dispatch<SetStateAction<boolean>>;
  sessionCard: CounselSessionCardPayload | null;
  setSessionCard: Dispatch<SetStateAction<CounselSessionCardPayload | null>>;
};

function CounselCornerInner({
  draft,
  setDraft,
  sending,
  setSending,
  sessionCard,
  setSessionCard,
}: InnerProps) {
  const { birth, setAnalysisSummary, counselMessages, setCounselMessages } = useSajuSession();
  const { notifyThinking } = useCharacterCounsel();

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const text = draft.trim();
    if (!text || !birth || sending) return;

    const userMsg: CounselMessageModel = {
      id: `u-${Date.now()}`,
      role: "user",
      text,
    };

    notifyThinking();
    setDraft("");
    setSending(true);
    setSessionCard(null);
    setCounselMessages((prev) => [...prev, userMsg]);

    const history = [...counselMessages, userMsg].map((m) => ({
      role: m.role as "user" | "assistant",
      text: m.text,
    }));

    try {
      const res = await postCounsel({
        ...birth,
        name: "",
        messages: history,
      });

      setAnalysisSummary(res.analysisSummary);
      if (res.sessionCard) setSessionCard(res.sessionCard);
      setCounselMessages((prev) => [
        ...prev,
        {
          id: `a-${Date.now()}`,
          role: "assistant",
          text: res.reply,
          character: res.character,
          counselType: res.counselType,
        },
      ]);
    } catch (err) {
      setSessionCard(null);
      const msg = err instanceof Error ? err.message : String(err);
      setCounselMessages((prev) => [
        ...prev,
        {
          id: `a-err-${Date.now()}`,
          role: "assistant",
          text: msg,
          character: "undol",
          counselType: "analysis",
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  return (
    <>
      <CharacterStageConnected />
      {sessionCard && <CounselSessionCard card={sessionCard} />}

      <section className="counsel-corner__content">
        {COUNSEL_LAYOUT.inputSectionPosition === "top" && (
          <form className="counsel-corner__composer counsel-input-section" onSubmit={onSubmit}>
            <label className="visually-hidden" htmlFor="counsel-input">
              상담 질문
            </label>
            <textarea
              id="counsel-input"
              className="counsel-corner__input"
              rows={2}
              placeholder={
                birth
                  ? "예: 제 성격과 올해 흐름을 사주 근거로 알려주세요."
                  : "먼저 사주 입력 탭에서 생년월일을 저장해 주세요."
              }
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              disabled={!birth || sending}
            />
            <button
              type="submit"
              className="counsel-corner__send"
              disabled={!birth || sending || !draft.trim()}
            >
              {sending ? "응답 중…" : "보내기"}
            </button>
          </form>
        )}

        <section className="counsel-corner__thread" aria-label="상담 대화">
          {counselMessages.map((m) => (
            <CounselMessage key={m.id} message={m} />
          ))}
        </section>

        {COUNSEL_LAYOUT.inputSectionPosition === "bottom" && (
          <form className="counsel-corner__composer counsel-input-section" onSubmit={onSubmit}>
            <label className="visually-hidden" htmlFor="counsel-input">
              상담 질문
            </label>
            <textarea
              id="counsel-input"
              className="counsel-corner__input"
              rows={2}
              placeholder={
                birth
                  ? "예: 제 성격과 올해 흐름을 사주 근거로 알려주세요."
                  : "먼저 사주 입력 탭에서 생년월일을 저장해 주세요."
              }
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              disabled={!birth || sending}
            />
            <button
              type="submit"
              className="counsel-corner__send"
              disabled={!birth || sending || !draft.trim()}
            >
              {sending ? "응답 중…" : "보내기"}
            </button>
          </form>
        )}
      </section>
    </>
  );
}

/**
 * 사주 엔진 요약 + OpenAI — 후속 질문은 동일 생년월일로 매 요청 시 엔진 재실행 후 요약 주입
 */
export function CounselCorner() {
  const { birth, analysisSummary, counselMessages } = useSajuSession();
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [sessionCard, setSessionCard] = useState<CounselSessionCardPayload | null>(null);

  const lastAssistant = useMemo(
    () => [...counselMessages].reverse().find((m) => m.role === "assistant"),
    [counselMessages]
  );

  return (
    <CharacterCounselProvider lastAssistantMessage={lastAssistant}>
      <div className="counsel-corner">
        <AICounselHero
          sectionOrder={[...COUNSEL_LAYOUT.heroSectionOrder]}
          characterOrder={[...COUNSEL_LAYOUT.characterOrder]}
          characterLayout={COUNSEL_LAYOUT.characterLayout}
        />

        {!birth && (
          <p className="counsel-corner__warn" role="status">
            AI 상담은 사주 입력 탭에서 생년월일·시간·성별을 모두 입력한 뒤에만 진행할 수 있습니다. 더미 운세는 제공하지
            않습니다.
          </p>
        )}

        {birth && (
          <p className="counsel-corner__meta" aria-live="polite">
            상담 기준: {formatDualCalendarSegment(birth)}
            {analysisSummary ? " · 분석 요약 로드됨" : ""}
          </p>
        )}

        <CounselCornerInner
          draft={draft}
          setDraft={setDraft}
          sending={sending}
          setSending={setSending}
          sessionCard={sessionCard}
          setSessionCard={setSessionCard}
        />
      </div>
    </CharacterCounselProvider>
  );
}
