/**
 * TTS 생성 · 캐싱 · 긴 텍스트 분할
 * - 서버: VITE_TTS_API_URL POST { text, voice } -> audio/mpeg
 * - 없으면 VoicePlayer가 브라우저 speechSynthesis 폴백 (자동 재생 없음)
 */

import { createHash } from "./ttsHash";

export type VoiceId = "undol" | "unsuni";

export interface GenerateTtsOptions {
  voice?: VoiceId;
  playbackRate?: number;
}

export interface TtsSegment {
  text: string;
  blob: Blob;
  url: string;
}

export type TtsGenerateResult =
  | { mode: "audio"; segments: TtsSegment[]; revokeAll: () => void }
  | { mode: "browser"; text: string; voice: VoiceId };

const MAX_CHUNK = 380;
const CACHE_MAX = 48;

type CacheEntry = { result: TtsGenerateResult; at: number };
const cache = new Map<string, CacheEntry>();

function cacheKey(text: string, voice: VoiceId): string {
  return `${voice}::${createHash(text)}`;
}

function evictIfNeeded(): void {
  if (cache.size <= CACHE_MAX) return;
  const oldest = [...cache.entries()].sort((a, b) => a[1].at - b[1].at)[0];
  if (oldest) {
    const [, entry] = oldest;
    if (entry.result.mode === "audio") entry.result.revokeAll();
    cache.delete(oldest[0]);
  }
}

export function splitTextForTts(text: string): string[] {
  const t = text.trim();
  if (t.length <= MAX_CHUNK) return [t];
  const parts: string[] = [];
  let rest = t;
  while (rest.length > MAX_CHUNK) {
    let cut = rest.lastIndexOf("。", MAX_CHUNK);
    if (cut < MAX_CHUNK / 2) cut = rest.lastIndexOf(".", MAX_CHUNK);
    if (cut < MAX_CHUNK / 2) cut = rest.lastIndexOf(" ", MAX_CHUNK);
    if (cut < MAX_CHUNK / 2) cut = rest.lastIndexOf("\n", MAX_CHUNK);
    if (cut < MAX_CHUNK / 2) cut = MAX_CHUNK;
    parts.push(rest.slice(0, cut).trim());
    rest = rest.slice(cut).trim();
  }
  if (rest) parts.push(rest);
  return parts.filter(Boolean);
}

async function fetchTtsBlob(text: string, voice: VoiceId): Promise<Blob> {
  const base = import.meta.env.VITE_TTS_API_URL as string | undefined;
  if (!base) throw new Error("TTS_API_UNAVAILABLE");
  const url = base.replace(/\/$/, "") + "/tts";
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, voice }),
  });
  if (!res.ok) throw new Error(`TTS_HTTP_${res.status}`);
  return res.blob();
}

function blobToUrl(blob: Blob): { url: string; revoke: () => void } {
  const url = URL.createObjectURL(blob);
  return {
    url,
    revoke: () => URL.revokeObjectURL(url),
  };
}

export async function generateTts(
  text: string,
  options: GenerateTtsOptions = {}
): Promise<TtsGenerateResult> {
  const voice: VoiceId = options.voice ?? "undol";
  const key = cacheKey(text, voice);
  const hit = cache.get(key);
  if (hit) {
    hit.at = Date.now();
    return hit.result;
  }

  evictIfNeeded();

  const chunks = splitTextForTts(text);
  try {
    const blobs = await Promise.all(chunks.map((c) => fetchTtsBlob(c, voice)));
    const revokers: (() => void)[] = [];
    const segments: TtsSegment[] = blobs.map((blob, i) => {
      const { url, revoke } = blobToUrl(blob);
      revokers.push(revoke);
      return { text: chunks[i]!, blob, url };
    });
    const result: TtsGenerateResult = {
      mode: "audio",
      segments,
      revokeAll: () => {
        revokers.forEach((r) => r());
      },
    };
    cache.set(key, { result, at: Date.now() });
    return result;
  } catch {
    const result: TtsGenerateResult = {
      mode: "browser",
      text,
      voice,
    };
    cache.set(key, { result, at: Date.now() });
    return result;
  }
}

export function peekTtsCache(text: string, voice: VoiceId): TtsGenerateResult | undefined {
  return cache.get(cacheKey(text, voice))?.result;
}
