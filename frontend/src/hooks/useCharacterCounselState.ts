import { useMemo } from "react";
import type { CounselCharacterId, CounselMessage } from "@/types/counsel";
import { IDLE_EMOTION_STATE, emotionToVoiceTone, type CharacterEmotionState, type VoiceTone } from "@/types/counsel";
import type { CharacterExpression } from "@/components/character/characterExpression";
import { baselineFromMessage } from "@/counsel/CharacterCounselContext";

export interface CharacterCounselInputs {
  activeCharacter: CounselCharacterId;
  isTtsPlaying: boolean;
  isAssistantStreaming: boolean;
  isAwaitingUser: boolean;
  awaitingAssistantReply?: boolean;
  lastAssistant: CounselMessage | undefined;
}

export interface CharacterCounselSnapshot {
  characterId: CounselCharacterId;
  expression: CharacterExpression;
  baselineEmotion: CharacterEmotionState;
  currentTone: VoiceTone;
}

/**
 * Provider 없는 화면용 스냅샷 — 실제 앱은 CharacterCounselProvider 권장
 */
export function useCharacterCounselState(input: CharacterCounselInputs): CharacterCounselSnapshot {
  return useMemo(() => {
    const {
      activeCharacter,
      isTtsPlaying,
      isAssistantStreaming,
      isAwaitingUser,
      awaitingAssistantReply,
      lastAssistant,
    } = input;

    if (isTtsPlaying) {
      return {
        characterId: activeCharacter,
        expression: "speaking",
        baselineEmotion: IDLE_EMOTION_STATE,
        currentTone: "neutral",
      };
    }
    if (awaitingAssistantReply) {
      return {
        characterId: activeCharacter,
        expression: "thinking",
        baselineEmotion: IDLE_EMOTION_STATE,
        currentTone: "neutral",
      };
    }
    if (isAssistantStreaming) {
      return {
        characterId: activeCharacter,
        expression: "guiding",
        baselineEmotion: IDLE_EMOTION_STATE,
        currentTone: "neutral",
      };
    }
    if (isAwaitingUser) {
      return {
        characterId: activeCharacter,
        expression: "idle",
        baselineEmotion: IDLE_EMOTION_STATE,
        currentTone: "neutral",
      };
    }
    if (lastAssistant?.role === "assistant") {
      const b = baselineFromMessage(lastAssistant);
      return {
        characterId: b.stageCharacterId,
        expression: b.expression,
        baselineEmotion: b.baselineEmotion,
        currentTone: emotionToVoiceTone(b.baselineEmotion.emotion),
      };
    }
    return {
      characterId: activeCharacter,
      expression: "thinking",
      baselineEmotion: IDLE_EMOTION_STATE,
      currentTone: "neutral",
    };
  }, [
    input.activeCharacter,
    input.isTtsPlaying,
    input.isAssistantStreaming,
    input.isAwaitingUser,
    input.awaitingAssistantReply,
    input.lastAssistant,
  ]);
}
