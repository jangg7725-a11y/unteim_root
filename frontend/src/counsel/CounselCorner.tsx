import { useEffect, useMemo, useState, type Dispatch, type FormEvent, type SetStateAction } from "react";
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

function CounselIntroPanel() {
  const { birth, reportData } = useSajuSession();
  if (!birth) return null;
  if (!reportData) {
    return (
      <section className="counsel-intro" aria-label="1차 사주 요약">
        <p className="counsel-intro__text">
          리포트 탭에서 사주 분석을 생성하면, 여기에 <strong>엔진 기반 요약</strong>이 먼저 표시됩니다. AI 대화는 선택
          사항이며 이용 시 비용이 발생할 수 있습니다.
        </p>
      </section>
    );
  }
  const snippet = (reportData.total || "").trim();
  const short = snippet.length > 320 ? `${snippet.slice(0, 320)}…` : snippet;
  return (
    <section className="counsel-intro" aria-label="1차 사주 요약">
      <h2 className="counsel-intro__title">1차 · 사주 기반 요약 (참고)</h2>
      <p className="counsel-intro__body">{short || "요약 텍스트가 준비되지 않았습니다."}</p>
      <p className="counsel-intro__fine" role="note">
        아래 대화는 AI 상담으로 이어질 수 있으며, <strong>이용 시 비용이 발생할 수 있습니다</strong>. 먼저 위 요약으로
        흐름을 파악한 뒤 필요할 때만 이어가 보세요.
      </p>
    </section>
  );
}

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

  useEffect(() => {
    try {
      const pref = sessionStorage.getItem("unteim_counsel_prefill");
      if (pref && birth) {
        setDraft((d) => (d.trim() ? d : pref));
        sessionStorage.removeItem("unteim_counsel_prefill");
      }
    } catch {
      /* ignore */
    }
  }, [birth, setDraft]);

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

        {birth && <CounselIntroPanel />}

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
