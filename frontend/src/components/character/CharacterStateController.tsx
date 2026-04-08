import type { ReactNode } from "react";
import type { CharacterEmotionState, VoiceTone } from "@/types/counsel";
import type { CharacterAnimPhase, CharacterExpression } from "./characterExpression";
import "./character.css";

type Props = {
  expression: CharacterExpression;
  animPhase: CharacterAnimPhase;
  baselineEmotion: CharacterEmotionState;
  voiceTone?: VoiceTone;
  intensity?: "low" | "normal";
  ttsActive?: boolean;
  children: ReactNode;
};

/**
 * 톤(expression) + 행동(animPhase) + 감정 baseline(emotion) — CSS 클래스 병행
 */
export function CharacterStateController({
  expression,
  animPhase,
  baselineEmotion,
  voiceTone = "neutral",
  intensity = "normal",
  ttsActive,
  children,
}: Props) {
  const { emotion, level } = baselineEmotion;
  return (
    <div
      className={`char-state char-state--${expression} char-state--anim-${animPhase} char-emotion-${emotion} char-level-${level} char-tone-${voiceTone} char-state--i-${intensity}${ttsActive ? " char-state--tts tts-active" : ""}`}
      data-expression={expression}
      data-char-anim={animPhase}
      data-char-emotion={emotion}
      data-char-level={level}
      data-voice-tone={voiceTone}
      data-tts-active={ttsActive ? "true" : undefined}
    >
      {children}
    </div>
  );
}
