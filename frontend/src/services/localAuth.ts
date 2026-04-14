/**
 * 로컬 전용 계정(데모) — 실서비스 시 서버 OAuth/세션으로 교체하세요.
 * 비밀번호는 평문 저장이므로 개발·내부 확인용입니다.
 */
const ACCOUNTS_KEY_V1 = "unteim_local_accounts_v1";
const ACCOUNTS_KEY = "unteim_local_accounts_v2";
const PHONE_INDEX_KEY = "unteim_phone_to_email_v1";
const SESSION_KEY = "unteim_session_email_v1";

export type LocalAccount = {
  password: string;
  /** 정규화된 숫자만 (예: 01012345678) */
  phone?: string;
};

type AccountMap = Record<string, LocalAccount>;
type PhoneIndex = Record<string, string>;

function readJson<T>(key: string, fallback: T): T {
  if (typeof window === "undefined" || !window.localStorage) return fallback;
  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) return fallback;
    const o = JSON.parse(raw) as T;
    return o && typeof o === "object" ? o : fallback;
  } catch {
    return fallback;
  }
}

function writeJson(key: string, val: unknown): void {
  if (typeof window === "undefined" || !window.localStorage) return;
  try {
    window.localStorage.setItem(key, JSON.stringify(val));
  } catch {
    /* quota */
  }
}

/** 한국 휴대폰 번호: 숫자 10~11자리, 0으로 시작 */
export function normalizePhone(raw: string): string | null {
  const d = (raw || "").replace(/\D/g, "");
  if (d.length < 10 || d.length > 11) return null;
  if (!d.startsWith("0")) return null;
  return d;
}

function readAccounts(): AccountMap {
  let acc = readJson<AccountMap>(ACCOUNTS_KEY, {});
  if (Object.keys(acc).length === 0) {
    const legacy = readJson<Record<string, { password: string }>>(ACCOUNTS_KEY_V1, {});
    if (Object.keys(legacy).length > 0) {
      acc = {};
      for (const [email, row] of Object.entries(legacy)) {
        acc[email.toLowerCase()] = { password: row.password };
      }
      writeJson(ACCOUNTS_KEY, acc);
    }
  }
  return acc;
}

function readPhoneIndex(): PhoneIndex {
  return readJson<PhoneIndex>(PHONE_INDEX_KEY, {});
}

function writePhoneIndex(m: PhoneIndex): void {
  writeJson(PHONE_INDEX_KEY, m);
}

function writeAccounts(m: AccountMap): void {
  writeJson(ACCOUNTS_KEY, m);
}

function setSessionEmail(email: string): void {
  window.localStorage.setItem(SESSION_KEY, email);
}

/**
 * 회원가입 — 이메일·비밀번호 필수, 휴대폰은 로그인 편의용(중복 불가)
 */
export function registerLocal(
  email: string,
  password: string,
  phoneRaw?: string,
): { ok: boolean; message?: string } {
  const e = email.trim().toLowerCase();
  if (!e.includes("@") || password.length < 4) {
    return { ok: false, message: "이메일 형식과 비밀번호(4자 이상)를 확인해 주세요." };
  }
  const phone = phoneRaw?.trim() ? normalizePhone(phoneRaw) : null;
  if (phoneRaw?.trim() && !phone) {
    return { ok: false, message: "휴대폰 번호를 확인해 주세요. (예: 01012345678)" };
  }

  const acc = readAccounts();
  if (acc[e]) {
    return { ok: false, message: "이미 가입된 이메일입니다. 로그인해 주세요." };
  }

  const idx = readPhoneIndex();
  if (phone) {
    const existing = idx[phone];
    if (existing && existing !== e) {
      return { ok: false, message: "이 휴대폰 번호는 다른 계정에 등록되어 있습니다." };
    }
  }

  acc[e] = { password, ...(phone ? { phone } : {}) };
  writeAccounts(acc);
  if (phone) {
    idx[phone] = e;
    writePhoneIndex(idx);
  }
  setSessionEmail(e);
  return { ok: true };
}

/**
 * 로그인 — 이메일 또는 휴대폰 번호 + 비밀번호
 */
export function loginLocal(
  identifier: string,
  password: string,
): { ok: boolean; message?: string } {
  const id = identifier.trim();
  if (!id || password.length < 1) {
    return { ok: false, message: "아이디와 비밀번호를 입력해 주세요." };
  }

  let email: string;
  if (id.includes("@")) {
    email = id.toLowerCase();
  } else {
    const phone = normalizePhone(id);
    if (!phone) {
      return { ok: false, message: "휴대폰 번호 형식을 확인해 주세요. (예: 01012345678)" };
    }
    const idx = readPhoneIndex();
    const mapped = idx[phone];
    if (!mapped) {
      return { ok: false, message: "등록된 휴대폰 번호가 없습니다. 이메일로 가입했는지 확인해 주세요." };
    }
    email = mapped;
  }

  const acc = readAccounts();
  const row = acc[email];
  if (!row || row.password !== password) {
    return { ok: false, message: "이메일·휴대폰 또는 비밀번호가 올바르지 않습니다." };
  }
  setSessionEmail(email);
  return { ok: true };
}

export function logoutLocal(): void {
  if (typeof window === "undefined" || !window.localStorage) return;
  window.localStorage.removeItem(SESSION_KEY);
}

export function getSessionEmail(): string | null {
  if (typeof window === "undefined" || !window.localStorage) return null;
  const s = window.localStorage.getItem(SESSION_KEY);
  return s && s.includes("@") ? s : null;
}

/** 드로어 등 표시용 — 마스킹 */
export function getMaskedPhoneForEmail(email: string): string | null {
  const e = email.trim().toLowerCase();
  const acc = readAccounts()[e];
  const p = acc?.phone;
  if (!p || p.length < 8) return null;
  return `${p.slice(0, 3)}-****-${p.slice(-4)}`;
}
