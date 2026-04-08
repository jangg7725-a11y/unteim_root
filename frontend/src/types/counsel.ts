/**
 * 리포트 기반 AI 상담 메시지 (자유 챗봇과 구분: role + 메타로 상담 맥락 유지)
 *
 * UI/TTS: 질문 → thinking → 응답 후 baseline(표현층+감정층) → TTS speaking → baseline
 * 감정 baseline은 assistant 본문 키워드 매핑(analyzeAssistantEmotion), TTS/thinking 중 미적용
 * baseline은 { emotion, level(1~3) } + 향후 TTS용 VoiceTone 매핑
 */
export type CounselRole = "user" | "assistant";

/** 감정 종류 — 행동 phase(idle/thinking/speaking)와 별개 */
export type CharacterEmotion =
  | "idle"
  | "comfort"
  | "happy"
  | "serious"
  | "sad"
  | "excited";

/** 감정 강도: 1 약함 · 2 중간 · 3 강함 */
export type EmotionLevel = 1 | 2 | 3;

export type CharacterEmotionState = {
  emotion: CharacterEmotion;
  level: EmotionLevel;
};

/** TTS 톤 분리 예비 — 실제 엔진 연동은 후속 */
export type VoiceTone = "neutral" | "soft" | "calm" | "serious" | "bright";

export const IDLE_EMOTION_STATE: CharacterEmotionState = { emotion: "idle", level: 2 };

export function emotionToVoiceTone(emotion: CharacterEmotion): VoiceTone {
  switch (emotion) {
    case "comfort":
      return "soft";
    case "happy":
      return "bright";
    case "serious":
      return "serious";
    case "sad":
      return "calm";
    case "excited":
      return "bright";
    case "idle":
      return "neutral";
  }
}
export type CounselCharacterId = "undol" | "unsuni";

/** 구조 설명 vs 감정 문장 — 캐릭터 baseline(guiding / empathizing) 분기 */
export type CounselTypeHint = "analysis" | "emotion";

/** 상담 응답 후 요약 카드 — 핵심 흐름·주의·추천 행동 */
export type CounselSessionCardPayload = {
  flow: string;
  cautions: string;
  actions: string[];
};

export interface CounselMessage {
  id: string;
  role: CounselRole;
  /** 사주 해설 상담 본문 */
  text: string;
  /**
   * 상담 톤 힌트 — 없으면 본문 키워드로 보조 추론
   * - analysis: 구조·해설 → guiding, 운돌이 중심
   * - emotion: 공감·위로 → empathizing, 운순이 등장
   */
  counselType?: CounselTypeHint;
  /** 운돌이 / 운순이 — 리포트 구역·톤에 맞게 서버 또는 클라이언트가 지정 */
  character?: CounselCharacterId;
  /** 사전 생성된 음성 URL (CDN 등) */
  audio_url?: string;
  /** 클라이언트/Worker에서 생성한 Blob — revoke는 TTSService가 관리 */
  audio_blob?: Blob;
  /** 동일 문장 재생 시 캐시 키 (없으면 text+voice로 해시) */
  tts_cache_key?: string;
}
