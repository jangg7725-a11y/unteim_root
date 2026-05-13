import { useEffect, useState } from "react";
import type { BirthInputPayload } from "@/types/birthInput";
import type { SajuReportData } from "@/types/report";
import { formatDualCalendarBirthLine } from "@/utils/calendarDualLabel";
import { getApiBase } from "@/services/apiBase";

type Props = {
  birth: BirthInputPayload | null;
  report: SajuReportData | null;
};

type PillarKey = "hour" | "day" | "month" | "year";

const STEM_META: Record<string, { element: string; sign: "+" | "-" }> = {
  甲: { element: "목", sign: "+" },
  乙: { element: "목", sign: "-" },
  丙: { element: "화", sign: "+" },
  丁: { element: "화", sign: "-" },
  戊: { element: "토", sign: "+" },
  己: { element: "토", sign: "-" },
  庚: { element: "금", sign: "+" },
  辛: { element: "금", sign: "-" },
  壬: { element: "수", sign: "+" },
  癸: { element: "수", sign: "-" },
};

const BRANCH_META: Record<string, { element: string; sign: "+" | "-"; hidden: string[] }> = {
  子: { element: "수", sign: "+", hidden: ["癸"] },
  丑: { element: "토", sign: "-", hidden: ["己", "癸", "辛"] },
  寅: { element: "목", sign: "+", hidden: ["甲", "丙", "戊"] },
  卯: { element: "목", sign: "-", hidden: ["乙"] },
  辰: { element: "토", sign: "+", hidden: ["戊", "乙", "癸"] },
  巳: { element: "화", sign: "-", hidden: ["丙", "庚", "戊"] },
  午: { element: "화", sign: "+", hidden: ["丁", "己"] },
  未: { element: "토", sign: "-", hidden: ["己", "丁", "乙"] },
  申: { element: "금", sign: "+", hidden: ["庚", "壬", "戊"] },
  酉: { element: "금", sign: "-", hidden: ["辛"] },
  戌: { element: "토", sign: "+", hidden: ["戊", "辛", "丁"] },
  亥: { element: "수", sign: "-", hidden: ["壬", "甲"] },
};

const STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"];
const BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"];

/** 12운성: 한자·변형 표기 → 한글 표준명 */
const TWELVE_STAGE_TO_HANGUL: Record<string, string> = {
  장생: "장생",
  목욕: "목욕",
  관대: "관대",
  임관: "임관",
  제왕: "제왕",
  쇠: "쇠",
  병: "병",
  사: "사",
  묘: "묘",
  절: "절",
  태: "태",
  양: "양",
  长生: "장생",
  沐浴: "목욕",
  冠带: "관대",
  臨官: "임관",
  临官: "임관",
  帝旺: "제왕",
  衰: "쇠",
  病: "병",
  死: "사",
  墓: "묘",
  绝: "절",
  絕: "절",
  胎: "태",
  养: "양",
  養: "양",
};

const KO_TWELVE_STAGES = new Set([
  "장생",
  "목욕",
  "관대",
  "임관",
  "제왕",
  "쇠",
  "병",
  "사",
  "묘",
  "절",
  "태",
  "양",
]);

function formatTwelveStage(raw: string): string {
  let s = String(raw ?? "").trim();
  if (!s || s === "—") return "—";
  s = s.replace(/^12운성[:：]?\s*/i, "").trim();
  if (!s) return "—";
  if (KO_TWELVE_STAGES.has(s)) return s;
  if (TWELVE_STAGE_TO_HANGUL[s]) return TWELVE_STAGE_TO_HANGUL[s];
  const parts = s.split(/[\s·/]+/).filter(Boolean);
  if (parts.length > 1) {
    return parts.map((p) => formatTwelveStage(p)).join(" · ");
  }
  return s;
}

function asRecord(v: unknown): Record<string, unknown> | null {
  return v && typeof v === "object" ? (v as Record<string, unknown>) : null;
}

function flattenTexts(v: unknown): string[] {
  if (typeof v === "string") return v.trim() ? [v.trim()] : [];
  if (Array.isArray(v)) return v.flatMap((x) => flattenTexts(x));
  const o = asRecord(v);
  if (!o) return [];
  return Object.values(o).flatMap((x) => flattenTexts(x));
}

function pickFirst(v: unknown, fallback = "—"): string {
  const arr = flattenTexts(v).filter(Boolean);
  return arr.length ? arr.slice(0, 6).join(" · ") : fallback;
}

function tenGod(dayStem: string, targetStem: string): string {
  const d = STEM_META[dayStem];
  const t = STEM_META[targetStem];
  if (!d || !t) return "—";
  const cycle = ["목", "화", "토", "금", "수"];
  const di = cycle.indexOf(d.element);
  const ti = cycle.indexOf(t.element);
  if (di < 0 || ti < 0) return "—";
  if (di === ti) return d.sign === t.sign ? "비견" : "겁재";
  if ((di + 1) % 5 === ti) return d.sign === t.sign ? "식신" : "상관";
  if ((di + 2) % 5 === ti) return d.sign === t.sign ? "편재" : "정재";
  if ((di + 3) % 5 === ti) return d.sign === t.sign ? "편관" : "정관";
  return d.sign === t.sign ? "편인" : "정인";
}

function voidByPillar(stem: string, branch: string): string {
  const idx = Array.from({ length: 60 }).findIndex((_, i) => STEMS[i % 10] === stem && BRANCHES[i % 12] === branch);
  if (idx < 0) return "—";
  const g = Math.floor(idx / 10);
  const groups = ["戌亥", "申酉", "午未", "辰巳", "寅卯", "子丑"];
  return groups[g] ?? "—";
}

function pickSipsin(raw: Record<string, unknown>): string {
  const analysis = asRecord(raw.analysis) ?? {};
  const sibsin = asRecord(raw.sibsin) ?? asRecord(analysis.sipsin) ?? {};
  return pickFirst((asRecord(sibsin.summary) ?? sibsin).dominant ?? sibsin.summary ?? sibsin);
}

function getPillars(raw: Record<string, unknown>) {
  const p = asRecord(raw.pillars) ?? {};
  return {
    year: asRecord(p.year),
    month: asRecord(p.month),
    day: asRecord(p.day),
    hour: asRecord(p.hour),
  };
}

function byWhereShinsal(raw: Record<string, unknown>, where: PillarKey): string[] {
  const items = (asRecord(asRecord(raw.analysis)?.shinsal)?.items as unknown[]) ?? [];
  const out = items
    .filter((x) => asRecord(x)?.where === where)
    .map((x) => String(asRecord(x)?.name ?? "").trim())
    .filter(Boolean)
    // 12운성은 별도 섹션에서 다루므로 '12운성:' 접두만 제외
    .filter((n) => !n.startsWith("12운성:"));
  return Array.from(new Set(out)).slice(0, 8);
}

function byWhereTwelve(raw: Record<string, unknown>, where: PillarKey): string {
  const tf = asRecord(asRecord(raw.analysis)?.twelve_fortunes)?.[where];
  const o = asRecord(tf);
  return String(o?.fortune ?? "").trim() || "—";
}

function getOhaengCounts(raw: Record<string, unknown>): Record<string, number> {
  const oheng = asRecord(raw.oheng) ?? asRecord(asRecord(raw.analysis)?.oheng) ?? {};
  const c = asRecord(oheng.counts) ?? oheng;
  const out: Record<string, number> = {};
  for (const [k, v] of Object.entries(c)) {
    if (typeof v === "number") out[k] = v;
  }
  return out;
}

function getLocalOhaengCountsFromPillars(p: {
  year: Record<string, unknown> | null;
  month: Record<string, unknown> | null;
  day: Record<string, unknown> | null;
  hour: Record<string, unknown> | null;
}): Record<string, number> {
  const out: Record<string, number> = { 목: 0, 화: 0, 토: 0, 금: 0, 수: 0 };
  const ks: Array<"year" | "month" | "day" | "hour"> = ["year", "month", "day", "hour"];
  for (const k of ks) {
    const blk = p[k];
    const gan = String(blk?.gan ?? "").trim();
    const ji = String(blk?.ji ?? "").trim();
    const ge = STEM_META[gan]?.element;
    const je = BRANCH_META[ji]?.element;
    if (ge && ge in out) out[ge] += 1;
    if (je && je in out) out[je] += 1;
  }
  return out;
}

function isAllZeroCounts(c: Record<string, number>): boolean {
  const keys = Object.keys(c);
  if (!keys.length) return true;
  return keys.every((k) => Number(c[k] ?? 0) === 0);
}

function localTwelveByWhereFromPillars(p: {
  year: Record<string, unknown> | null;
  month: Record<string, unknown> | null;
  day: Record<string, unknown> | null;
  hour: Record<string, unknown> | null;
}): Record<string, string> {
  const dayStem = String(p.day?.gan ?? "").trim();
  const mapStart: Record<string, string> = {
    甲: "亥", 乙: "午", 丙: "寅", 丁: "酉", 戊: "寅",
    己: "酉", 庚: "巳", 辛: "子", 壬: "申", 癸: "卯",
  };
  const fortunes = ["長生", "沐浴", "冠帶", "臨官", "帝旺", "衰", "病", "死", "墓", "絕", "胎", "養"];
  const branches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"];
  const start = mapStart[dayStem];
  if (!start) return { year: "—", month: "—", day: "—", hour: "—" };
  const sidx = branches.indexOf(start);
  if (sidx < 0) return { year: "—", month: "—", day: "—", hour: "—" };
  const yang = new Set(["甲", "丙", "戊", "庚", "壬"]);
  const table: Record<string, string> = {};
  for (let i = 0; i < fortunes.length; i += 1) {
    const idx = (sidx + (yang.has(dayStem) ? i : -i) + 120) % 12;
    table[branches[idx]] = fortunes[i];
  }
  const pick = (key: "year" | "month" | "day" | "hour") => {
    const br = String(p[key]?.ji ?? "").trim();
    return table[br] ?? "—";
  };
  return { year: pick("year"), month: pick("month"), day: pick("day"), hour: pick("hour") };
}

function OhaengChips({ counts }: { counts: Record<string, number> }) {
  const items: Array<{ key: string; label: string; cls: string }> = [
    { key: "목", label: "목", cls: "wood" },
    { key: "화", label: "화", cls: "fire" },
    { key: "토", label: "토", cls: "earth" },
    { key: "금", label: "금", cls: "metal" },
    { key: "수", label: "수", cls: "water" },
  ];
  return (
    <div className="saju-dash__chips">
      {items.map((it) => (
        <span key={it.key} className={`saju-dash__chip saju-dash__chip--${it.cls}`}>
          {it.label} {counts[it.key] ?? 0}
        </span>
      ))}
    </div>
  );
}

export function SajuSummaryDashboard({ birth, report }: Props) {
  const [previewPillars, setPreviewPillars] = useState<Record<string, Record<string, string>> | null>(null);
  const [previewFiveElements, setPreviewFiveElements] = useState<Record<string, number> | null>(null);
  const [previewShinsalByWhere, setPreviewShinsalByWhere] = useState<Record<string, string[]> | null>(null);
  const [previewTwelveByWhere, setPreviewTwelveByWhere] = useState<Record<string, string> | null>(null);
  const ov = report?.sajuOverview ?? null;
  const raw = asRecord(report?.raw) ?? {};
  useEffect(() => {
    let alive = true;
    if (!birth) {
      setPreviewPillars(null);
      return () => {
        alive = false;
      };
    }
    const body = {
      birth: `${birth.date} ${birth.time}`,
      calendar: birth.calendarApi,
    };
    const base = getApiBase();
    const url = base ? `${base}/api/pillars` : "/api/pillars";
    fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
      .then(async (res) => {
        const json = (await res.json()) as Record<string, unknown>;
        const p = asRecord(json.pillars);
        if (!alive || !res.ok || !p) return;
        const year = asRecord(p.year);
        const month = asRecord(p.month);
        const day = asRecord(p.day);
        const hour = asRecord(p.hour);
        if (!year || !month || !day || !hour) return;
        setPreviewPillars({
          year: { gan: String(year.gan ?? ""), ji: String(year.ji ?? "") },
          month: { gan: String(month.gan ?? ""), ji: String(month.ji ?? "") },
          day: { gan: String(day.gan ?? ""), ji: String(day.ji ?? "") },
          hour: { gan: String(hour.gan ?? ""), ji: String(hour.ji ?? "") },
        });
        const fe = asRecord(json.fiveElements);
        const counts = asRecord(fe?.counts);
        setPreviewFiveElements(
          counts
            ? {
                목: Number(counts["목"] ?? 0),
                화: Number(counts["화"] ?? 0),
                토: Number(counts["토"] ?? 0),
                금: Number(counts["금"] ?? 0),
                수: Number(counts["수"] ?? 0),
              }
            : null
        );
        const sbw = asRecord(json.shinsalByWhere);
        setPreviewShinsalByWhere(
          sbw
            ? {
                year: Array.isArray(sbw.year) ? (sbw.year as unknown[]).map((x) => String(x)) : [],
                month: Array.isArray(sbw.month) ? (sbw.month as unknown[]).map((x) => String(x)) : [],
                day: Array.isArray(sbw.day) ? (sbw.day as unknown[]).map((x) => String(x)) : [],
                hour: Array.isArray(sbw.hour) ? (sbw.hour as unknown[]).map((x) => String(x)) : [],
              }
            : null
        );
        const tbw = asRecord(json.twelveByWhere);
        setPreviewTwelveByWhere(
          tbw
            ? {
                year: String(tbw.year ?? "—"),
                month: String(tbw.month ?? "—"),
                day: String(tbw.day ?? "—"),
                hour: String(tbw.hour ?? "—"),
              }
            : null
        );
      })
      .catch(() => {
        if (alive) {
          setPreviewPillars(null);
          setPreviewFiveElements(null);
          setPreviewShinsalByWhere(null);
          setPreviewTwelveByWhere(null);
        }
      });
    return () => {
      alive = false;
    };
  }, [birth?.date, birth?.time, birth?.calendarApi]);

  const p = ov
    ? {
        hour: ov.pillars.hour,
        day: ov.pillars.day,
        month: ov.pillars.month,
        year: ov.pillars.year,
      }
    : previewPillars
      ? {
          hour: previewPillars.hour ?? null,
          day: previewPillars.day ?? null,
          month: previewPillars.month ?? null,
          year: previewPillars.year ?? null,
        }
    : getPillars(raw);
  const sipsin = pickSipsin(raw);
  const localOhaeng = getLocalOhaengCountsFromPillars({
    year: p.year as Record<string, unknown> | null,
    month: p.month as Record<string, unknown> | null,
    day: p.day as Record<string, unknown> | null,
    hour: p.hour as Record<string, unknown> | null,
  });
  const ohaengCandidate = ov?.fiveElements?.counts ?? previewFiveElements ?? getOhaengCounts(raw);
  const ohaeng = isAllZeroCounts(ohaengCandidate) ? localOhaeng : ohaengCandidate;
  const localTwelveByWhere = localTwelveByWhereFromPillars({
    year: p.year as Record<string, unknown> | null,
    month: p.month as Record<string, unknown> | null,
    day: p.day as Record<string, unknown> | null,
    hour: p.hour as Record<string, unknown> | null,
  });
  const yinYangCounts = ov?.fiveElements?.yinYangCounts ?? {};
  const gongmang = pickFirst(raw.gongmang ?? asRecord(raw.analysis)?.gongmang);
  const dayStem = String((p.day as Record<string, unknown> | null)?.gan ?? "").trim();
  const gridKeys: Array<{ key: PillarKey; title: string; pillar: Record<string, unknown> | null }> = [
    { key: "hour", title: "시주", pillar: p.hour as Record<string, unknown> | null },
    { key: "day", title: "일주", pillar: p.day as Record<string, unknown> | null },
    { key: "month", title: "월주", pillar: p.month as Record<string, unknown> | null },
    { key: "year", title: "년주", pillar: p.year as Record<string, unknown> | null },
  ];
  /** 표시 순서: 년주 → 월주 → 일주 → 시주 (만세력 읽는 순서와 동일) */
  const cardKeys: Array<{ key: PillarKey; title: string; pillar: Record<string, unknown> | null }> = [
    { key: "year", title: "년주", pillar: p.year as Record<string, unknown> | null },
    { key: "month", title: "월주", pillar: p.month as Record<string, unknown> | null },
    { key: "day", title: "일주", pillar: p.day as Record<string, unknown> | null },
    { key: "hour", title: "시주", pillar: p.hour as Record<string, unknown> | null },
  ];
  const daewoon = ov?.daewoon ?? (((raw.daewoon as unknown[]) ?? (asRecord(raw.analysis)?.daewoon as unknown[]) ?? []).filter((x) => asRecord(x)).slice(0, 8) as any[]);
  const dayVoid =
    ov?.gongmang?.dayBase ??
    voidByPillar(String((p.day as Record<string, unknown> | null)?.gan ?? "").trim(), String((p.day as Record<string, unknown> | null)?.ji ?? "").trim());
  const yearVoid =
    ov?.gongmang?.yearBase ??
    voidByPillar(String((p.year as Record<string, unknown> | null)?.gan ?? "").trim(), String((p.year as Record<string, unknown> | null)?.ji ?? "").trim());

  return (
    <section className="saju-dash" aria-label="입력 페이지 사주 요약">
      <div className="saju-dash__head">
        <h2 className="saju-dash__title">입력값 기반 사주 요약</h2>
        <p className="saju-dash__meta">{formatDualCalendarBirthLine(birth)}</p>
      </div>

      <div className="saju-dash__grid8">
        <div className="saju-dash__grid-head"> </div>
        <div className="saju-dash__grid-head">시주</div>
        <div className="saju-dash__grid-head">일주</div>
        <div className="saju-dash__grid-head">월주</div>
        <div className="saju-dash__grid-head">년주</div>
        <div className="saju-dash__grid-label">천간</div>
        {gridKeys.map((c) => (
          <div key={`g-${c.key}`} className="saju-dash__grid-cell saju-dash__grid-cell--gan">
            {String(c.pillar?.gan ?? "—")}
          </div>
        ))}
        <div className="saju-dash__grid-label">지지</div>
        {gridKeys.map((c) => (
          <div key={`j-${c.key}`} className="saju-dash__grid-cell saju-dash__grid-cell--ji">
            {String(c.pillar?.ji ?? "—")}
          </div>
        ))}
      </div>

      <div className="saju-dash__pillar-grid">
        {cardKeys.map((c) => {
          const gan = String(c.pillar?.gan ?? "").trim();
          const ji = String(c.pillar?.ji ?? "").trim();
          const gm = STEM_META[gan];
          const jm = BRANCH_META[ji];
          const sh = previewShinsalByWhere?.[c.key] ?? byWhereShinsal(raw, c.key);
          return (
            <article key={c.title} className="saju-dash__pillar-card">
              <p className="saju-dash__pillar-title">{c.title}</p>
              <p className="saju-dash__pillar-main">
                {gan || "—"} {ji || "—"}
              </p>
              <div className="saju-dash__mini">
                <span className="saju-dash__mini-label">천간 오행</span>
                <span className="saju-dash__mini-value">
                  {String((c.pillar?.ganOhaeng as string | undefined) ?? (gm ? `${gm.sign}${gm.element}` : "—"))}
                </span>
              </div>
              <div className="saju-dash__mini">
                <span className="saju-dash__mini-label">지지 오행</span>
                <span className="saju-dash__mini-value">
                  {String((c.pillar?.jiOhaeng as string | undefined) ?? (jm ? `${jm.sign}${jm.element}` : "—"))}
                </span>
              </div>
              <div className="saju-dash__mini">
                <span className="saju-dash__mini-label">12운성</span>
                <span className="saju-dash__mini-value">
                  {formatTwelveStage(
                    String((c.pillar?.twelve as string | undefined) ?? previewTwelveByWhere?.[c.key] ?? localTwelveByWhere[c.key] ?? byWhereTwelve(raw, c.key) ?? "—")
                  )}
                </span>
              </div>
              <div className="saju-dash__chips">
                {((
                  Array.isArray(c.pillar?.shinsal)
                    ? (c.pillar?.shinsal as string[])
                    : sh
                ).length
                  ? (
                      Array.isArray(c.pillar?.shinsal)
                        ? (c.pillar?.shinsal as string[])
                        : sh
                    )
                  : ["—"]
                ).map((x, i) => (
                  <span key={i} className="saju-dash__chip saju-dash__chip--fortune">
                    {x}
                  </span>
                ))}
              </div>
            </article>
          );
        })}
      </div>

      <div className="saju-dash__blocks">
        <section className="saju-dash__block">
          <p className="saju-dash__block-title">오행 분포</p>
          <OhaengChips counts={ohaeng} />
          {Object.keys(yinYangCounts).length > 0 ? (
            <div className="saju-dash__chips" style={{ marginTop: "0.35rem" }}>
              {Object.entries(yinYangCounts).map(([k, v]) => (
                <span key={k} className="saju-dash__chip">
                  {k} {v}
                </span>
              ))}
            </div>
          ) : null}
        </section>
        <section className="saju-dash__block">
          <p className="saju-dash__block-title">공망 (기준 구분)</p>
          <div className="saju-dash__chips">
            <span className="saju-dash__chip saju-dash__chip--void">일주 기준: {dayVoid}</span>
            <span className="saju-dash__chip saju-dash__chip--void">년주 기준: {yearVoid}</span>
            {ov?.gongmang?.engineVoidBranches?.length ? (
              <span className="saju-dash__chip saju-dash__chip--void">
                엔진 공망 지지: {ov.gongmang.engineVoidBranches.join("·")}
              </span>
            ) : null}
            {gongmang !== "—" ? <span className="saju-dash__chip saju-dash__chip--void">{gongmang}</span> : null}
          </div>
        </section>
        <section className="saju-dash__block">
          <p className="saju-dash__block-title">신살 (기둥별)</p>
          <div className="saju-dash__shinsal-grid">
            {cardKeys.map((c) => {
              const arr = Array.isArray(c.pillar?.shinsal) ? (c.pillar?.shinsal as string[]) : [];
              const arrPreview = previewShinsalByWhere?.[c.key] ?? [];
              return (
                <div key={`sg-${c.key}`} className="saju-dash__shinsal-col">
                  <p className="saju-dash__shinsal-head">{c.title} 기준</p>
                  <div className="saju-dash__chips">
                    {(arr.length ? arr : arrPreview.length ? arrPreview : ["신살 없음"]).map((x, i) => (
                      <span key={`${c.key}-${i}`} className="saju-dash__chip saju-dash__chip--fortune">
                        {x}
                      </span>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
          <p className="saju-dash__block-title" style={{ marginTop: "0.65rem" }}>
            12운성 (기둥별)
          </p>
          <div className="saju-dash__shinsal-grid">
            {cardKeys.map((c) => {
              const rawTw = String((c.pillar?.twelve as string | undefined) ?? previewTwelveByWhere?.[c.key] ?? localTwelveByWhere[c.key] ?? byWhereTwelve(raw, c.key));
              return (
                <div key={`twelve-${c.key}`} className="saju-dash__shinsal-col">
                  <p className="saju-dash__shinsal-head">{c.title} 기준</p>
                  <div className="saju-dash__chips">
                    <span className="saju-dash__chip saju-dash__chip--state">{formatTwelveStage(rawTw)}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
        <section className="saju-dash__block">
          <p className="saju-dash__block-title">십신 (기둥별)</p>
          <div className="saju-dash__shinsal-grid">
            {cardKeys.map((c) => {
              const gan = String(c.pillar?.gan ?? "").trim();
              const sipsinChip = String((c.pillar?.sipsin as string | undefined) ?? (gan ? tenGod(dayStem, gan) : "—")) || "—";
              return (
                <div key={`sipsin-${c.key}`} className="saju-dash__shinsal-col">
                  <p className="saju-dash__shinsal-head">{c.title} 기준</p>
                  <div className="saju-dash__chips">
                    <span className="saju-dash__chip saju-dash__chip--fortune">{sipsinChip}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
        <section className="saju-dash__block">
          <p className="saju-dash__block-title">지장간 (기둥별)</p>
          <div className="saju-dash__shinsal-grid">
            {cardKeys.map((c) => {
              const ji = String(c.pillar?.ji ?? "").trim();
              const jm = BRANCH_META[ji];
              const hiddenFallback = (jm?.hidden ?? []).slice(0, 3);
              const stemsArr: string[] = Array.isArray(c.pillar?.hiddenStems)
                ? (c.pillar?.hiddenStems as Array<Record<string, unknown>>)
                    .map((h) => {
                      const stem = String(h.stem ?? "").trim();
                      const ss = String(h.sipsin ?? "").trim();
                      return stem ? `${stem}(${ss || tenGod(dayStem, stem)})` : "";
                    })
                    .filter(Boolean)
                : hiddenFallback.map((h) => `${h}(${tenGod(dayStem, h)})`);
              return (
                <div key={`hidden-${c.key}`} className="saju-dash__shinsal-col">
                  <p className="saju-dash__shinsal-head">{c.title} 기준</p>
                  <div className="saju-dash__chips">
                    {(stemsArr.length ? stemsArr : ["—"]).map((s, i) => (
                      <span key={i} className="saju-dash__chip saju-dash__chip--state">{s}</span>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      </div>

      <section className="saju-dash__block saju-dash__block--daewoon">
        <p className="saju-dash__block-title">대운</p>
        <div className="saju-dash__chips">
          {daewoon.length
            ? daewoon.map((d, i) => {
                const o = asRecord(d) ?? {};
                const pz = String(o.pillar ?? "—");
                const age = `${o.startAge ?? o.start_age ?? "?"}~${o.endAge ?? o.end_age ?? "?"}`;
                return (
                  <span key={i} className="saju-dash__chip saju-dash__chip--state">
                    {pz} ({age})
                  </span>
                );
              })
            : [<span key="n" className="saju-dash__chip">대운 데이터 준비 중</span>]}
        </div>
      </section>
    </section>
  );
}

