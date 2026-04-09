/**
 * 사주 입력 요약에 쓰는 양력·음력 동시 표기 (korean-lunar-calendar, 서버와 동일 라이브러리 계열).
 */
import KoreanLunarCalendar from "korean-lunar-calendar";
import type { BirthInputPayload } from "@/types/birthInput";

function pad2(n: number): string {
  return String(n).padStart(2, "0");
}

/** YYYY-MM-DD HH:MM */
function joinDateTime(y: number, m: number, d: number, time: string): string {
  return `${y}-${pad2(m)}-${pad2(d)} ${time}`;
}

/**
 * 양력·음력만 (성별 제외). 상담 코너 등에서 재사용.
 * - 양력 입력: 양력(입력) + 음력 환산
 * - 음력 입력: 음력(입력) + 양력 환산
 */
export function formatDualCalendarSegment(birth: BirthInputPayload): string {
  const time = birth.time.trim() || "12:00";
  const parts = birth.date.split("-").map((x) => parseInt(x, 10));
  if (parts.length !== 3 || parts.some((n) => Number.isNaN(n))) {
    return `${birth.date} ${time}`;
  }
  const [yy, mm, dd] = parts;

  if (birth.calendarApi === "solar") {
    const cal = new KoreanLunarCalendar();
    if (!cal.setSolarDate(yy, mm, dd)) {
      return `양력 ${birth.date} ${time}`;
    }
    const l = cal.getLunarCalendar();
    const leapTag = l.intercalation ? "음력(윤) " : "음력 ";
    const lunarLine = `${leapTag}${joinDateTime(l.year, l.month, l.day, time)}`;
    return `양력 ${joinDateTime(yy, mm, dd, time)} · ${lunarLine}`;
  }

  const isLeap = birth.calendarApi === "lunar_leap";
  const cal = new KoreanLunarCalendar();
  if (!cal.setLunarDate(yy, mm, dd, isLeap)) {
    const tag = isLeap ? "음력(윤) " : "음력 ";
    return `${tag}${birth.date} ${time}`;
  }
  const s = cal.getSolarCalendar();
  const leapTag = isLeap ? "음력(윤) " : "음력 ";
  const lunarLine = `${leapTag}${joinDateTime(yy, mm, dd, time)}`;
  const solarLine = `양력 ${joinDateTime(s.year, s.month, s.day, time)}`;
  return `${lunarLine} · ${solarLine}`;
}

/**
 * 입력 요약 박스: 양력·음력 + 성별 한 줄.
 */
export function formatDualCalendarBirthLine(birth: BirthInputPayload | null): string {
  if (!birth) return "사주 입력값을 저장하면 요약이 여기에 표시됩니다.";
  const gender = birth.gender === "male" ? "남성" : "여성";
  return `${formatDualCalendarSegment(birth)} · ${gender}`;
}
