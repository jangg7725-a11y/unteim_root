import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type Dispatch,
  type ReactNode,
  type SetStateAction,
} from "react";
import type { BirthInputPayload } from "@/types/birthInput";
import type { CounselMessage } from "@/types/counsel";
import type { SajuReportData } from "@/types/report";
import {
  getSessionEmail,
  loginLocal,
  logoutLocal,
  registerLocal,
} from "@/services/localAuth";
import {
  clearUserMemory,
  getOrCreateUserId,
  loadUserMemory,
  saveUserMemory,
  type StoredCounselMessage,
} from "@/services/userMemoryStorage";
import { isStoredReportTimedOutWithoutMonthly, refreshReportDataCopy } from "@/services/reportApi";

type InitState = {
  userId: string;
  birth: BirthInputPayload | null;
  analysisSummary: string | null;
  reportData: SajuReportData | null;
  messages: CounselMessage[];
  hydrated: boolean;
  identityVerified: boolean;
  sessionEmail: string | null;
};

function getInitialSajuState(): InitState {
  if (typeof window === "undefined") {
    return {
      userId: "ssr",
      birth: null,
      analysisSummary: null,
      reportData: null,
      messages: [],
      hydrated: false,
      identityVerified: false,
      sessionEmail: null,
    };
  }
  const userId = getOrCreateUserId();
  const sessionFromAuth = getSessionEmail();
  const mem = loadUserMemory();
  /** 로그인 세션이 있으면 가입 이메일로 본인 연결된 것으로 봅니다(별도 버튼 불필요). */
  const verifiedFromLogin = Boolean(sessionFromAuth);
  if (mem && mem.userId === userId) {
    let reportData = refreshReportDataCopy(mem.reportData);
    if (isStoredReportTimedOutWithoutMonthly(reportData)) {
      reportData = null;
    }
    return {
      userId,
      birth: mem.birth,
      analysisSummary: mem.analysisSummary,
      reportData,
      messages: mem.recentMessages as CounselMessage[],
      hydrated: true,
      identityVerified: verifiedFromLogin || Boolean(mem.identityVerified),
      sessionEmail: mem.sessionEmail ?? sessionFromAuth,
    };
  }
  return {
    userId,
    birth: null,
    analysisSummary: null,
    reportData: null,
    messages: [],
    hydrated: true,
    identityVerified: verifiedFromLogin,
    sessionEmail: sessionFromAuth,
  };
}

type SajuSessionValue = {
  userId: string;
  memoryHydrated: boolean;
  birth: BirthInputPayload | null;
  setBirth: Dispatch<SetStateAction<BirthInputPayload | null>>;
  analysisSummary: string | null;
  setAnalysisSummary: Dispatch<SetStateAction<string | null>>;
  reportData: SajuReportData | null;
  setReportData: Dispatch<SetStateAction<SajuReportData | null>>;
  counselMessages: CounselMessage[];
  setCounselMessages: Dispatch<SetStateAction<CounselMessage[]>>;
  /** 로그인(로컬 데모) 이메일 */
  sessionEmail: string | null;
  /** 본인 인증 완료 — 탐색·카테고리에서 저장 사주로 바로 리포트 */
  identityVerified: boolean;
  setIdentityVerified: (v: boolean) => void;
  login: (identifier: string, password: string) => { ok: boolean; message?: string };
  register: (email: string, password: string, phone?: string) => { ok: boolean; message?: string };
  logout: () => void;
  /** 생년월일·시간·성별 + 로그인 + 본인인증 완료 시 탐색 주제 클릭 시 입력 없이 리포트로 */
  canUseSavedSajuContent: boolean;
  /** 사주·리포트·상담 기록을 비우고 새 사주를 입력할 수 있게 함(로그인 세션은 유지) */
  resetSajuMemory: () => void;
};

const SajuSessionContext = createContext<SajuSessionValue | null>(null);

export function SajuSessionProvider({ children }: { children: ReactNode }) {
  const initRef = useRef(getInitialSajuState());
  const [userId] = useState(initRef.current.userId);
  const [memoryHydrated, setMemoryHydrated] = useState(initRef.current.hydrated);
  const [birth, setBirth] = useState<BirthInputPayload | null>(initRef.current.birth);
  const [analysisSummary, setAnalysisSummary] = useState<string | null>(initRef.current.analysisSummary);
  const [reportData, setReportData] = useState<SajuReportData | null>(initRef.current.reportData);
  const [counselMessages, setCounselMessages] = useState<CounselMessage[]>(initRef.current.messages);
  const [identityVerified, setIdentityVerifiedState] = useState(initRef.current.identityVerified);
  const [sessionEmail, setSessionEmail] = useState<string | null>(initRef.current.sessionEmail);

  useEffect(() => {
    if (typeof window === "undefined") return;
    setMemoryHydrated(true);
  }, []);

  const setIdentityVerified = useCallback(
    (v: boolean) => {
      if (v && !sessionEmail) return;
      setIdentityVerifiedState(v);
    },
    [sessionEmail]
  );

  const login = useCallback((identifier: string, password: string) => {
    const r = loginLocal(identifier, password);
    if (r.ok) {
      setSessionEmail(getSessionEmail());
      setIdentityVerifiedState(true);
    }
    return r;
  }, []);

  const register = useCallback((email: string, password: string, phone?: string) => {
    const r = registerLocal(email, password, phone);
    if (r.ok) {
      setSessionEmail(getSessionEmail());
      setIdentityVerifiedState(true);
    }
    return r;
  }, []);

  const logout = useCallback(() => {
    logoutLocal();
    setSessionEmail(null);
    setIdentityVerifiedState(false);
  }, []);

  const resetSajuMemory = useCallback(() => {
    setBirth(null);
    setAnalysisSummary(null);
    setReportData(null);
    setCounselMessages([]);
    clearUserMemory();
  }, []);

  const persistTimer = useRef<number | null>(null);
  useEffect(() => {
    if (typeof window === "undefined" || !memoryHydrated) return;

    if (persistTimer.current) window.clearTimeout(persistTimer.current);
    persistTimer.current = window.setTimeout(() => {
      const recentMessages: StoredCounselMessage[] = counselMessages.map((m) => ({
        id: m.id,
        role: m.role,
        text: m.text,
        character: m.character,
        counselType: m.counselType,
      }));
      saveUserMemory({
        userId,
        birth,
        analysisSummary,
        reportData,
        recentMessages,
        sessionEmail,
        identityVerified,
      });
    }, 450);

    return () => {
      if (persistTimer.current) window.clearTimeout(persistTimer.current);
    };
  }, [userId, birth, analysisSummary, reportData, counselMessages, memoryHydrated, sessionEmail, identityVerified]);

  const canUseSavedSajuContent = useMemo(() => {
    const b = birth;
    return Boolean(
      b?.date && b?.time && b?.gender && identityVerified && sessionEmail
    );
  }, [birth, identityVerified, sessionEmail]);

  const value = useMemo(
    () => ({
      userId,
      memoryHydrated,
      birth,
      setBirth,
      analysisSummary,
      setAnalysisSummary,
      reportData,
      setReportData,
      counselMessages,
      setCounselMessages,
      sessionEmail,
      identityVerified,
      setIdentityVerified,
      login,
      register,
      logout,
      canUseSavedSajuContent,
      resetSajuMemory,
    }),
    [
      userId,
      memoryHydrated,
      birth,
      analysisSummary,
      reportData,
      counselMessages,
      sessionEmail,
      identityVerified,
      setIdentityVerified,
      login,
      register,
      logout,
      canUseSavedSajuContent,
      resetSajuMemory,
    ]
  );

  return <SajuSessionContext.Provider value={value}>{children}</SajuSessionContext.Provider>;
}

export function useSajuSession(): SajuSessionValue {
  const ctx = useContext(SajuSessionContext);
  if (!ctx) {
    throw new Error("useSajuSession must be used within SajuSessionProvider");
  }
  return ctx;
}
