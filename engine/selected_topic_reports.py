# engine/selected_topic_reports.py
# -*- coding: utf-8 -*-
"""
선택형 주제 리포트 — 기본 리포트(총운·연간·월·오늘)와 분리된 확장 블록.
packed["selected_reports"] 는 report_key(예: career, move, document)를 최상위 키로 사용한다.
"""
from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional

from utils.narrative_loader import load_sentences
from engine.report_topic_registry import (
    TOPIC_DEFS,
    export_topic_catalog,
    normalize_selected_topics,
    partition_topics,
    registry_id_to_report_key,
)
from engine.trauma_profile import build_trauma_profile

PATTERN_REGISTRY_IDS = frozenset({"career", "money", "health", "relationship"})
INTENSITY_SLOTS = frozenset({"emotion", "insight", "action"})


def _as_dict(x: Any) -> Dict[str, Any]:
    return x if isinstance(x, dict) else {}


def _as_list(x: Any) -> List[Any]:
    return x if isinstance(x, list) else []


def _str_list(x: Any) -> List[str]:
    """JSON 배열 → 문자열 리스트 (Pylance 안전 + _pick 용)."""
    if not isinstance(x, list):
        return []
    out: List[str] = []
    for i in x:
        if isinstance(i, str) and i.strip():
            out.append(i)
        elif i is not None and not isinstance(i, (dict, list)):
            s = str(i).strip()
            if s:
                out.append(s)
    return out


def _seed(packed: dict) -> str:
    _pr = packed.get("pillars")
    p: Dict[str, Any] = _pr if isinstance(_pr, dict) else {}
    _dr = p.get("day")
    d: Dict[str, Any] = _dr if isinstance(_dr, dict) else {}
    return str(d.get("gan", "")) + str(d.get("ji", "")) + str(packed.get("birth_str", ""))


def _pick(pool: List[str], seed: str, suffix: str) -> str:
    if not pool:
        return ""
    h = int(hashlib.md5((seed + suffix).encode("utf-8")).hexdigest(), 16)
    return pool[h % len(pool)]


def _load_topic_pool(registry_id: str) -> Dict[str, Any]:
    data = load_sentences("selected_topics_v1")
    if not isinstance(data, dict):
        return {}
    topics = data.get("topics") or {}
    t = topics.get(registry_id)
    return t if isinstance(t, dict) else {}


def _load_slot_pools() -> Dict[str, Any]:
    d = load_sentences("topic_slot_pools")
    return d if isinstance(d, dict) else {}


def _intensity_band_lines(registry_id: str, slot: str, primary: str, intensity: str) -> List[str]:
    """slot_intensity_bands.json — emotion/insight/action + primary + low|medium|high."""
    if slot not in INTENSITY_SLOTS:
        return []
    data = load_sentences("slot_intensity_bands")
    if not isinstance(data, dict):
        return []
    reg = _as_dict(_as_dict(data.get("registry_ids")).get(registry_id))
    slot_obj = _as_dict(reg.get(slot))
    by_primary = _as_dict(slot_obj.get(primary))
    raw = _as_list(by_primary.get(intensity))
    return [str(x).strip() for x in raw if isinstance(x, str) and x.strip()]


def _collect_slot_candidate_lines(
    registry_id: str,
    slot: str,
    primary: str,
    secondary: str,
    intensity: str,
    legacy_topic: Dict[str, Any],
) -> List[str]:
    """
    topic_slot_pools.json: pools[].trauma_types 와 primary/secondary/default 교집합이 있으면 lines 합류.
    emotion/insight/action 은 slot_intensity_bands (primary+intensity) 후보를 먼저 합류.
    pools[].intensity 가 있으면 현재 intensity 와 일치할 때만 해당 풀 사용.
    sentence_set_integration: selected_topics_v1 필드(예: summary_pool)를 insight 등 슬롯 후보에 합류.
    """
    lines: List[str] = []
    if slot in INTENSITY_SLOTS:
        lines.extend(_intensity_band_lines(registry_id, slot, primary, intensity))

    data = _load_slot_pools()
    reg = _as_dict(_as_dict(data.get("registry_ids")).get(registry_id))
    slot_obj = _as_dict(reg.get(slot))
    pool_list = _as_list(slot_obj.get("pools"))
    active = {primary, secondary, "default"}
    for pool in pool_list:
        if not isinstance(pool, dict):
            continue
        pint = pool.get("intensity")
        if pint is not None and str(pint).strip() != "" and slot in INTENSITY_SLOTS:
            if str(pint).strip().lower() != str(intensity).lower():
                continue
        tts = pool.get("trauma_types")
        if not isinstance(tts, list):
            continue
        if not (set(str(t) for t in tts) & active):
            continue
        for ln in pool.get("lines") or []:
            if isinstance(ln, str) and ln.strip():
                lines.append(ln.strip())
    if not lines:
        for pool in pool_list:
            if not isinstance(pool, dict):
                continue
            tts = pool.get("trauma_types")
            if not isinstance(tts, list) or "default" not in tts:
                continue
            for ln in pool.get("lines") or []:
                if isinstance(ln, str) and ln.strip():
                    lines.append(ln.strip())

    integ_root = _as_dict(data.get("sentence_set_integration"))
    stv = _as_dict(integ_root.get("selected_topics_v1"))
    per = _as_dict(stv.get(registry_id))
    append_map = _as_dict(per.get("append_fields_to_slot"))
    field_names = _as_list(append_map.get(slot))
    for fn in field_names:
        arr = legacy_topic.get(fn)
        if not isinstance(arr, list):
            continue
        for x in arr:
            if isinstance(x, str) and x.strip():
                lines.append(x.strip())

    return lines


def _dedupe_lines(lines: List[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for x in lines:
        t = x.strip()
        if not t or t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out


def _join_with_inner_slot(registry_id: str, slot: str, seed: str, parts: List[str]) -> str:
    """한 슬롯 안 2~3문장 — inner_slot_joiners 풀에서 시드로 연결."""
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0].strip()
    data = load_sentences("slot_connectors")
    if not isinstance(data, dict):
        data = {}
    inner = _as_dict(data.get("inner_slot_joiners"))
    default_pool = _str_list(inner.get("default"))
    if not default_pool:
        default_pool = [" "]
    by_slot = _as_dict(inner.get("by_slot"))
    slot_pool = _str_list(by_slot.get(slot))
    pool = slot_pool if slot_pool else default_pool
    out = parts[0].strip()
    for j in range(1, len(parts)):
        sep = _pick(pool, seed, f"inner|{registry_id}|{slot}|{j}")
        out += sep + parts[j].strip()
    return out.strip()


def _compose_slot_text(
    registry_id: str,
    slot: str,
    seed: str,
    primary: str,
    secondary: str,
    intensity: str,
    legacy_topic: Dict[str, Any],
) -> str:
    merged = _collect_slot_candidate_lines(
        registry_id, slot, primary, secondary, intensity, legacy_topic
    )
    uniq = _dedupe_lines(merged)
    if not uniq:
        return ""
    n = len(uniq)
    h = int(
        hashlib.md5(
            (seed + registry_id + slot + primary + secondary + intensity).encode("utf-8")
        ).hexdigest(),
        16,
    )
    if n == 1:
        return uniq[0]
    if n == 2:
        return _join_with_inner_slot(registry_id, slot, seed, uniq)
    want = 2 + (h % 2)
    want = min(want, n)
    idx = list(range(n))
    idx.sort(key=lambda i: hashlib.md5(f"{seed}|{slot}|{i}".encode("utf-8")).hexdigest())
    parts = [uniq[i] for i in idx[:want]]
    return _join_with_inner_slot(registry_id, slot, seed, parts)


def _bridge_phrase(registry_id: str, primary: str, bridge_key: str, seed: str) -> str:
    data = load_sentences("slot_connectors")
    if not isinstance(data, dict):
        return ""
    bridges = _as_dict(data.get("bridges"))
    base_list = _str_list(bridges.get(bridge_key))
    reg_root = _as_dict(data.get("by_registry"))
    reg = _as_dict(reg_root.get(registry_id))
    reg_list = _str_list(reg.get(bridge_key))
    tr_root = _as_dict(data.get("by_trauma_primary"))
    tr = _as_dict(tr_root.get(primary))
    tr_list = _str_list(tr.get(bridge_key))
    pool = [x for x in base_list + reg_list + tr_list if x.strip()]
    return _pick(pool, seed, f"bridge|{bridge_key}|{registry_id}") if pool else ""


def _build_narrative_flow(
    registry_id: str,
    primary: str,
    seed: str,
    cause: str,
    pattern: str,
    emotion: str,
    insight: str,
    action: str,
) -> str:
    texts = [cause, pattern, emotion, insight, action]
    bridge_keys = [
        "cause_to_pattern",
        "pattern_to_emotion",
        "emotion_to_insight",
        "insight_to_action",
    ]
    bridge_between: Dict[tuple[int, int], str] = {
        (0, 1): bridge_keys[0],
        (1, 2): bridge_keys[1],
        (2, 3): bridge_keys[2],
        (3, 4): bridge_keys[3],
    }
    flow = ""
    prev_i: Optional[int] = None
    for i, t in enumerate(texts):
        if not (isinstance(t, str) and t.strip()):
            continue
        if prev_i is not None:
            bk = bridge_between.get((prev_i, i))
            if bk:
                br = _bridge_phrase(registry_id, primary, bk, seed + str(prev_i) + str(i))
                if br:
                    flow += " " + br + " "
                else:
                    flow += " "
        flow += t.strip()
        prev_i = i
    return flow.strip()


def _hint_ten_axis(packed: dict) -> Dict[str, float]:
    _ar = packed.get("analysis")
    a: Dict[str, Any] = _ar if isinstance(_ar, dict) else {}
    n = a.get("ten_gods_count")
    if not isinstance(n, dict):
        n = {}
    out: Dict[str, float] = {}
    for k, v in n.items():
        kk = str(k)
        if kk in ("인성", "식상", "관성", "재성", "비겁"):
            try:
                out[kk] = float(v or 0)
            except Exception:
                continue
    return out


def _hint_shinsal_names(packed: dict) -> List[str]:
    sh = packed.get("shinsal")
    if not isinstance(sh, dict):
        sh = packed.get("analysis", {}).get("shinsal") if isinstance(packed.get("analysis"), dict) else {}
    if not isinstance(sh, dict):
        return []
    items = sh.get("items") or []
    if not isinstance(items, list):
        return []
    names: List[str] = []
    for it in items:
        if isinstance(it, dict):
            nm = str(it.get("name") or "").strip()
            if nm:
                names.append(nm)
    return names[:16]


def _hint_yongshin_element(packed: dict) -> str:
    _an = packed.get("analysis")
    a: Dict[str, Any] = _an if isinstance(_an, dict) else {}
    _ys = a.get("yongshin")
    ys: Dict[str, Any] = _ys if isinstance(_ys, dict) else {}
    inner = ys.get("yongshin")
    inner_el = ""
    if isinstance(inner, dict):
        inner_el = str(inner.get("element", "") or "").strip()
    elif isinstance(inner, str):
        inner_el = inner.strip()
    el = str(ys.get("yongshin_element") or ys.get("element") or inner_el or "").strip()
    return el


def _hint_five_elements(packed: dict) -> Dict[str, float]:
    _an = packed.get("analysis")
    a: Dict[str, Any] = _an if isinstance(_an, dict) else {}
    fe = a.get("five_elements_count")
    if not isinstance(fe, dict):
        return {}
    out: Dict[str, float] = {}
    for k, v in fe.items():
        try:
            out[str(k)] = float(v or 0)
        except Exception:
            continue
    return out


def _v2_first_line(packed: dict, *keys: str) -> str:
    v2 = packed.get("v2_sentences")
    if not isinstance(v2, dict):
        return ""
    for key in keys:
        block = v2.get(key)
        if isinstance(block, list) and block:
            first = block[0]
            if isinstance(first, dict):
                t = str(first.get("text") or "").strip()
                if t:
                    return t[:220]
            elif isinstance(first, str) and first.strip():
                return first.strip()[:220]
        if isinstance(block, dict):
            tr = block.get("table_row")
            if isinstance(tr, dict) and tr:
                # 한 줄 요약
                parts = [str(v) for v in list(tr.values())[:2] if v]
                if parts:
                    return " · ".join(parts)[:220]
    return ""


def _flow_ui_line(packed: dict) -> str:
    fs = packed.get("flow_summary")
    if not isinstance(fs, dict):
        return ""
    ui = fs.get("ui_view")
    if not isinstance(ui, dict):
        return ""
    for k in ("wolwoon_commentary", "sewun_commentary", "summary_line"):
        t = str(ui.get(k) or "").strip()
        if t:
            return t[:200]
    return ""


def _engine_hints(registry_id: str, packed: dict) -> List[str]:
    extras: List[str] = []
    tg = _hint_ten_axis(packed)

    if registry_id == "career":
        g = float(tg.get("관성", 0.0)) + float(tg.get("식상", 0.0))
        if g > 0.0:
            extras.append(
                f"엔진: 십신 축에서 관성·식상 가중 합이 약 {g:.1f}입니다. 업무 성과·보고·책임이 동시에 겹치기 쉬운 타입으로 읽힙니다."
            )
        ys = _hint_yongshin_element(packed)
        if ys:
            extras.append(f"엔진: 용신 방향({ys})에 맞춘 업무 스타일(집중 분야·협업 방식)을 택하면 피로 대비 효율이 좋아집니다.")

    elif registry_id == "money":
        g = float(tg.get("재성", 0.0)) + float(tg.get("비겁", 0.0))
        if g > 0.0:
            extras.append(
                f"엔진: 재성·비겁 합이 약 {g:.1f}로 수입·지출이 연동되기 쉬운 패턴입니다. 고정비·미수·현금흐름을 함께 보면 좋습니다."
            )
        fe = _hint_five_elements(packed)
        if fe:
            try:
                mx = max(fe, key=lambda k: fe[k])
                mn = min(fe, key=lambda k: fe[k])
                if mx != mn and fe[mx] > 0 and fe[mn] >= 0:
                    extras.append(
                        f"엔진: 오행 분포에서 {mx} 기운이 상대적으로 두드러지고 {mn}은 약합니다. 소비·투자·저축 루틴을 약한 쪽 보완에 맞출 수 있습니다."
                    )
            except Exception:
                pass

    elif registry_id == "health":
        fe = _hint_five_elements(packed)
        if len(fe) >= 3:
            try:
                mx = max(fe, key=lambda k: fe[k])
                mn = min(fe, key=lambda k: fe[k])
                if fe[mx] >= 3.0 or fe[mx] - fe[mn] >= 2.0:
                    extras.append(
                        f"엔진: 원국 오행에서 {mx}가 강하고 {mn}이 상대적으로 약합니다. 수면·소화·호흡 등 루틴을 약한 쪽 보완에 맞추면 안정에 도움이 됩니다."
                    )
            except Exception:
                pass

    elif registry_id == "relationship":
        sh = _hint_shinsal_names(packed)
        hits = [x for x in sh if any(k in x for k in ("도화", "홍염", "화개"))]
        if hits:
            extras.append(f"엔진: 신살에 「{hits[0][:40]}」 등이 보입니다. 인연 기회와 말실수·오해 가능성을 같이 점검하는 편이 안전합니다.")

    elif registry_id == "compatibility":
        _an2 = packed.get("analysis")
        sp: Dict[str, Any] = {}
        if isinstance(_an2, dict):
            _sip = _an2.get("sipsin")
            sp = _sip if isinstance(_sip, dict) else {}
        dm = ""
        if sp:
            _pf = sp.get("profiles")
            prof: Dict[str, Any] = _pf if isinstance(_pf, dict) else {}
            _st = prof.get("stems")
            stems: Dict[str, Any] = _st if isinstance(_st, dict) else {}
            day = stems.get("day") or stems.get("일")
            if isinstance(day, dict):
                dm = str(day.get("sipsin_name") or day.get("name") or "").strip()
        if dm:
            extras.append(f"엔진: 일간 십신이 「{dm[:16]}」로 잡힙니다. 상대 사주 없이도 ‘내 관계 스타일’의 기준점으로 쓸 수 있습니다.")
        extras.append(
            "안내: 궁합 정밀도는 상대 생년월일·시간 입력 시 일간·지지 합충형·용신 보완으로 확장할 수 있습니다."
        )

    elif registry_id == "travel_move":
        line = _flow_ui_line(packed)
        if line:
            extras.append(f"엔진: 현재 세운·월운 흐름 코멘터리 일부 — {line}")
        else:
            extras.append("엔진: 환경·이동은 세운/월운 변동과 함께 읽는 것이 안전합니다. 조건·계약·일정을 문서로 남기세요.")

    elif registry_id == "exam":
        _exr = packed.get("extra")
        extra: Dict[str, Any] = _exr if isinstance(_exr, dict) else {}
        mp = extra.get("month_patterns") or []
        pid = ""
        if isinstance(mp, list):
            for p in mp[:12]:
                if not isinstance(p, dict):
                    continue
                pids = str(p.get("id") or p.get("title") or "")
                if "exam" in pids.lower() or "시험" in pids or "합격" in pids or "학업" in pids:
                    pid = pids[:48]
                    break
        if pid:
            extras.append(f"엔진: 월간 패턴에서 「{pid}」 계열 신호가 포착됩니다. 정리·복습 루틴을 우선하세요.")
        g = float(tg.get("인성", 0.0)) + float(tg.get("식상", 0.0))
        if g > 0.0:
            extras.append(f"엔진: 인성·식상 합이 약 {g:.1f}로 학습·정리·표출 에너지가 동시에 작동하기 쉬운 편입니다.")

    elif registry_id == "marriage":
        sh = _hint_shinsal_names(packed)
        hits = [x for x in sh if any(k in x for k in ("도화", "홍염", "화개"))]
        if hits:
            extras.append(f"엔진: 인연 신호 「{hits[0][:40]}」이 보입니다. 만남은 늘어나도 선택은 현실 조건과 함께 보는 편이 안전합니다.")
        g = float(tg.get("재성", 0.0)) + float(tg.get("관성", 0.0))
        if g > 0.0:
            extras.append(f"엔진: 재성·관성 합이 약 {g:.1f}로 관계에서 책임·현실(경제·역할) 이슈가 함께 올 수 있습니다.")

    elif registry_id == "business":
        g1 = float(tg.get("재성", 0.0)) + float(tg.get("식상", 0.0))
        if g1 > 0.0:
            extras.append(
                f"엔진: 재성·식상 합이 약 {g1:.1f}입니다. 매출·아이디어·실행이 동시에 돌아가는 구조인지 현금흐름과 함께 보세요."
            )

    elif registry_id == "contract_doc":
        sh = _hint_shinsal_names(packed)
        hits = [x for x in sh if any(k in x for k in ("관재", "백호", "형", "충", "관재살"))]
        if hits:
            extras.append(f"엔진: 「{hits[0][:40]}」 등 긴장·분쟁 신호가 있을 수 있어 계약·증빙을 특히 꼼꼼히 두는 편이 좋습니다.")

    elif registry_id == "noble":
        sh = _hint_shinsal_names(packed)
        hits = [x for x in sh if "귀인" in x or "천을" in x]
        if hits:
            extras.append(f"엔진: 「{hits[0][:40]}」 등 귀인 신호가 보입니다. 도움은 요청이 구체할수록 잘 붙는 편입니다.")

    elif registry_id == "accident_gossip":
        sh = _hint_shinsal_names(packed)
        hits = [x for x in sh if any(k in x for k in ("형", "충", "살", "관재", "구설", "백호"))]
        if hits:
            extras.append(f"엔진: 「{hits[0][:40]}」 등 긴장 신호가 보일 수 있어 안전·말투·이동 일정에 여유를 두세요.")

    elif registry_id == "gaeunbeop":
        line = _v2_first_line(packed, "B2_yongshin_advice", "B1_practice_table")
        if line:
            extras.append(f"엔진: 용신·실천 개운법 요약 — {line}")
        ys = _hint_yongshin_element(packed)
        if ys and not line:
            extras.append(f"엔진: 용신 방향을 {ys}에 맞춘 색·방위·루틴을 우선하면 생활 정렬에 도움이 됩니다.")

    return extras[:4]


def _pick_trigger_message(registry_id: str, seed: str) -> str:
    data = load_sentences("selected_topic_triggers")
    if not isinstance(data, dict):
        return ""
    base = _str_list(data.get("default_pool"))
    by_reg = data.get("by_registry")
    reg = _str_list(by_reg.get(registry_id)) if isinstance(by_reg, dict) else []
    pool = [x for x in base + reg if x.strip()]
    return _pick(pool, seed, f"trigger|{registry_id}") if pool else ""


def _pick_cta_message(registry_id: str, seed: str) -> str:
    data = load_sentences("selected_topic_cta")
    if not isinstance(data, dict):
        return ""
    base = _str_list(data.get("default_pool"))
    by_reg = data.get("by_registry")
    reg = _str_list(by_reg.get(registry_id)) if isinstance(by_reg, dict) else []
    pool = [x for x in base + reg if x.strip()]
    return _pick(pool, seed, f"cta|{registry_id}") if pool else ""


def _emotion_excerpt(text: str, limit: int = 160) -> str:
    """무료 구역용 감정 슬롯 일부 (고정문 아님, 길이 기준 발췌)."""
    t = (text or "").strip()
    if not t:
        return ""
    if len(t) <= limit:
        return t
    cut = t[:limit]
    for sep in (" ", "，", ",", "·", "\n"):
        idx = cut.rfind(sep)
        if idx > limit // 3:
            return t[:idx].strip() + "…"
    return cut.strip() + "…"


def _build_extend_block(registry_id: str, packed: dict, report_key: str) -> Dict[str, Any]:
    if registry_id in PATTERN_REGISTRY_IDS:
        return _build_pattern_block(registry_id, packed, report_key)
    seed = _seed(packed)
    pool = _load_topic_pool(registry_id)
    title = pool.get("title") or TOPIC_DEFS.get(registry_id, ("", "extend"))[0]
    summaries = _str_list(pool.get("summary_pool"))
    bullets = [str(b) for b in _as_list(pool.get("bullets_pool")) if str(b).strip()]
    summary = _pick(summaries, seed, registry_id + "|s")
    bl: List[str] = []
    for i, b in enumerate(bullets[:8]):
        bl.append(_pick([b], seed, registry_id + "|b" + str(i)))

    for e in _engine_hints(registry_id, packed):
        if e and e not in bl:
            bl.insert(0, e)

    trig = _pick_trigger_message(registry_id, seed)
    cta = _pick_cta_message(registry_id, seed)
    return {
        "id": report_key,
        "registry_id": registry_id,
        "title": title,
        "summary": summary,
        "bullets": bl[:10],
        "trigger_message": trig,
        "cta_message": cta,
        "free_version": {
            "summary": summary,
            "emotion": "",
        },
        "premium_version": {
            "summary": summary,
            "bullets": bl[:10],
        },
        "source": "narrative_v1+engine_hints",
        "tier": "extend",
    }


def _build_pattern_block(registry_id: str, packed: dict, report_key: str) -> Dict[str, Any]:
    seed = _seed(packed)
    pool = _load_topic_pool(registry_id)
    title = pool.get("title") or TOPIC_DEFS.get(registry_id, ("", "extend"))[0]
    legacy_summary = [str(x) for x in _as_list(pool.get("summary_pool")) if str(x).strip()]
    legacy_bullets = [str(b) for b in _as_list(pool.get("bullets_pool")) if str(b).strip()]

    tp = build_trauma_profile(packed, registry_id, seed)
    primary = str(tp.get("primary_type") or "")
    secondary = str(tp.get("secondary_type") or "")
    intensity = str(tp.get("intensity") or "medium")

    cause = _compose_slot_text(registry_id, "cause", seed, primary, secondary, intensity, pool)
    pattern = _compose_slot_text(registry_id, "pattern", seed, primary, secondary, intensity, pool)
    emotion = _compose_slot_text(registry_id, "emotion", seed, primary, secondary, intensity, pool)
    insight = _compose_slot_text(registry_id, "insight", seed, primary, secondary, intensity, pool)
    action = _compose_slot_text(registry_id, "action", seed, primary, secondary, intensity, pool)

    narrative_flow = _build_narrative_flow(
        registry_id, primary, seed, cause, pattern, emotion, insight, action
    )

    summary = _pick([insight, narrative_flow] + legacy_summary, seed, registry_id + "|summary_mix") if (
        insight or narrative_flow or legacy_summary
    ) else ""

    bl: List[str] = []
    for slot_txt, label in (
        (cause, "원인"),
        (pattern, "반복"),
        (emotion, "느낌"),
        (insight, "이해"),
        (action, "방향"),
    ):
        if slot_txt:
            bl.append(f"{label}: {slot_txt}")
    for e in _engine_hints(registry_id, packed):
        if e and e not in bl:
            bl.insert(0, e)
    for i, b in enumerate(legacy_bullets[:6]):
        bl.append(_pick([b], seed, registry_id + "|lb" + str(i)))

    em_ex = _emotion_excerpt(emotion)
    free_version = {
        "summary": summary,
        "emotion": em_ex,
    }
    premium_version = {
        "cause": cause,
        "pattern": pattern,
        "emotion": emotion,
        "insight": insight,
        "action": action,
        "trauma_profile": tp,
        "narrative_flow": narrative_flow,
        "bullets": bl[:14],
    }

    trig = _pick_trigger_message(registry_id, seed)
    cta = _pick_cta_message(registry_id, seed)

    return {
        "id": report_key,
        "registry_id": registry_id,
        "title": title,
        "summary": summary,
        "bullets": bl[:14],
        "cause": cause,
        "pattern": pattern,
        "emotion": emotion,
        "insight": insight,
        "action": action,
        "narrative_flow": narrative_flow,
        "trauma_profile": tp,
        "trigger_message": trig,
        "cta_message": cta,
        "free_version": free_version,
        "premium_version": premium_version,
        "source": "pattern_slots+trauma_profile+narrative_v1",
        "tier": "extend",
    }


def build_selected_reports_dict(packed: dict, topics: Optional[List[str]]) -> Dict[str, Any]:
    norm = normalize_selected_topics(topics or [])
    base, extend, _planned = partition_topics(norm)
    reports: Dict[str, Any] = {}

    seen_rk: set[str] = set()
    order_keys: List[str] = []
    for tid in norm:
        if tid not in TOPIC_DEFS or TOPIC_DEFS[tid][1] != "extend":
            continue
        rk = registry_id_to_report_key(tid)
        if rk in seen_rk:
            continue
        seen_rk.add(rk)
        order_keys.append(rk)

    for tid in extend:
        rk = registry_id_to_report_key(tid)
        if rk in reports:
            continue
        reports[rk] = _build_extend_block(tid, packed, rk)

    return {
        "meta": {
            "requested": norm,
            "requested_report_keys": order_keys,
            "requested_base": base,
            "requested_extend": extend,
        },
        "reports": reports,
    }


def attach_selected_topic_reports(packed: dict, selected_topics: Optional[List[str]] = None) -> None:
    """
    - packed['meta']['selected_topics'] : PDF/출력 순서용 report_key 목록
    - packed['selected_reports'] : { career: {...}, move: {...} } (flat)
    - packed['topic_catalog'] : UI용 카탈로그
    """
    packed["topic_catalog"] = export_topic_catalog()

    meta = packed.setdefault("meta", {})
    if selected_topics is not None:
        norm = normalize_selected_topics(selected_topics)
        meta["selected_topics"] = norm
    else:
        raw = meta.get("selected_topics")
        norm = normalize_selected_topics(raw if isinstance(raw, list) else [])

    if not norm:
        packed["selected_reports"] = {}
        ex = packed.setdefault("extra", {})
        ex["selected_reports"] = {}
        ex["selected_topics"] = []
        ex["selected_reports_meta"] = {
            "requested": [],
            "requested_report_keys": [],
            "requested_extend": [],
            "requested_base": [],
        }
        meta["selected_report_keys"] = []
        meta["selected_registry_ids"] = []
        return

    structured = build_selected_reports_dict(packed, norm)
    flat = structured.get("reports") or {}
    if not isinstance(flat, dict):
        flat = {}
    sm = structured.get("meta") or {}
    report_order = sm.get("requested_report_keys") if isinstance(sm, dict) else []

    meta["selected_topics"] = norm
    meta["selected_report_keys"] = report_order
    meta["selected_registry_ids"] = sm.get("requested_extend") if isinstance(sm, dict) else []

    packed["selected_reports"] = flat
    ex = packed.setdefault("extra", {})
    ex["selected_reports"] = flat
    ex["selected_topics"] = norm
    ex["selected_reports_structured"] = structured
    ex["selected_reports_meta"] = sm
