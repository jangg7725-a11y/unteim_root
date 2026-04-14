/**
 * 엔진 `compatibility_analyzer._score_to_star` 와 동일한 구간.
 * 카피는 단정·의료·법률 효력을 암시하지 않도록 경향·참고 수준으로 유지합니다.
 */
export function starBandFrom100(score100: number): {
  star: 1 | 2 | 3 | 4 | 5;
  /** 짧은 해석 라벨 (UI용) */
  hint: string;
} {
  const s = Number(score100);
  if (!Number.isFinite(s)) {
    return { star: 3, hint: "참고 구간" };
  }
  if (s >= 85) return { star: 5, hint: "상단 구간에 가깝게 해석될 수 있음" };
  if (s >= 70) return { star: 4, hint: "우수에 가까운 구간으로 해석될 수 있음" };
  if (s >= 55) return { star: 3, hint: "중간~양호에 가까운 구간으로 해석될 수 있음" };
  if (s >= 40) return { star: 2, hint: "보완·조율이 도움이 될 수 있는 구간" };
  return { star: 1, hint: "신중한 조율이 도움이 될 수 있는 구간" };
}

export const COMPAT_SCORE_LEGEND_LINES = [
  "85~100점 → 별 5 / 70~84점 → 별 4 / 55~69점 → 별 3 / 40~54점 → 별 2 / 39점 이하 → 별 1",
] as const;
