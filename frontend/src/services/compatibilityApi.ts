import type { BirthInputPayload } from "@/types/birthInput";
import { getApiBase } from "./apiBase";

export type CompatibilityResult = {
  score: 1 | 2 | 3 | 4 | 5;
  score100?: number;
  summary: string;
  attraction: string;
  conflict: string;
  longevity: string;
  reality: {
    emotion: string;
    money: string;
    lifestyle: string;
  };
  guide: string;
};

type PersonPayload = {
  date: string;
  time: string;
  gender: "male" | "female";
  calendarApi: "solar" | "lunar" | "lunar_leap";
};

export async function postCompatibility(
  birth1: BirthInputPayload,
  birth2: BirthInputPayload
): Promise<CompatibilityResult> {
  const base = getApiBase();
  const url = base ? `${base}/api/compatibility` : "/api/compatibility";
  const p1: PersonPayload = {
    date: birth1.date,
    time: birth1.time,
    gender: birth1.gender,
    calendarApi: birth1.calendarApi,
  };
  const p2: PersonPayload = {
    date: birth2.date,
    time: birth2.time,
    gender: birth2.gender,
    calendarApi: birth2.calendarApi,
  };

  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ birth1: p1, birth2: p2 }),
  });

  const raw = await res.text();
  let j: unknown = null;
  try {
    j = raw ? JSON.parse(raw) : null;
  } catch {
    j = null;
  }
  if (!res.ok) {
    const detail =
      typeof j === "object" && j && "detail" in j
        ? String((j as { detail: unknown }).detail)
        : raw || "궁합 분석 중 오류가 발생했습니다.";
    throw new Error(detail);
  }
  if (!j || typeof j !== "object") throw new Error("궁합 응답 형식이 올바르지 않습니다.");
  return j as CompatibilityResult;
}

