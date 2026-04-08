import type { VoiceTone } from "@/types/counsel";

/** Web Audio / SpeechSynthesis에 적용할 상대 배율 (1 = 기본) */
export type TonePlayback = {
  /** 재생 속도 배율 (comfort 느리게, happy 빠르게 등) */
  rate: number;
  /** 피치 배율 (낮게/높게) */
  pitch: number;
};

/**
 * VoiceTone → TTS 재생 특성
 * - soft(comfort 계열): rate 낮춤, pitch 낮춤
 * - serious: 또박또박
 * - bright(happy): 약간 빠르고 밝게
 * - calm(sad): 느리고 낮게
 */
export function getTonePlayback(tone: VoiceTone | undefined): TonePlayback {
  switch (tone) {
    case "soft":
      return { rate: 0.9, pitch: 0.92 };
    case "calm":
      return { rate: 0.85, pitch: 0.88 };
    case "serious":
      return { rate: 1.0, pitch: 0.96 };
    case "bright":
      return { rate: 1.1, pitch: 1.06 };
    case "neutral":
    default:
      return { rate: 1.0, pitch: 1.0 };
  }
}
