import type { BirthInputPayload } from "@/types/birthInput";
import { getApiBase } from "./apiBase";

export type SoloLoveInsightTopic = "general" | "sseom" | "timing" | "emotion";

export type SoloLoveInsightResult = {
  summary: string;
  pullsIn: string;
  likelyBond: string;
  energy: string;
  balanceNote: string;
  monthlyFlow: string;
  topicNote: string;
  disclaimer: string;
  topic: string;
  meta?: Record<string, unknown>;
};

const TIMEOUT_MS = 90_000;

export async function postSoloLoveInsight(
  birth: BirthInputPayload,
  topic: SoloLoveInsightTopic = "general",
): Promise<SoloLoveInsightResult> {
  const base = getApiBase();
  const url = base ? `${base}/api/solo-love-insight` : "/api/solo-love-insight";
  const ctrl = new AbortController();
  const tid = window.setTimeout(() => ctrl.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        date: birth.date,
        time: birth.time,
        gender: birth.gender,
        calendarApi: birth.calendarApi,
        topic,
      }),
      signal: ctrl.signal,
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
          : raw || "인연 해석 요청 중 오류가 발생했습니다.";
      throw new Error(detail);
    }
    if (!j || typeof j !== "object") throw new Error("응답 형식이 올바르지 않습니다.");
    return j as SoloLoveInsightResult;
  } catch (e) {
    if (e instanceof Error && e.name === "AbortError") {
      throw new Error("요청 시간이 초과되었습니다. API 서버 상태를 확인해 주세요.");
    }
    throw e;
  } finally {
    window.clearTimeout(tid);
  }
}
