import type { CounselCharacterId, CharacterEmotionState, VoiceTone } from "@/types/counsel";
import type { CharacterAnimPhase, CharacterExpression } from "./characterExpression";
import { CHARACTER_COPY } from "./characterExpression";
import "./character.css";

type Props = {
  characterId: CounselCharacterId;
  expression: CharacterExpression;
  animPhase: CharacterAnimPhase;
  baselineEmotion: CharacterEmotionState;
  voiceTone?: VoiceTone;
  ttsActive?: boolean;
  className?: string;
};

/**
 * MVP: div + className — animPhase로 breathe / tilt / talk, baselineEmotion으로 미세 톤
 */
export function CharacterAvatar({
  characterId,
  expression,
  animPhase,
  baselineEmotion,
  voiceTone = "neutral",
  ttsActive,
  className = "",
}: Props) {
  const copy = CHARACTER_COPY[characterId];
  const speakingMotion = animPhase === "speaking" && ttsActive;
  const { emotion, level } = baselineEmotion;

  return (
    <div
      className={`char-avatar char-avatar--${characterId} char-avatar--${expression} char-motion--${animPhase} char-emotion-${emotion} char-level-${level} char-tone-${voiceTone}${speakingMotion ? " char-avatar--tts-mouth" : ""} ${className}`.trim()}
      data-character={characterId}
      data-expression={expression}
      data-char-anim={animPhase}
      data-char-emotion={emotion}
      data-char-level={level}
      data-voice-tone={voiceTone}
      data-tts-active={ttsActive ? "true" : undefined}
      role="img"
      aria-label={`${copy.title}, ${expression}`}
    >
      <div className="char-avatar__silhouette" />
      <div className="char-avatar__face">
        <span className="char-avatar__eyes" aria-hidden />
        <span className="char-avatar__mouth" aria-hidden />
      </div>
      <p className="char-avatar__caption">
        <strong>{copy.title}</strong>
        <span className="char-avatar__sub">{copy.subtitle}</span>
      </p>
    </div>
  );
}
