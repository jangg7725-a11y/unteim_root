/**
 * 사용자 기억 — localStorage (확장 시 동일 스키마로 API/DB 이전 가능)
 * optional backend: 동일 payload를 POST /api/user/profile 등으로 동기화할 수 있음.
 */

import type { BirthInputPayload } from "@/types/birthInput";
import type { CounselCharacterId, CounselTypeHint } from "@/types/counsel";
import type { SajuReportData } from "@/types/report";

const STORAGE_USER_ID = "unteim_user_id_v1";
const STORAGE_MEMORY = "unteim_user_memory_v1";

export const USER_MEMORY_VERSION = 1 as const;

export type StoredCounselMessage = {
  id: string;
  role: "user" | "assistant";
  text: string;
  character?: CounselCharacterId;
  counselType?: CounselTypeHint;
};

export type UserMemoryPayload = {
  version: typeof USER_MEMORY_VERSION;
  userId: string;
  birth: BirthInputPayload | null;
  analysisSummary: string | null;
  reportData?: SajuReportData | null;
  recentMessages: StoredCounselMessage[];
  /** 로그인된 계정 이메일(로컬 데모) */
  sessionEmail?: string | null;
  /** 로그인 후 본인 인증 완료 시 탐색 등에서 저장 사주로 바로 이용 */
  identityVerified?: boolean;
};

const MAX_STORED_MESSAGES = 40;

function safeJsonParse<T>(raw: string | null): T | null {
  if (!raw) return null;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

export function getOrCreateUserId(): string {
  if (typeof window === "undefined" || !window.localStorage) {
    return "ssr-anon";
  }
  let id = window.localStorage.getItem(STORAGE_USER_ID);
  if (!id || id.length < 8) {
    id = typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : `u-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
    window.localStorage.setItem(STORAGE_USER_ID, id);
  }
  return id;
}

export function loadUserMemory(): UserMemoryPayload | null {
  if (typeof window === "undefined" || !window.localStorage) return null;
  const raw = window.localStorage.getItem(STORAGE_MEMORY);
  const parsed = safeJsonParse<UserMemoryPayload>(raw);
  if (!parsed || parsed.version !== USER_MEMORY_VERSION) return null;
  if (!parsed.userId || !Array.isArray(parsed.recentMessages)) return null;
  return {
    ...parsed,
    recentMessages: parsed.recentMessages.slice(-MAX_STORED_MESSAGES),
  };
}

export function saveUserMemory(payload: Omit<UserMemoryPayload, "version" | "userId"> & { userId: string }): void {
  if (typeof window === "undefined" || !window.localStorage) return;
  const data: UserMemoryPayload = {
    version: USER_MEMORY_VERSION,
    userId: payload.userId,
    birth: payload.birth,
    analysisSummary: payload.analysisSummary,
    reportData: payload.reportData ?? null,
    recentMessages: payload.recentMessages.slice(-MAX_STORED_MESSAGES),
    sessionEmail: payload.sessionEmail ?? null,
    identityVerified: payload.identityVerified ?? false,
  };
  try {
    window.localStorage.setItem(STORAGE_MEMORY, JSON.stringify(data));
  } catch {
    /* quota */
  }
}

export function clearUserMemory(): void {
  if (typeof window === "undefined" || !window.localStorage) return;
  window.localStorage.removeItem(STORAGE_MEMORY);
}

/** 앱 첫 탭: 저장된 생년 정보가 있으면 리포트 탭 우선 */
export function hasStoredBirth(): boolean {
  const m = loadUserMemory();
  return Boolean(m?.birth?.date && m?.birth?.time && m?.birth?.gender);
}
