import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import type { CounselCharacterId, CounselMessage } from "@/types/counsel";
import {
  IDLE_EMOTION_STATE,
  emotionToVoiceTone,
  type CharacterEmotionState,
  type VoiceTone,
} from "@/types/counsel";
import type { CharacterAnimPhase, CharacterExpression } from "@/components/character/characterExpression";
import { analyzeAssistantEmotion } from "@/components/character/characterExpression";

function inferExpressionFromText(text: string): CharacterExpression | null {
  if (/주의|조심|무리|과하|위험|너무 많이/i.test(text)) return "gentle_warning";
  if (/이해|공감|힘드|아프|외로|불안|마음/i.test(text)) return "empathizing";
  if (/먼저|순서|구조|방향|정리|단계/i.test(text)) return "guiding";
  return null;
}

/** 메시지 힌트 + 텍스트로 표현층 + 감정 baseline(본문 키워드) */
export function baselineFromMessage(msg: CounselMessage): {
  expression: CharacterExpression;
  stageCharacterId: CounselCharacterId;
  baselineEmotion: CharacterEmotionState;
} {
  const emotionFromText = analyzeAssistantEmotion(msg.text);

  const hint = msg.counselType;
  if (hint === "emotion") {
    return {
      expression: "empathizing",
      stageCharacterId: "unsuni",
      baselineEmotion: emotionFromText,
    };
  }
  if (hint === "analysis") {
    return {
      expression: "guiding",
      stageCharacterId: "undol",
      baselineEmotion: emotionFromText,
    };
  }
  const inferred = inferExpressionFromText(msg.text);
  if (inferred) {
    return {
      expression: inferred,
      stageCharacterId: msg.character ?? (inferred === "empathizing" ? "unsuni" : "undol"),
      baselineEmotion: emotionFromText,
    };
  }
  if (msg.text.trim()) {
    return {
      expression: "guiding",
      stageCharacterId: msg.character ?? "undol",
      baselineEmotion: emotionFromText,
    };
  }
  return {
    expression: "idle",
    stageCharacterId: msg.character ?? "undol",
    baselineEmotion: emotionFromText,
  };
}

export interface CharacterCounselContextValue {
  expression: CharacterExpression;
  stageCharacterId: CounselCharacterId;
  isTtsPlaying: boolean;
  /** idle=호흡 baseline, thinking=응답 대기, speaking=TTS */
  characterAnimPhase: CharacterAnimPhase;
  /**
   * 감정 연출 레이어 — thinking/speaking 중에는 시각 중립(idle), 그 외 assistant 본문 기반
   */
  characterBaselineEmotion: CharacterEmotionState;
  /** 감정 → 향후 TTS 톤 매핑 (엔진 연동 전 구조만) */
  currentTone: VoiceTone;
  notifyTtsPlay: (characterId: CounselCharacterId) => void;
  notifyTtsEnd: () => void;
  notifyThinking: (characterId?: CounselCharacterId) => void;
}

const CharacterCounselContext = createContext<CharacterCounselContextValue | null>(null);

type ProviderProps = {
  children: ReactNode;
  lastAssistantMessage?: CounselMessage;
};

export function CharacterCounselProvider({ children, lastAssistantMessage }: ProviderProps) {
  const [isTtsPlaying, setIsTtsPlaying] = useState(false);
  const [ttsCharacterId, setTtsCharacterId] = useState<CounselCharacterId>("undol");
  const [awaitingAssistantReply, setAwaitingAssistantReply] = useState(false);
  const [thinkingCharacterId, setThinkingCharacterId] = useState<CounselCharacterId>("undol");
  const waitAssistantFingerprintRef = useRef<string | undefined>(undefined);

  const snapshot = useMemo(() => {
    if (isTtsPlaying) {
      return {
        expression: "speaking" as const,
        stageCharacterId: ttsCharacterId,
        baselineEmotion: IDLE_EMOTION_STATE,
      };
    }
    if (awaitingAssistantReply) {
      return {
        expression: "thinking" as const,
        stageCharacterId: thinkingCharacterId,
        baselineEmotion: IDLE_EMOTION_STATE,
      };
    }
    if (lastAssistantMessage?.role === "assistant") {
      return baselineFromMessage(lastAssistantMessage);
    }
    return {
      expression: "idle" as const,
      stageCharacterId: "undol" as const,
      baselineEmotion: IDLE_EMOTION_STATE,
    };
  }, [
    isTtsPlaying,
    ttsCharacterId,
    awaitingAssistantReply,
    thinkingCharacterId,
    lastAssistantMessage,
  ]);

  const characterAnimPhase = useMemo((): CharacterAnimPhase => {
    if (isTtsPlaying) return "speaking";
    if (awaitingAssistantReply) return "thinking";
    return "idle";
  }, [isTtsPlaying, awaitingAssistantReply]);

  /** TTS·thinking 중에는 감정 레이어 덮어쓰지 않음 → 시각 중립 */
  const characterBaselineEmotion = useMemo((): CharacterEmotionState => {
    if (isTtsPlaying || awaitingAssistantReply) return IDLE_EMOTION_STATE;
    return snapshot.baselineEmotion;
  }, [isTtsPlaying, awaitingAssistantReply, snapshot.baselineEmotion]);

  const currentTone = useMemo((): VoiceTone => {
    if (isTtsPlaying || awaitingAssistantReply) return "neutral";
    return emotionToVoiceTone(snapshot.baselineEmotion.emotion);
  }, [isTtsPlaying, awaitingAssistantReply, snapshot.baselineEmotion]);

  const notifyTtsPlay = useCallback((characterId: CounselCharacterId) => {
    setAwaitingAssistantReply(false);
    setIsTtsPlaying(true);
    setTtsCharacterId(characterId);
  }, []);

  const notifyTtsEnd = useCallback(() => {
    setIsTtsPlaying(false);
  }, []);

  const notifyThinking = useCallback(
    (characterId?: CounselCharacterId) => {
      setThinkingCharacterId(characterId ?? "undol");
      waitAssistantFingerprintRef.current = lastAssistantMessage?.id;
      setAwaitingAssistantReply(true);
    },
    [lastAssistantMessage?.id]
  );

  useEffect(() => {
    if (isTtsPlaying) return;
    const cur = lastAssistantMessage?.id;
    if (!awaitingAssistantReply) return;
    if (cur !== undefined && cur !== waitAssistantFingerprintRef.current) {
      setAwaitingAssistantReply(false);
    }
  }, [lastAssistantMessage?.id, isTtsPlaying, awaitingAssistantReply]);

  const value = useMemo(
    () => ({
      expression: snapshot.expression,
      stageCharacterId: snapshot.stageCharacterId,
      isTtsPlaying,
      characterAnimPhase,
      characterBaselineEmotion,
      currentTone,
      notifyTtsPlay,
      notifyTtsEnd,
      notifyThinking,
    }),
    [
      snapshot.expression,
      snapshot.stageCharacterId,
      isTtsPlaying,
      characterAnimPhase,
      characterBaselineEmotion,
      currentTone,
      notifyTtsPlay,
      notifyTtsEnd,
      notifyThinking,
    ]
  );

  return (
    <CharacterCounselContext.Provider value={value}>{children}</CharacterCounselContext.Provider>
  );
}

export function useCharacterCounsel(): CharacterCounselContextValue {
  const ctx = useContext(CharacterCounselContext);
  if (!ctx) {
    throw new Error("useCharacterCounsel must be used within CharacterCounselProvider");
  }
  return ctx;
}

export function useCharacterCounselOptional(): CharacterCounselContextValue | null {
  return useContext(CharacterCounselContext);
}
