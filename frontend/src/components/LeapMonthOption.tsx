import type { LeapResolutionSource, LunarMonthKind } from "@/types/birthInput";
import "./field.css";

type Props = {
  /** 음력일 때만 부모에서 true 로 렌더 */
  visible: boolean;
  lunarMonthKind: LunarMonthKind;
  onLunarMonthKindChange: (v: LunarMonthKind) => void;
  leapResolutionSource: LeapResolutionSource;
  onLeapResolutionSourceChange: (v: LeapResolutionSource) => void;
  /** KASI 자동 판단 결과 표시용 (선택) */
  kasiResolvedLabel?: string;
};

/**
 * 음력 전용: 평달 / 윤달 선택 + 향후 KASI 자동 모드 전환 구조
 */
export function LeapMonthOption({
  visible,
  lunarMonthKind,
  onLunarMonthKindChange,
  leapResolutionSource,
  onLeapResolutionSourceChange,
  kasiResolvedLabel,
}: Props) {
  if (!visible) return null;

  const isAuto = leapResolutionSource === "kasi_auto";

  return (
    <div className="leap-panel flow-step">
      <div className="leap-panel__title">음력 날짜 세부 설정</div>
      <p className="leap-panel__hint">
        음력에는 같은 해에 같은 달이 두 번 있는 경우(윤달)가 있습니다. 아래에서
        구분해 주세요. KASI 연동 시에는 자동으로 맞출 수 있습니다.
      </p>

      <div className="field field--soft">
        <span className="field__label">윤달 판단</span>
        <div className="segment segment--narrow" role="group">
          <button
            type="button"
            className={`segment__btn${!isAuto ? " segment__btn--active" : ""}`}
            onClick={() => onLeapResolutionSourceChange("user")}
          >
            직접 선택
          </button>
          <button
            type="button"
            className={`segment__btn${isAuto ? " segment__btn--active" : ""}`}
            onClick={() => onLeapResolutionSourceChange("kasi_auto")}
            title="천문연 API 연동 후 사용"
          >
            자동 (KASI)
          </button>
        </div>
      </div>

      {isAuto ? (
        <div className="leap-panel__auto">
          {kasiResolvedLabel ? (
            <p className="leap-panel__resolved">{kasiResolvedLabel}</p>
          ) : (
            <p className="leap-panel__pending">
              연동 시 이 자리에 KASI 기준 평달/윤달 결과가 표시됩니다.
            </p>
          )}
        </div>
      ) : (
        <div className="field field--soft">
          <span className="field__label">해당 음력일이 속한 달</span>
          <div className="segment segment--leap" role="group" aria-label="평달 또는 윤달">
            <button
              type="button"
              className={`segment__btn${lunarMonthKind === "normal" ? " segment__btn--active" : ""}`}
              onClick={() => onLunarMonthKindChange("normal")}
            >
              평달
            </button>
            <button
              type="button"
              className={`segment__btn${lunarMonthKind === "leap" ? " segment__btn--active" : ""}`}
              onClick={() => onLunarMonthKindChange("leap")}
            >
              윤달
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
