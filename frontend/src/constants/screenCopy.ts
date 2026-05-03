/**
 * 화면별 콘셉트 카피 — 이미지/레이아웃 작업 시 동일 상수 재사용
 *
 * 연결 위치:
 * - home: 랜딩/스플래시 또는 App 첫 화면
 * - input: SajuInputScreen (사주 입력)
 * - output: 리포트·PDF 뷰어 등 결과 화면
 * - aiCounsel: CounselCorner (AI 상담 코너)
 */

export const SCREEN_COPY = {
  home: {
    title: "당신의 흐름을 읽고, 오늘을 안내합니다",
    subtitle: "사주·타로·감정까지, 지금 당신에게 필요한 단 하나의 방향",
  },
  input: {
    title: "당신의 시간을 들려주세요",
    subtitle: "태어난 순간의 흐름이, 지금의 방향을 알려줍니다",
  },
  output: {
    /** 리포트 상단 메인 헤더(한 줄) */
    subtitle: "이해하고, 준비하면 운은 기회가 됩니다",
  },
  aiCounsel: {
    title: "혼자가 아닙니다, 제가 함께 볼게요",
    subtitle: "궁금한 마음, 이해되지 않는 흐름까지 편하게 물어보세요",
  },
} as const;

export type ScreenCopyKey = keyof typeof SCREEN_COPY;
