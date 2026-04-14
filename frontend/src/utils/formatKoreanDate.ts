/** 화면 표기용 — 한국 시간 기준 오늘 날짜 (예: 2026년 4월 14일 (화)) */
export function formatKoreanDisplayDate(date: Date = new Date(), timeZone = "Asia/Seoul"): string {
  const ymd = new Intl.DateTimeFormat("ko-KR", {
    timeZone,
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(date);
  const wd = new Intl.DateTimeFormat("ko-KR", {
    timeZone,
    weekday: "short",
  }).format(date);
  return `${ymd} (${wd})`;
}
