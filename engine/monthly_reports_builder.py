# engine/monthly_reports_builder.py
"""세운(연운) 기준 12개월 월운 리포트 — full_analyzer / unified 연동."""
from __future__ import annotations

import random
import re
import statistics
from typing import Any, Dict, List, Tuple

from utils.narrative_loader import get_sentence

from .shinsal_score import summarize_shinsal
from .sipsin import BRANCH_TO_KOR
from .wolwoon_feature_calc import CHUNG, HAP

from .calendar_year_fortune import _find_sewun_pillar, resolve_pdf_target_year


def _sewun_rows_for_lookup(sewun: Any) -> List[Dict[str, Any]]:
    """sewun이 dict 리스트 또는 SewoonItem 등 객체 리스트일 때 year/year_pillar dict로 통일."""
    if not isinstance(sewun, list):
        return []
    out: List[Dict[str, Any]] = []
    for s in sewun:
        if isinstance(s, dict):
            out.append(s)
            continue
        y = getattr(s, "year", None)
        yp = getattr(s, "year_pillar", None)
        if y is not None:
            out.append({"year": int(y), "year_pillar": str(yp or "")})
    return out


from .month_stem_resolver import BRANCH_HANJA_TO_KOR, MonthStemResolver
from .sipsin import STEM_ELEM, branch_ten_gods, ten_god_stem
from .wolwoon_engine import _BRANCHES_FROM_IN

_KOR_JI_TO_HANJA = {v: k for k, v in BRANCH_HANJA_TO_KOR.items()}

_EN = frozenset({"wood", "fire", "earth", "metal", "water"})

# 지지 본행(표층)
_BRANCH_ELEM: Dict[str, str] = {
    "子": "水",
    "丑": "土",
    "寅": "木",
    "卯": "木",
    "辰": "土",
    "巳": "火",
    "午": "火",
    "未": "土",
    "申": "金",
    "酉": "金",
    "戌": "土",
    "亥": "水",
}

_KR_HANJA_TO_EN = {
    "목": "wood",
    "화": "fire",
    "토": "earth",
    "금": "metal",
    "수": "water",
    "木": "wood",
    "火": "fire",
    "土": "earth",
    "金": "metal",
    "水": "water",
}


def _to_elem_en(tok: Any) -> str:
    t = str(tok or "").strip()
    return _KR_HANJA_TO_EN.get(t, "") if t else ""


def _oheng_dict(packed: Dict[str, Any]) -> Dict[str, Any]:
    oh = packed.get("oheng")
    if isinstance(oh, dict):
        return oh
    an = packed.get("analysis")
    if isinstance(an, dict):
        o2 = an.get("oheng")
        if isinstance(o2, dict):
            return o2
    return {}


def _five_element_counts(packed: Dict[str, Any]) -> Dict[str, Any]:
    an = packed.get("analysis")
    if isinstance(an, dict):
        c = an.get("five_elements_count")
        if isinstance(c, dict) and c:
            return c
    oh = _oheng_dict(packed)
    c = oh.get("counts")
    return c if isinstance(c, dict) else {}


def _aggregate_en_counts(counts: Dict[str, Any]) -> Dict[str, float]:
    agg = {e: 0.0 for e in _EN}
    for k, v in counts.items():
        en = _to_elem_en(k)
        if en not in _EN:
            continue
        try:
            agg[en] += float(v or 0)
        except Exception:
            pass
    return agg


def _extreme_element_en(counts: Dict[str, Any], *, pick_max: bool) -> str:
    agg = _aggregate_en_counts(counts)
    if sum(agg.values()) <= 0:
        return ""
    items = [(e, agg[e]) for e in _EN]
    if pick_max:
        return max(items, key=lambda x: x[1])[0]
    return min(items, key=lambda x: x[1])[0]


def _dominant_weak_en(packed: Dict[str, Any]) -> tuple[str, str]:
    """
    (dominant_en, weak_en) — narrative domain_templates_v2 키(wood_strong 등)에 맞춤.
    oheng.dominant 등이 있으면 우선, 없으면 five_elements_count 극대/극소.
    """
    oh = _oheng_dict(packed)
    for label, pick_max in (("dominant", True), ("dominant_element", True), ("main_element", True)):
        raw = oh.get(label)
        if raw:
            en = _to_elem_en(raw)
            if en:
                counts = _five_element_counts(packed)
                weak = _extreme_element_en(counts, pick_max=False) if counts else ""
                return en, weak
    counts = _five_element_counts(packed)
    if counts:
        d = _extreme_element_en(counts, pick_max=True)
        w = _extreme_element_en(counts, pick_max=False)
        return d, w
    return "", ""


_FINAL_FALLBACK = (
    "이번 달 흐름은 개인 사주와 월기운을 함께 보며, 무리한 확장보다 정리·확인·컨디션 관리에 "
    "무게를 두면 체감이 좋아집니다."
)


# 1~3: 시작 / 4~6: 압박·성과 / 7~9: 변수·관계 / 10~12: 안정·결실
def _month_tone_bucket(month_index: int) -> int:
    m = int(month_index)
    if m <= 3:
        return 0
    if m <= 6:
        return 1
    if m <= 9:
        return 2
    return 3


_TONE_NAMES = ("start", "pressure", "variable", "stable")

# 분기별 접두어 풀(월·도메인·지지 시드로 골라 문장 구조를 다르게 함)
_TONE_PREFIX_POOLS: Tuple[List[str], ...] = (
    [  # 0 시작·확장·시도
        "새 흐름이 시작됩니다.",
        "시작과 시도의 기운이 앞섭니다.",
        "계획을 올리고 첫 시동을 걸기 좋은 달입니다.",
        "확장보다 ‘첫 시도’에 무게를 두면 체감이 좋아집니다.",
        "새로운 제안·루틴을 작게 열어보기 좋은 흐름입니다.",
    ],
    [  # 1 정리·압박·성과
        "성과와 부담이 동시에 들어옵니다.",
        "마감·정리·평가가 겹치기 쉬운 달입니다.",
        "실무 밀도가 올라가고 책임이 무거워질 수 있어요.",
        "속도보다 ‘정리·증빙’이 점수를 가릅니다.",
        "압박 속에서도 우선순위만 지키면 버틸 수 있습니다.",
    ],
    [  # 2 변수·충돌·관계
        "예상 밖 변수가 생길 수 있습니다.",
        "일정·사람·조건이 엇갈리기 쉬운 달입니다.",
        "관계·약속에서 오해가 생기기 쉬우니 확인이 필요합니다.",
        "환경이 바뀌는 신호가 있으니 유연하게 대응하세요.",
        "말·문서·약속을 한 번 더 확인하면 리스크가 줄어듭니다.",
    ],
    [  # 3 안정·결실·정리
        "흐름이 안정되고 정리됩니다.",
        "한 해의 결실을 묶고 마무리하기 좋은 흐름입니다.",
        "속도를 낮추고 ‘확정·정리’에 무게를 두면 좋습니다.",
        "지출·일정·관계를 정리하면 마음이 가벼워집니다.",
        "긴 호흡보다 짧은 마감과 확인이 이득입니다.",
    ],
)


def _month_field_seed(month: int, domain: str, ji: str) -> int:
    h = 0
    for c in (domain + ji):
        h = (h * 31 + ord(c)) % (2**31 - 1)
    return int(month) * 100000 + h


def _pick_tone_prefix(month: int, domain: str, ji: str) -> str:
    b = _month_tone_bucket(month)
    pool = _TONE_PREFIX_POOLS[b]
    rng = random.Random(_month_field_seed(month, domain, ji))
    return rng.choice(pool)


def _apply_tone_prefix(text: str, month: int, domain: str, ji: str) -> str:
    t = (text or "").strip()
    if not t:
        return t
    pre = _pick_tone_prefix(month, domain, ji)
    if t.startswith(pre[:2]):
        return t
    return f"{pre} {t}"


_SIPSIN_KW: Dict[str, str] = {
    "비견": "자기 확립",
    "겁재": "경쟁 조율",
    "식신": "표현·결과",
    "상관": "말·조율",
    "정재": "재물·안정",
    "편재": "기회·흐름",
    "정관": "직무·규범",
    "편관": "압박·돌파",
    "정인": "회복·학습",
    "편인": "직관·내면",
}

_DOM_KW: Dict[str, str] = {
    "wood": "확장·추진",
    "fire": "속도·열정",
    "earth": "안정·정리",
    "metal": "기준·마감",
    "water": "분석·유연",
    "default": "균형",
}

_TONE_KW_EXTRA: Tuple[List[str], ...] = (
    ["기회 포착", "새 출발", "확장 시도"],
    ["성과 정리", "실무 집중", "마감 대응"],
    ["관계 조율", "변수 대응", "합충 정리"],
    ["결실 정리", "안정 마감", "한 해 정돈"],
)


def _summary_line(month: int, s_stem: str, dom_en: str) -> str:
    sk = _SIPSIN_KW.get(str(s_stem or "").strip(), "운세 조율")
    dk = _DOM_KW.get(dom_en or "default", "균형")
    b = _month_tone_bucket(month)
    rng = random.Random(_month_field_seed(month, "summary", str(dom_en)))
    tk = rng.choice(_TONE_KW_EXTRA[b])
    return f"핵심: {sk} · {dk} · {tk}"


def _ji_to_kor(ji: str) -> str:
    t = str(ji or "").strip()
    return BRANCH_TO_KOR.get(t, t)


def _natal_branches_kor(pillars: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    for k in ("year", "month", "day", "hour"):
        p = pillars.get(k)
        if not isinstance(p, dict):
            continue
        j = _ji_to_kor(str(p.get("ji") or ""))
        if j:
            out.append(j)
    return out


def _balance_points(agg: Dict[str, float]) -> int:
    t = sum(agg.values())
    if t <= 0:
        return 8
    probs = [agg[e] / t for e in _EN]
    if len(probs) < 2:
        return 0
    var = statistics.pvariance(probs)
    # 5개 균등 분포면 var≈0, 한 편중이면 커짐
    return int(22 * (1.0 - min(var * 6.0, 1.0)))


def _sipsin_strength_points(stem: str) -> int:
    s = str(stem or "").strip()
    good = {"정관", "정재", "정인", "식신"}
    mixed = {"편관", "편재", "상관", "편인", "겁재"}
    if s in good:
        return 18
    if s in mixed:
        return 12
    if s in {"비견"}:
        return 14
    return 10


def _clash_hap_adjust(mb_kor: str, natal: List[str]) -> int:
    """월지(한글) vs 원국 지지: 충은 감점, 합은 가점."""
    adj = 0
    for b in natal:
        if (mb_kor, b) in CHUNG:
            adj -= 7
        elif (mb_kor, b) in HAP:
            adj += 6
    return max(-22, min(18, adj))


def _month_luck_score(
    *,
    pillars: Dict[str, Any],
    month_branch_hanja: str,
    agg: Dict[str, float],
    s_stem: str,
) -> int:
    """
    0~100: 오행 균형 + 십신 강도 + 월지 vs 원국 충·합.
    """
    base = 32
    bal = _balance_points(agg)
    sp = _sipsin_strength_points(s_stem)
    mb = _ji_to_kor(month_branch_hanja)
    natal = _natal_branches_kor(pillars)
    ch_adj = _clash_hap_adjust(mb, natal)
    raw = base + bal + sp + ch_adj
    return int(max(0, min(100, raw)))


def _luck_score_line(score: int) -> str:
    return f"이번 달 운 점수: {score}점"


def _key_slug(tok: Any) -> str:
    t = str(tok or "").strip()
    if not t:
        return "unknown"
    t = re.sub(r"[\s\.\(\)]+", "_", t)
    t = re.sub(r"_+", "_", t).strip("_")
    return t or "unknown"


def _verdict_from_packed(packed: Dict[str, Any]) -> str:
    """신살 items 요약 verdict(길/보통(혼재)/흉 등). 계산 로직 변경 없이 기존 items만 요약."""
    for blk in (packed.get("analysis"), packed):
        if not isinstance(blk, dict):
            continue
        sh = blk.get("shinsal")
        if isinstance(sh, list):
            items = sh
        elif isinstance(sh, dict):
            items = sh.get("items") or []
        else:
            items = []
        if not isinstance(items, list):
            items = []
        try:
            summ = summarize_shinsal(items)
            v = str(summ.get("verdict") or "").strip()
            if v:
                return v
        except Exception:
            pass
    return ""


# 월간 천간 십신 → 도메인별 JSON 힌트 키 (정재/편재→money, 정관/편관→job, 식상→관계, 인성→건강)
_SIPSIN_HINT_KEYS: Dict[tuple[str, str], List[str]] = {
    ("job", "정관"): ["tg_정관"],
    ("job", "편관"): ["tg_편관"],
    ("money", "정재"): ["tg_정재"],
    ("money", "편재"): ["tg_편재"],
    ("relationship", "식신"): ["tg_식신"],
    ("relationship", "상관"): ["tg_상관"],
    ("health", "정인"): ["tg_정인"],
    ("health", "편인"): ["tg_편인"],
}


def _sipsin_hint_keys(domain: str, ten_god: str) -> List[str]:
    tg = str(ten_god or "").strip()
    return list(_SIPSIN_HINT_KEYS.get((domain, tg), []))


def _month_narrative_key_candidates(
    month: int,
    ten_god: str,
    dom_en: str,
    tmpl_key: str,
    verdict: str,
    domain: str,
) -> List[str]:
    """
    상위 job/money/… 풀과 domain_templates_v2 모두에서 동일 키로 조회.
    JSON 키는 점(.) 경로 분할을 피하기 위해 언더스코어만 사용.
    우선순위: 십신 힌트 → m{MM}_십신_편중_판정 → m{MM}_십신 → m{MM} → 십신_편중 → 편중(영문) → tmpl_key → default
    """
    m = f"{int(month):02d}"
    tg = _key_slug(ten_god)
    dom = _key_slug(dom_en) if dom_en else "default"
    vd = _key_slug(verdict) if verdict else "unknown"

    # 월별 m01~m12가 십신 힌트(tg_*)보다 먼저 와야, 간지가 주기로 겹쳐도 달마다 문장이 갈린다.
    raw: List[str] = [
        f"m{m}_{tg}_{dom}_{vd}",
        f"m{m}_{tg}",
        f"m{m}",
    ]
    raw.extend(_sipsin_hint_keys(domain, ten_god))
    raw.append(f"{tg}_{dom}")
    if dom != "default":
        raw.append(dom)
    raw.extend([tmpl_key, "default"])

    seen: set[str] = set()
    out: List[str] = []
    for c in raw:
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out


def _resolve_domain_narrative(domain: str, candidates: List[str]) -> str:
    """
    1) 최상위 job / money / … (monthly_sentences.json 루트)
    2) domain_templates_v2.{domain}.{key}
    후보 순서대로; default는 JSON에 있을 때만 매칭. 전부 비면 최종 _FINAL_FALLBACK.
    """
    for key in candidates:
        if not key:
            continue
        for base in (domain, f"domain_templates_v2.{domain}"):
            s = get_sentence("monthly_sentences", f"{base}.{key}", "")
            s = (s or "").strip()
            if s:
                return s
    return _FINAL_FALLBACK


def _stem_elem(gan: str) -> str:
    return str(STEM_ELEM.get(gan, "") or "")


def _branch_elem(ji: str) -> str:
    return str(_BRANCH_ELEM.get(ji, "") or "")


def _summary(
    month: int,
    gan: str,
    ji: str,
    sipsin_stem: str,
    stem_el: str,
    branch_el: str,
) -> str:
    gj = f"{gan}{ji}" if gan and ji else "—"
    return (
        f"{month}월 월주 {gj}: 월간 십신 {sipsin_stem or '—'}, "
        f"천간 오행 {stem_el or '—'}, 지지 오행 {branch_el or '—'}."
    )


def attach_monthly_reports(packed: Dict[str, Any]) -> None:
    """
    packed에 monthly_reports(길이 12)를 채운다.
    - 대상 연도: resolve_pdf_target_year(packed) (sewun / meta / when / 올해)
    - 월지 순서: 인월(1) ~ 축월(12) — 세운 해당 연도의 월간은 MonthStemResolver(연도·지지).
    - narrative: monthly_sentences 루트 job/… + domain_templates_v2, 이후 분기 톤 접두어.
    - summary_line / luck_score / luck_score_line / flow(핵심·점수·요약) 추가.
    """
    pillars = packed.get("pillars")
    if not isinstance(pillars, dict):
        packed["monthly_reports"] = []
        return

    day = pillars.get("day")
    if not isinstance(day, dict):
        packed["monthly_reports"] = []
        return

    day_stem = str(day.get("gan") or "").strip()
    if not day_stem:
        packed["monthly_reports"] = []
        return

    sewun = packed.get("sewun")
    if not isinstance(sewun, list):
        an = packed.get("analysis")
        if isinstance(an, dict):
            sewun = an.get("sewun")
    if not isinstance(sewun, list):
        sewun = []

    sewun_rows = _sewun_rows_for_lookup(sewun)
    target_year = resolve_pdf_target_year(packed)
    year_pillar = _find_sewun_pillar(sewun_rows, target_year)

    dom_en, weak_en = _dominant_weak_en(packed)
    dominant = dom_en if dom_en else "default"
    weak = weak_en if weak_en else "default"
    if dom_en:
        tmpl_key = f"{dom_en}_strong"
    else:
        tmpl_key = "default"

    verdict = _verdict_from_packed(packed)
    agg_profile = _aggregate_en_counts(_five_element_counts(packed))

    ms = MonthStemResolver()
    out: List[Dict[str, Any]] = []

    for i, br_kor in enumerate(_BRANCHES_FROM_IN):
        month_n = i + 1
        gan = ""
        try:
            gan = str(ms.resolve(target_year, br_kor) or "").strip()
        except Exception:
            gan = ""

        ji = _KOR_JI_TO_HANJA.get(br_kor, br_kor)
        s_stem = ten_god_stem(day_stem, gan) if gan else "미상"
        s_branch = branch_ten_gods(day_stem, ji) if ji else {}
        se = _stem_elem(gan)
        be = _branch_elem(ji)

        summ = _summary(month_n, gan, ji, s_stem, se, be)
        sl = _summary_line(month_n, s_stem, dom_en)
        luck = _month_luck_score(
            pillars=pillars,
            month_branch_hanja=ji,
            agg=agg_profile,
            s_stem=s_stem,
        )
        luck_txt = _luck_score_line(luck)
        tone_bucket = _month_tone_bucket(month_n)

        row: Dict[str, Any] = {
            "month": month_n,
            "gan": gan,
            "ji": ji,
            "ganji": f"{gan}{ji}" if (gan and ji) else "",
            "sewun_year": target_year,
            "year_pillar": year_pillar,
            "sipsin": {
                "stem": s_stem,
                "branch": s_branch,
            },
            "month_ten_god": s_stem,
            "verdict": verdict,
            "month_tone": _TONE_NAMES[tone_bucket],
            "month_tone_index": tone_bucket,
            "oheng": {
                "stem": se,
                "branch": be,
            },
            "summary": summ,
            "summary_line": sl,
            "luck_score": luck,
            "luck_score_line": luck_txt,
            "dominant": dominant,
            "weak": weak,
        }

        pillar = row["ganji"]
        row["pillar"] = pillar
        row["month_pillar"] = pillar
        row["flow"] = "\n".join([sl, luck_txt, summ])

        # narrative: get_sentence 후 분기 톤 접두어 + 루트 job/money/… → domain_templates_v2
        row["job"] = _apply_tone_prefix(
            _resolve_domain_narrative(
                "job",
                _month_narrative_key_candidates(month_n, s_stem, dom_en, tmpl_key, verdict, "job"),
            ),
            month_n,
            "job",
            ji,
        )
        row["money"] = _apply_tone_prefix(
            _resolve_domain_narrative(
                "money",
                _month_narrative_key_candidates(month_n, s_stem, dom_en, tmpl_key, verdict, "money"),
            ),
            month_n,
            "money",
            ji,
        )
        row["relationship"] = _apply_tone_prefix(
            _resolve_domain_narrative(
                "relationship",
                _month_narrative_key_candidates(month_n, s_stem, dom_en, tmpl_key, verdict, "relationship"),
            ),
            month_n,
            "relationship",
            ji,
        )
        row["health"] = _apply_tone_prefix(
            _resolve_domain_narrative(
                "health",
                _month_narrative_key_candidates(month_n, s_stem, dom_en, tmpl_key, verdict, "health"),
            ),
            month_n,
            "health",
            ji,
        )
        row["caution"] = _apply_tone_prefix(
            _resolve_domain_narrative(
                "caution",
                _month_narrative_key_candidates(month_n, s_stem, dom_en, tmpl_key, verdict, "caution"),
            ),
            month_n,
            "caution",
            ji,
        )
        row["tip"] = _apply_tone_prefix(
            _resolve_domain_narrative(
                "tip",
                _month_narrative_key_candidates(month_n, s_stem, dom_en, tmpl_key, verdict, "tip"),
            ),
            month_n,
            "tip",
            ji,
        )

        # reports/report_calendar_fortune.py: 직장·일=career, 활용 팁=tips
        row["career"] = row["job"]
        row["tips"] = row["tip"]

        out.append(row)

    packed["monthly_reports"] = out
