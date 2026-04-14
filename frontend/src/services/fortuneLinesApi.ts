import type { FortuneLinesData } from "@/types/fortuneLines";

const EMPTY: FortuneLinesData = {
  version: 0,
  byCategory: {},
};

/**
 * `public/data/fortune_lines.json` — `scripts/build_fortune_lines.py`로 생성합니다.
 */
export async function loadFortuneLines(): Promise<FortuneLinesData> {
  const base = import.meta.env.BASE_URL || "/";
  const root = base.endsWith("/") ? base : `${base}/`;
  const url = `${root}data/fortune_lines.json`;
  try {
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) return EMPTY;
    const data = (await res.json()) as FortuneLinesData;
    if (!data?.byCategory || typeof data.byCategory !== "object") return EMPTY;
    return data;
  } catch {
    return EMPTY;
  }
}
