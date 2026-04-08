/// <reference types="vite/client" />

interface ImportMetaEnv {
  /**
   * REST API 베이스(슬래시 없음). 예: https://api.example.com
   * 비우면 개발 시 Vite proxy로 `/api` 전달.
   */
  readonly VITE_API_BASE_URL?: string;
  /** @deprecated `VITE_API_BASE_URL` 사용 권장 */
  readonly VITE_API_BASE?: string;
  /** 예: https://api.example.com — POST /tts { text, voice } -> audio/mpeg */
  readonly VITE_TTS_API_URL?: string;
  /**
   * 개발 서버만: `vite` 프록시 대상 (기본 http://127.0.0.1:8000).
   * 배포 빌드에는 포함되지 않음.
   */
  readonly VITE_DEV_PROXY_TARGET?: string;
  /**
   * `false`일 때만 유료 UI(월별 블러, 포인트 가격) 표시.
   * 미설정·`true`면 잠금 해제(기본).
   */
  readonly VITE_UNLOCK_PREMIUM?: string;
}
