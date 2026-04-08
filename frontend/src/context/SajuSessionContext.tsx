import {
  createContext,
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
  getOrCreateUserId,
  loadUserMemory,
  saveUserMemory,
  type StoredCounselMessage,
} from "@/services/userMemoryStorage";

function getInitialSajuState() {
  if (typeof window === "undefined") {
    return {
      userId: "ssr",
      birth: null as BirthInputPayload | null,
      analysisSummary: null as string | null,
      reportData: null as SajuReportData | null,
      messages: [] as CounselMessage[],
      hydrated: false,
    };
  }
  const userId = getOrCreateUserId();
  const mem = loadUserMemory();
  if (mem && mem.userId === userId) {
    return {
      userId,
      birth: mem.birth,
      analysisSummary: mem.analysisSummary,
      reportData: mem.reportData ?? null,
      messages: mem.recentMessages as CounselMessage[],
      hydrated: true,
    };
  }
  return {
    userId,
    birth: null,
    analysisSummary: null,
    reportData: null,
    messages: [],
    hydrated: true,
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

  useEffect(() => {
    if (typeof window === "undefined") return;
    setMemoryHydrated(true);
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
      });
    }, 450);

    return () => {
      if (persistTimer.current) window.clearTimeout(persistTimer.current);
    };
  }, [userId, birth, analysisSummary, reportData, counselMessages, memoryHydrated]);

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
    }),
    [userId, memoryHydrated, birth, analysisSummary, reportData, counselMessages]
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
