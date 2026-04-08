/**
 * REST API 베이스 URL.
 * - 개발: 비우면 상대 경로 `/api/...` → Vite proxy로 백엔드 전달
 * - 배포: `VITE_API_BASE_URL=https://api.example.com` (끝 슬래시 없음)
 *
 * 하위 호환: 예전 이름 `VITE_API_BASE`도 읽음
 */
export function getApiBase(): string {
  const primary = import.meta.env.VITE_API_BASE_URL as string | undefined;
  const legacy = import.meta.env.VITE_API_BASE as string | undefined;
  const raw = (primary ?? legacy ?? "").trim();
  return raw.replace(/\/+$/, "");
}
