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


def _build_extend_block(registry_id: str, packed: dict, report_key: str) -> Dict[str, Any]:
    seed = _seed(packed)
    pool = _load_topic_pool(registry_id)
    title = pool.get("title") or TOPIC_DEFS.get(registry_id, ("", "extend"))[0]
    summaries = pool.get("summary_pool") or []
    bullets = [str(b) for b in (pool.get("bullets_pool") or []) if str(b).strip()]
    summary = _pick(summaries, seed, registry_id + "|s")
    bl: List[str] = []
    for i, b in enumerate(bullets[:8]):
        bl.append(_pick([b], seed, registry_id + "|b" + str(i)))

    for e in _engine_hints(registry_id, packed):
        if e and e not in bl:
            bl.insert(0, e)

    return {
        "id": report_key,
        "registry_id": registry_id,
        "title": title,
        "summary": summary,
        "bullets": bl[:10],
        "source": "narrative_v1+engine_hints",
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
