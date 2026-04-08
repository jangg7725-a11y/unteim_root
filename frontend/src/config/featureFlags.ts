/**
 * 유료/프리미엄 UI(월별 블러, 소액 포인트 가격 표시 등).
 * 기본: 잠금 해제(개발·내부 테스트). 상용 유료 배포 시 `.env.production`에
 * `VITE_UNLOCK_PREMIUM=false` 를 넣어 잠금을 켭니다.
 */
export const UNLOCK_PREMIUM_CONTENT = import.meta.env.VITE_UNLOCK_PREMIUM !== "false";
