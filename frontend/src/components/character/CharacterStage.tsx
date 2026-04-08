import type { CounselCharacterId, CharacterEmotionState, VoiceTone } from "@/types/counsel";
import type { CharacterAnimPhase, CharacterExpression } from "./characterExpression";
import { CharacterAvatar } from "./CharacterAvatar";
import { CharacterStateController } from "./CharacterStateController";
import "./character.css";

type Props = {
  characterId: CounselCharacterId;
  expression: CharacterExpression;
  animPhase: CharacterAnimPhase;
  baselineEmotion: CharacterEmotionState;
  /** TTS·캐릭터 연동 음성 톤 */
  voiceTone?: VoiceTone;
  ttsActive?: boolean;
};

/**
 * 상담 캐릭터 스테이지 — 우하단 고정은 .char-stage--dock (character.css)
 */
export function CharacterStage({
  characterId,
  expression,
  animPhase,
  baselineEmotion,
  voiceTone = "neutral",
  ttsActive,
}: Props) {
  return (
    <div className="char-stage char-stage--dock">
      <CharacterStateController
        expression={expression}
        animPhase={animPhase}
        baselineEmotion={baselineEmotion}
        voiceTone={voiceTone}
        ttsActive={ttsActive}
      >
        <div
          className="char-stage__inner"
          data-tts-active={ttsActive ? "true" : undefined}
          data-char-anim={animPhase}
          data-char-emotion={baselineEmotion.emotion}
          data-char-level={baselineEmotion.level}
          data-voice-tone={voiceTone}
        >
          <CharacterAvatar
            characterId={characterId}
            expression={expression}
            animPhase={animPhase}
            baselineEmotion={baselineEmotion}
            voiceTone={voiceTone}
            ttsActive={ttsActive}
          />
        </div>
      </CharacterStateController>
    </div>
  );
}
