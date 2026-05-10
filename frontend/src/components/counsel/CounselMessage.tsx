import type { CounselMessage as CounselMessageModel } from "@/types/counsel";
import type { VoiceId } from "@/services/ttsService";
import { useCharacterCounselOptional } from "@/counsel/CharacterCounselContext";
import { VoicePlayer } from "./VoicePlayer";
import { CounselFeedback } from "./CounselFeedback";
import "./counsel.css";

type Props = {
  message: CounselMessageModel;
  voice?: VoiceId;
  /** Provider 없을 때만 사용 */
  onPlaybackChange?: (playing: boolean) => void;
  /** 피드백용 세션 ID */
  sessionId?: string;
  counselIntent?: string;
};

export function CounselMessage({ message, voice, onPlaybackChange, sessionId, counselIntent }: Props) {
  const counsel = useCharacterCounselOptional();
  const v: VoiceId = voice ?? message.character ?? "undol";
  const isUser = message.role === "user";

  const charId = message.character ?? "undol";

  return (
    <article
      className={`counsel-msg${isUser ? " counsel-msg--user" : " counsel-msg--assistant"}`}
      data-character={charId}
      data-counsel-type={message.counselType ?? undefined}
    >
      {!isUser && (
        <div className="counsel-msg__badge" aria-hidden>
          {message.character === "unsuni" ? "운순이" : "운돌이"}
        </div>
      )}
      <div className="counsel-msg__bubble">
        <p className="counsel-msg__text">{message.text}</p>
        {!isUser && (
          <div className="counsel-msg__actions">
            <VoicePlayer
              text={message.text}
              voice={v}
              voiceTone={counsel?.currentTone ?? "neutral"}
              initialAudioUrl={message.audio_url}
              initialBlob={message.audio_blob}
              onPlay={counsel ? () => counsel.notifyTtsPlay(charId) : undefined}
              onEnded={counsel ? () => counsel.notifyTtsEnd() : undefined}
              onPlaybackChange={counsel ? undefined : onPlaybackChange}
            />
            {sessionId && (
              <CounselFeedback
                messageId={message.id}
                sessionId={sessionId}
                counselIntent={counselIntent}
                character={message.character}
              />
            )}
          </div>
        )}
      </div>
    </article>
  );
}
