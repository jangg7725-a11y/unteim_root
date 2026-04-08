import type { CounselCharacterId } from "@/types/counsel";
import type {
  CharacterEmotion,
  CharacterEmotionState,
  EmotionLevel,
} from "@/types/counsel";

/**
 * 캐릭터 표현 상태 — TTS/AI 스트림/문장 톤과 연동
 * - MVP: 이미지 교체 또는 CSS 보조 모션
 * - 확장: Lottie(JSON) / Live2D 레이어
 */
export type CharacterExpression =
  | "idle"
  | "speaking"
  | "guiding"
  | "empathizing"
  | "thinking"
  | "gentle_warning";

/**
 * 행동 상태(몸 애니메이션) — thinking / speaking 은 여기서만
 * - idle: 호흡(breathe) — 기본 대기·baseline 감정 레이어와 동시 사용
 * - thinking: 응답 대기(tilt)
 * - speaking: TTS(talk)
 */
export type CharacterAnimPhase = "idle" | "thinking" | "speaking";

/** @deprecated Prefer CharacterEmotion from @/types/counsel — 문자열 감정만 필요할 때 */
export type CharacterBaselineEmotion = CharacterEmotion;

/** 우선순위: serious > sad > comfort > excited > happy > idle */
const SERIOUS = /주의|조심|경계|신중|리스크|점검|과열|충돌/;
const SAD = /힘들|지친|외롭|불안|답답|속상|상처|무거/;
const COMFORT = /괜찮|천천히|무리|위로|마음|걱정|함께|다독|편안/;
const EXCITED = /변화|도전|시작|확장|상승|전환|열림|움직/;
const HAPPY = /좋|기회|행운|축하|반갑|잘될|가능성|맑/;

const LEVEL3 = /정말|반드시|지금은 꼭|절대|매우|크게|강하게/;
const LEVEL1 = /조금|약간|가볍게|천천히/;

function emotionKindFromText(text: string): CharacterEmotion {
  const t = text.trim();
  if (!t) return "idle";
  if (SERIOUS.test(t)) return "serious";
  if (SAD.test(t)) return "sad";
  if (COMFORT.test(t)) return "comfort";
  if (EXCITED.test(t)) return "excited";
  if (HAPPY.test(t)) return "happy";
  return "idle";
}

function emotionLevelFromText(text: string): EmotionLevel {
  const t = text.trim();
  if (!t) return 2;
  if (/!/.test(t) || LEVEL3.test(t)) return 3;
  if (LEVEL1.test(t)) return 1;
  return 2;
}

/**
 * assistant 메시지 본문 → 감정 baseline(kind + 강도)
 * - 감정 종류: 기존 키워드 우선순위 유지
 * - 강도: 강조/느낌표 → 3, 완화어 → 1, 그 외 2
 */
export function analyzeAssistantEmotion(text: string): CharacterEmotionState {
  return {
    emotion: emotionKindFromText(text),
    level: emotionLevelFromText(text),
  };
}

/** 역할: 운돌이=구조·안내, 운순이=공감·위로 (리포트 구역에 맞게 선택) */
export const CHARACTER_COPY: Record<
  CounselCharacterId,
  { title: string; subtitle: string }
> = {
  undol: { title: "운돌이", subtitle: "구조와 방향을 짚어 드려요" },
  unsuni: { title: "운순이", subtitle: "마음이 스며들도록 함께해요" },
};
