import type { BirthInputPayload } from "@/types/birthInput";
import type {
  CounselCharacterId,
  CounselSessionCardPayload,
  CounselTypeHint,
} from "@/types/counsel";
import { getApiBase } from "./apiBase";

export type CounselApiMessage = {
  role: "user" | "assistant";
  text: string;
};

export type CounselApiRequest = BirthInputPayload & {
  name?: string;
  messages: CounselApiMessage[];
  /** 클라이언트 캐시(선택). 서버는 엔진 재계산 요약을 우선한다. */
  analysisSummary?: string;
};

/** 서버 `infer_counsel_intent` 결과 */
export type CounselIntent =
  | "personality"
  | "wealth"
  | "work"
  | "relationship"
  | "health"
  | "exam"
  | "general";

export type CounselApiResponse = {
  reply: string;
  analysisSummary: string;
  counselType: CounselTypeHint;
  character: CounselCharacterId;
  counselIntent?: CounselIntent;
  /** 상담 직후 요약 카드 — 서버 미지원 시 생략 */
  sessionCard?: CounselSessionCardPayload;
};

function parseSessionCard(raw: unknown): CounselSessionCardPayload | undefined {
  if (!raw || typeof raw !== "object") return undefined;
  const o = raw as Record<string, unknown>;
  const flow = typeof o.flow === "string" ? o.flow.trim() : "";
  if (!flow) return undefined;
  const cautions = typeof o.cautions === "string" ? o.cautions.trim() : "";
  const actions: string[] = [];
  if (Array.isArray(o.actions)) {
    for (const a of o.actions) {
      if (typeof a === "string" && a.trim()) actions.push(a.trim());
      if (actions.length >= 2) break;
    }
  }
  return {
    flow,
    cautions:
      cautions ||
      "세부 판단은 본문을 함께 참고하고, 건강·법률·투자는 전문가 확인이 안전합니다.",
    actions:
      actions.length > 0
        ? actions
        : ["한 가지 작은 실천부터 시도해 보기", "무리하지 않고 휴식·루틴 점검하기"],
  };
}

const API_BASE = getApiBase();

function parseErrorDetail(body: unknown): string {
  if (body && typeof body === "object" && "detail" in body) {
    const d = (body as { detail: unknown }).detail;
    if (typeof d === "string") return d;
    if (Array.isArray(d)) {
      return d.map((x) => (typeof x === "object" && x && "msg" in x ? String((x as { msg: string }).msg) : String(x))).join("; ");
    }
  }
  return "요청 처리 중 오류가 발생했습니다.";
}

export async function postCounsel(body: CounselApiRequest): Promise<CounselApiResponse> {
  const res = await fetch(`${API_BASE}/api/counsel`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  const raw = await res.text();
  let json: unknown = null;
  try {
    json = raw ? JSON.parse(raw) : null;
  } catch {
    json = null;
  }

  if (!res.ok) {
    const msg = json ? parseErrorDetail(json) : raw || res.statusText;
    throw new Error(msg);
  }

  if (!json || typeof json !== "object") {
    throw new Error("서버 응답 형식이 올바르지 않습니다.");
  }

  const j = json as Record<string, unknown>;
  const reply = j.reply;
  const analysisSummary = j.analysisSummary;
  if (typeof reply !== "string" || typeof analysisSummary !== "string") {
    throw new Error("서버 응답에 reply/analysisSummary가 없습니다.");
  }

  const counselType = j.counselType === "emotion" ? "emotion" : "analysis";
  const character = j.character === "unsuni" ? "unsuni" : "undol";

  const intents: CounselIntent[] = [
    "personality",
    "wealth",
    "work",
    "relationship",
    "health",
    "exam",
    "general",
  ];
  const rawIntent = j.counselIntent;
  const counselIntent =
    typeof rawIntent === "string" && intents.includes(rawIntent as CounselIntent)
      ? (rawIntent as CounselIntent)
      : undefined;

  const sessionCard = parseSessionCard(j.sessionCard);

  return {
    reply,
    analysisSummary,
    counselType,
    character,
    counselIntent,
    ...(sessionCard ? { sessionCard } : {}),
  };
}
