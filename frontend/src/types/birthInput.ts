/**
 * 사주 입력 화면 상태 · API 전송용 페이로드.
 *
 * 백엔드(`AnalyzeRequest`)와 맞추기:
 * - `calendar`: "solar" | "lunar" | "lunar_leap"
 * - 음력일 때: 서버 `normalize_birth_string`(korean-lunar-calendar)으로 양력일+동일 시각(KST)으로 바꾼 뒤
 *   절기·월주·대운 등 전부 그 양력 시각을 사용한다. 양력이면 date/time을 그대로 사용한다.
 */

export type CalendarKind = "solar" | "lunar";

/** 음력에서 해당 일이 평달인지 윤달(윤N월)인지 — 사용자 수동 또는 KASI 결과 */
export type LunarMonthKind = "normal" | "leap";

/**
 * 윤달 판단 주체
 * - user: 화면에서 평달/윤달 선택
 * - kasi_auto: 천문연(KASI) 등 API로 자동 (UI는 결과만 표시하거나 숨김)
 */
export type LeapResolutionSource = "user" | "kasi_auto";

export interface BirthFormState {
  date: string;
  time: string;
  gender: "" | "male" | "female";
  calendar: CalendarKind;
  lunarMonthKind: LunarMonthKind;
  leapResolutionSource: LeapResolutionSource;
}

export interface BirthInputPayload {
  date: string;
  time: string;
  gender: "male" | "female";
  calendar: CalendarKind;
  /** API 문자열로 보낼 때: solar | lunar | lunar_leap */
  calendarApi: "solar" | "lunar" | "lunar_leap";
  lunarMonthKind?: LunarMonthKind;
  leapResolutionSource: LeapResolutionSource;
}

export function toCalendarApi(
  calendar: CalendarKind,
  lunarMonthKind: LunarMonthKind
): "solar" | "lunar" | "lunar_leap" {
  if (calendar === "solar") return "solar";
  return lunarMonthKind === "leap" ? "lunar_leap" : "lunar";
}

export function buildBirthPayload(state: BirthFormState): BirthInputPayload | null {
  if (!state.date || !state.time || !state.gender) return null;
  const calendarApi = toCalendarApi(state.calendar, state.lunarMonthKind);
  return {
    date: state.date,
    time: state.time,
    gender: state.gender,
    calendar: state.calendar,
    calendarApi,
    lunarMonthKind: state.calendar === "lunar" ? state.lunarMonthKind : undefined,
    leapResolutionSource: state.leapResolutionSource,
  };
}

/** 저장된 사주를 입력 화면 폼에 되돌릴 때 사용 */
export function birthPayloadToFormState(b: BirthInputPayload): BirthFormState {
  const lunarMonthKind: LunarMonthKind =
    b.calendar === "lunar"
      ? b.calendarApi === "lunar_leap"
        ? "leap"
        : (b.lunarMonthKind ?? "normal")
      : "normal";
  return {
    date: b.date,
    time: b.time,
    gender: b.gender,
    calendar: b.calendar,
    lunarMonthKind,
    leapResolutionSource: b.leapResolutionSource,
  };
}
