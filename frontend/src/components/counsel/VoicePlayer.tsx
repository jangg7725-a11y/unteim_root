import { useCallback, useEffect, useId, useRef, useState } from "react";
import type { VoiceTone } from "@/types/counsel";
import type { VoiceId } from "@/services/ttsService";
import { generateTts } from "@/services/ttsService";
import { getTonePlayback } from "@/services/voiceTonePlayback";
import "./counsel.css";

type Props = {
  text: string;
  voice?: VoiceId;
  /** 서버가 미리 준 URL */
  initialAudioUrl?: string;
  /** 서버가 미리 준 Blob */
  initialBlob?: Blob;
  /** 실제 소리가 시작될 때 — speaking 연동 */
  onPlay?: () => void;
  /** 재생 완료·사용자 정지·에러 후 — 비음성 baseline 복귀 트리거 */
  onEnded?: () => void;
  /** 하위 호환: 재생 여부만 필요할 때 */
  onPlaybackChange?: (playing: boolean) => void;
  /** 캐릭터/감정 기반 음성 톤 — 재생 속도·피치에 반영 */
  voiceTone?: VoiceTone;
  /** 레거시: tone 미사용 시에만 기본 배율에 곱함 */
  playbackRate?: number;
};

type PlayState = "idle" | "loading" | "playing";

/**
 * 🔊 듣기 — 클릭 시에만 재생. 캐시된 TTS 또는 브라우저 합성.
 */
export function VoicePlayer({
  text,
  voice = "undol",
  initialAudioUrl,
  initialBlob,
  onPlay,
  onEnded,
  onPlaybackChange,
  voiceTone = "neutral",
  playbackRate = 1,
}: Props) {
  const tone = getTonePlayback(voiceTone);
  const uid = useId();
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [state, setState] = useState<PlayState>("idle");

  const notify = useCallback(
    (playing: boolean) => {
      onPlaybackChange?.(playing);
    },
    [onPlaybackChange]
  );

  const finishPlayback = useCallback(() => {
    setState("idle");
    onEnded?.();
    notify(false);
  }, [onEnded, notify]);

  useEffect(() => {
    return () => {
      const a = audioRef.current;
      if (a) {
        a.pause();
        a.src = "";
      }
      speechSynthesis.cancel();
      notify(false);
    };
  }, [notify]);

  const playAudioUrl = useCallback(
    (url: string): Promise<void> => {
      return new Promise((resolve, reject) => {
        const el = new Audio(url);
        audioRef.current = el;
        el.playbackRate = Math.min(2, Math.max(0.5, playbackRate * tone.rate));
        el.onended = () => resolve();
        el.onerror = () => reject(new Error("audio_error"));
        el.play().catch(reject);
      });
    },
    [playbackRate, tone.rate]
  );

  const playBrowserTts = useCallback(
    (t: string, v: VoiceId): Promise<void> => {
      return new Promise((resolve, reject) => {
        if (!window.speechSynthesis) {
          reject(new Error("no_speech"));
          return;
        }
        const baseRate = v === "undol" ? 0.92 : 1.0;
        const basePitch = v === "undol" ? 0.88 : 1.05;
        const u = new SpeechSynthesisUtterance(t);
        u.lang = "ko-KR";
        u.rate = Math.min(1.5, Math.max(0.5, baseRate * playbackRate * tone.rate));
        u.pitch = Math.min(2, Math.max(0, basePitch * tone.pitch));
        u.onend = () => resolve();
        u.onerror = () => reject(new Error("speech_error"));
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(u);
      });
    },
    [playbackRate, tone.rate, tone.pitch]
  );

  const beginSound = useCallback(() => {
    setState("playing");
    onPlay?.();
    notify(true);
  }, [onPlay, notify]);

  const handleListen = async () => {
    if (!text.trim() || state === "loading") return;
    if (state === "playing") {
      speechSynthesis.cancel();
      const a = audioRef.current;
      if (a) {
        a.pause();
        a.src = "";
      }
      finishPlayback();
      return;
    }

    setState("loading");
    notify(false);

    try {
      if (initialAudioUrl) {
        beginSound();
        await playAudioUrl(initialAudioUrl);
        finishPlayback();
        return;
      }

      if (initialBlob) {
        const url = URL.createObjectURL(initialBlob);
        beginSound();
        try {
          await playAudioUrl(url);
        } finally {
          URL.revokeObjectURL(url);
        }
        finishPlayback();
        return;
      }

      const result = await generateTts(text, { voice });

      if (result.mode === "audio") {
        beginSound();
        for (const seg of result.segments) {
          await playAudioUrl(seg.url);
        }
        finishPlayback();
        return;
      }

      beginSound();
      await playBrowserTts(result.text, result.voice);
      finishPlayback();
    } catch {
      finishPlayback();
    }
  };

  const playing = state === "playing";
  const loading = state === "loading";

  return (
    <div className="voice-player">
      <button
        type="button"
        className={`voice-player__btn${playing ? " voice-player__btn--playing" : ""}${loading ? " voice-player__btn--loading" : ""}`}
        onClick={handleListen}
        disabled={!text.trim()}
        aria-pressed={playing}
        aria-describedby={`${uid}-hint`}
        title={playing ? "재생 중지" : "텍스트 음성 듣기"}
      >
        <span className="voice-player__icon" aria-hidden>
          {loading ? "◌" : "🔊"}
        </span>
        <span className="voice-player__label">{playing ? "정지" : "🔊 듣기"}</span>
        {playing && <span className="voice-player__wave" aria-hidden />}
      </button>
      <span id={`${uid}-hint`} className="visually-hidden">
        자동으로 재생되지 않습니다. 버튼을 눌러 들을 수 있습니다.
      </span>
    </div>
  );
}
