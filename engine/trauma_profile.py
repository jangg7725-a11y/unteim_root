# engine/trauma_profile.py
# -*- coding: utf-8 -*-
"""
운트임용 규칙 기반 ‘반복 정서/부담 성향’ 프로파일.
정신의학적 진단이 아니라 사주 구조 기반 해석 보조.
"""
from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional, Tuple

from utils.narrative_loader import load_sentences

TRAUMA_TYPES: Tuple[str, ...] = (
    "recognition_wound",
    "abandonment_wound",
    "over_responsibility",
    "self_blame",
    "instability_anxiety",
    "suppression_anger",
    "repetition_burnout",
)


def _f(x: Any) -> float:
    try:
        return float(x or 0)
    except Exception:
        return 0.0


def _ten_axis(packed: dict) -> Dict[str, float]:
    a = packed.get("analysis")
    if not isinstance(a, dict):
        return {}
    n = a.get("ten_gods_count")
    if not isinstance(n, dict):
        return {}
    out: Dict[str, float] = {}
    for k in ("인성", "식상", "관성", "재성", "비겁"):
        if k in n:
            out[k] = _f(n.get(k))
    return out


def _ten_detail(packed: dict) -> Dict[str, float]:
    a = packed.get("analysis")
    if not isinstance(a, dict):
        return {}
    t = a.get("ten_gods_count_10")
    if not isinstance(t, dict):
        return {}
    out: Dict[str, float] = {}
    for k in ("정인", "편인", "식신", "상관", "정관", "편관", "정재", "편재", "비견", "겁재"):
        if k in t:
            out[k] = _f(t.get(k))
    return out


def _five(packed: dict) -> Dict[str, float]:
    a = packed.get("analysis")
    if not isinstance(a, dict):
        return {}
    fe = a.get("five_elements_count")
    if not isinstance(fe, dict):
        return {}
    out: Dict[str, float] = {}
    for k, v in fe.items():
        kk = str(k)
        if kk in ("목", "화", "토", "금", "수"):
            out[kk] = _f(v)
    return out


def _shinsal_blob(packed: dict) -> str:
    sh = packed.get("shinsal")
    if not isinstance(sh, dict):
        a = packed.get("analysis")
        sh = a.get("shinsal") if isinstance(a, dict) else {}
    if not isinstance(sh, dict):
        return ""
    items = sh.get("items") or []
    if not isinstance(items, list):
        return ""
    parts: List[str] = []
    for it in items:
        if isinstance(it, dict):
            nm = str(it.get("name") or "")
            if nm:
                parts.append(nm)
    return " ".join(parts)


def _flow_blob(packed: dict) -> str:
    fs = packed.get("flow_summary")
    if not isinstance(fs, dict):
        return ""
    ui = fs.get("ui_view")
    if not isinstance(ui, dict):
        return ""
    return str(ui.get("wolwoon_commentary") or "") + str(ui.get("sewun_commentary") or "")


def _daewoon_pressure_hint(packed: dict) -> bool:
    dlist = packed.get("daewoon")
    if not isinstance(dlist, list):
        a = packed.get("analysis")
        dlist = a.get("daewoon") if isinstance(a, dict) else []
    if not isinstance(dlist, list):
        return False
    blob = str(dlist)[:2000]
    keys = ("관", "압", "책임", "규율", "경쟁", "바쁨", "바쁜", "시간")
    return any(k in blob for k in keys)


# 선택형 카테고리(직장/재물/건강/인연)별 트라우마 유형 가중 — 규칙만 이곳에서 조정
CATEGORY_TRAUMA_BONUSES: Dict[str, Dict[str, float]] = {
    "career": {
        "over_responsibility": 10.0,
        "recognition_wound": 8.0,
        "repetition_burnout": 7.0,
    },
    "money": {
        "instability_anxiety": 10.0,
        "self_blame": 6.0,
        "recognition_wound": 6.0,
    },
    "health": {
        "suppression_anger": 9.0,
        "repetition_burnout": 8.0,
        "instability_anxiety": 6.0,
    },
    "relationship": {
        "abandonment_wound": 11.0,
        "self_blame": 7.0,
        "suppression_anger": 6.0,
    },
}


def _category_bump(registry_id: str, t: str) -> float:
    return float(CATEGORY_TRAUMA_BONUSES.get(registry_id, {}).get(t, 0.0))


def score_to_intensity(score: int) -> str:
    if score >= 80:
        return "high"
    if score >= 55:
        return "medium"
    return "low"


def _score_types(packed: dict, registry_id: str) -> Dict[str, float]:
    tg = _ten_axis(packed)
    td = _ten_detail(packed)
    fe = _five(packed)
    sh = _shinsal_blob(packed)
    flow = _flow_blob(packed)
    관 = tg.get("관성", 0.0)
    식 = tg.get("식상", 0.0)
    인 = tg.get("인성", 0.0)
    재 = tg.get("재성", 0.0)
    비 = tg.get("비겁", 0.0)
    상관 = td.get("상관", 0.0)
    식신 = td.get("식신", 0.0)

    s: Dict[str, float] = {t: 0.0 for t in TRAUMA_TYPES}

    s["recognition_wound"] += 관 * 4.5 + 식 * 1.2
    if 인 < 2.0:
        s["recognition_wound"] += 6.0
    if 관 > 인 + 0.5:
        s["recognition_wound"] += 4.0

    if any(k in sh for k in ("도화", "홍염", "화개")):
        s["abandonment_wound"] += 10.0
    if any(k in sh for k in ("충", "형", "파", "해")):
        s["abandonment_wound"] += 5.0
    if "귀문" in sh or "고신" in sh:
        s["abandonment_wound"] += 4.0
        s["self_blame"] += 3.0

    s["over_responsibility"] += 관 * 4.0 + 비 * 1.5
    if 관 > 인:
        s["over_responsibility"] += 5.0
    if _daewoon_pressure_hint(packed):
        s["over_responsibility"] += 6.0
        s["repetition_burnout"] += 4.0

    s["self_blame"] += 인 * 3.5 + 관 * 2.0
    if 인 > 관:
        s["self_blame"] += 3.0

    s["instability_anxiety"] += 재 * 2.5 + 비 * 2.0
    if fe:
        try:
            mn = min(fe, key=lambda k: fe[k])
            if fe[mn] < 1.2:
                s["instability_anxiety"] += 7.0
        except Exception:
            pass
    if "수" in fe and fe["수"] < 1.5:
        s["instability_anxiety"] += 4.0

    s["suppression_anger"] += 상관 * 3.0 + (식 * 0.5 if 식신 < 상관 else 0.0)
    if "화" in fe and fe["화"] > 3.5:
        s["suppression_anger"] += 5.0
    if "금" in fe and fe["금"] > 3.5 and 상관 > 0:
        s["suppression_anger"] += 3.0

    s["repetition_burnout"] += 식 * 2.0 + 관 * 1.5
    if any(k in sh for k in ("형", "충", "관재")):
        s["repetition_burnout"] += 6.0
    if "반복" in flow or "바쁨" in flow:
        s["repetition_burnout"] += 3.0

    for t in TRAUMA_TYPES:
        s[t] += _category_bump(registry_id, t)

    return s


def _pick(pool: List[str], seed: str, suffix: str) -> str:
    if not pool:
        return ""
    h = int(hashlib.md5((seed + suffix).encode("utf-8")).hexdigest(), 16)
    return pool[h % len(pool)]


def _str_pool(x: Any) -> List[str]:
    """JSON 문자열 배열만 _pick 에 넘기기 (Pylance 안전)."""
    if not isinstance(x, list):
        return []
    out: List[str] = []
    for i in x:
        if isinstance(i, str) and i.strip():
            out.append(i)
    return out


def _labels_for_types(primary: str, secondary: str, data: dict) -> List[str]:
    tags = data.get("tag_pools") if isinstance(data, dict) else {}
    if not isinstance(tags, dict):
        return []
    out: List[str] = []
    for t in (primary, secondary):
        if not t:
            continue
        arr = tags.get(t)
        if isinstance(arr, list) and arr:
            out.append(str(arr[0]))
    # dedupe keep order
    seen = set()
    uniq: List[str] = []
    for x in out:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq[:4]


def _evidence_lines(packed: dict, scores: Dict[str, float], primary: str) -> List[str]:
    tg = _ten_axis(packed)
    fe = _five(packed)
    sh = _shinsal_blob(packed)
    lines: List[str] = []
    if tg.get("관성", 0) > tg.get("인성", 0) + 0.3:
        lines.append("십신 축에서 관성 대비 인성 비중이 유리하지 않게 잡힌 편입니다.")
    if fe:
        try:
            mx = max(fe, key=lambda k: fe[k])
            mn = min(fe, key=lambda k: fe[k])
            lines.append(f"오행 분포에서 {mx} 기운이 상대적으로 두드러지고 {mn}은 약합니다.")
        except Exception:
            pass
    if any(k in sh for k in ("도화", "홍염", "화개", "형", "충")):
        lines.append("신살·형충 신호가 관계·긴장 쪽에서 보조 근거로 잡힙니다.")
    if _daewoon_pressure_hint(packed):
        lines.append("대운 흐름에서 ‘책임·바쁨·압박’ 류 신호가 보조적으로 겹칠 수 있습니다.")
    td = _ten_detail(packed)
    if td.get("상관", 0) > td.get("식신", 0) and primary in ("suppression_anger", "recognition_wound"):
        lines.append("세부 십신에서 상관 에너지가 식신보다 두드러질 때 표현·억제가 엇갈릴 수 있습니다.")
    if primary == "instability_anxiety" and fe.get("수", 99) < 2.0:
        lines.append("수 기운이 약하게 잡히면 불안·회복 리듬이 흔들리기 쉽습니다.")
    return lines[:6]


def build_trauma_profile(packed: dict, registry_id: str, seed: str) -> Dict[str, Any]:
    scores = _score_types(packed, registry_id)
    ranked = sorted(TRAUMA_TYPES, key=lambda t: scores.get(t, 0.0), reverse=True)
    primary = ranked[0] if ranked else "repetition_burnout"
    secondary = ranked[1] if len(ranked) > 1 else "self_blame"

    raw_top = scores.get(primary, 0.0)
    score = int(max(0, min(100, round(raw_top * 1.8 + 22))))
    intensity = score_to_intensity(score)

    data = load_sentences("trauma_labels")
    if not isinstance(data, dict):
        data = {}
    types_raw = data.get("types")
    types_meta: Dict[str, Any] = types_raw if isinstance(types_raw, dict) else {}

    p_raw = types_meta.get(primary)
    p_meta: Dict[str, Any] = p_raw if isinstance(p_raw, dict) else {}

    lead_pool = _str_pool(p_meta.get("summary_lead_pool"))
    heal_pool = _str_pool(p_meta.get("healing_pool"))

    summary = _pick(lead_pool, seed, "tp|sum") + " "
    summary += _pick(heal_pool, seed, "tp|heal") if heal_pool else ""
    summary = summary.strip()

    healing_direction = _pick(heal_pool, seed, "tp|hd")

    labels = _labels_for_types(primary, secondary, data)
    evidence = _evidence_lines(packed, scores, primary)

    return {
        "primary_type": primary,
        "secondary_type": secondary,
        "score": score,
        "intensity": intensity,
        "labels": labels,
        "summary": summary,
        "evidence": evidence,
        "healing_direction": healing_direction,
    }
