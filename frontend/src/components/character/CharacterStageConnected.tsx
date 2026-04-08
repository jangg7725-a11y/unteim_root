import { useCharacterCounsel } from "@/counsel/CharacterCounselContext";
import { CharacterStage } from "./CharacterStage";

/** Context의 expression · stageCharacterId · animPhase · 감정 baseline · TTS */
export function CharacterStageConnected() {
  const {
    stageCharacterId,
    expression,
    isTtsPlaying,
    characterAnimPhase,
    characterBaselineEmotion,
    currentTone,
  } = useCharacterCounsel();
  return (
    <CharacterStage
      characterId={stageCharacterId}
      expression={expression}
      animPhase={characterAnimPhase}
      baselineEmotion={characterBaselineEmotion}
      voiceTone={currentTone}
      ttsActive={isTtsPlaying}
    />
  );
}
