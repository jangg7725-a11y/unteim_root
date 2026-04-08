# unteim/engine/dynamic_strength_engine_v1.py
# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

ELEM_KEYS = ("목", "화", "토", "금", "수")
TG_KEYS = ("인성", "식상", "관성", "재성", "비겁")


def _safe_get(d: Any, path: str, default=None):
    cur = d
    for key in path.split("."):
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def _to_num(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        if isinstance(x, bool):
            return float(x)
        return float(x)
    except Exception:
        return default


def _norm_map(m: Any, keys: Tuple[str, ...]) -> Dict[str, float]:
    out = {k: 0.0 for k in keys}
    if not isinstance(m, dict):
        return out
    for k in keys:
        if k in m:
            out[k] = _to_num(m.get(k), 0.0)
    return out


def _sum_maps(a: Dict[str, float], b: Dict[str, float], w: float = 1.0) -> Dict[str, float]:
    out = dict(a)
    for k, v in b.items():
        out[k] = out.get(k, 0.0) + (v * w)
    return out


def _scale_map(a: Dict[str, float], w: float) -> Dict[str, float]:
    return {k: v * w for k, v in a.items()}


def _minmax_normalize(a: Dict[str, float], floor: float = 0.0) -> Dict[str, float]:
    vals = list(a.values())
    if not vals:
        return a
    mn, mx = min(vals), max(vals)
    if mx - mn < 1e-9:
        # 모두 같으면 그대로(또는 전부 floor+1 같은 방식도 가능)
        return {k: max(floor, v) for k, v in a.items()}
    return {k: max(floor, (v - mn) / (mx - mn)) for k, v in a.items()}


def _pick_base_elements(report: Dict[str, Any]) -> Dict[str, float]:
    """
    base 오행 기세 후보들을 폭넓게 탐색.
    - 이미 존재하는 five_elements_strength가 있으면 그걸 base로 사용
    - 없으면 elements_count/ratio 계열을 찾아서 사용
    """
    # 1) 이미 계산된 게 있으면 그대로
    for p in (
        "analysis.five_elements_strength",
        "analysis.elements_strength",
        "analysis.five_elements.strength",
    ):
        m = _safe_get(report, p)
        if isinstance(m, dict) and any(k in m for k in ELEM_KEYS):
            return _norm_map(m, ELEM_KEYS)

    # 2) count/ratio 계열
    for p in (
        "analysis.five_elements_count",
        "analysis.elements_count",
        "analysis.five_elements.count",
        "analysis.elements",
        "analysis.five_elements",
    ):
        m = _safe_get(report, p)
        if isinstance(m, dict) and any(k in m for k in ELEM_KEYS):
            # count/ratio 모두 수치로 흡수
            return _norm_map(m, ELEM_KEYS)

    return {k: 0.0 for k in ELEM_KEYS}


def _pick_base_tengods(report: Dict[str, Any]) -> Dict[str, float]:
    """
    base 십신 기세 후보 탐색.
    - ten_gods_strength가 있으면 그걸 base
    - 없으면 ten_gods_count/summary 등을 찾아서 축약(인성/식상/관성/재성/비겁)
    """
    for p in (
        "analysis.ten_gods_strength",
        "analysis.ten_gods.strength",
        "analysis.tengods_strength",
    ):
        m = _safe_get(report, p)
        if isinstance(m, dict) and any(k in m for k in TG_KEYS):
            return _norm_map(m, TG_KEYS)

    for p in (
        "analysis.ten_gods_count",
        "analysis.ten_gods.count",
        "analysis.ten_gods",
        "analysis.tengods",
    ):
        m = _safe_get(report, p)
        if isinstance(m, dict):
            # 이미 5축으로 들어있는 경우
            if any(k in m for k in TG_KEYS):
                return _norm_map(m, TG_KEYS)

            # 정인/편인/식신/상관/정관/편관/정재/편재/비견/겁재 형태면 5축으로 합산
            agg = {k: 0.0 for k in TG_KEYS}
            agg["인성"] = _to_num(m.get("정인"), 0.0) + _to_num(m.get("편인"), 0.0)
            agg["식상"] = _to_num(m.get("식신"), 0.0) + _to_num(m.get("상관"), 0.0)
            agg["관성"] = _to_num(m.get("정관"), 0.0) + _to_num(m.get("편관"), 0.0)
            agg["재성"] = _to_num(m.get("정재"), 0.0) + _to_num(m.get("편재"), 0.0)
            agg["비겁"] = _to_num(m.get("비견"), 0.0) + _to_num(m.get("겁재"), 0.0)
            if any(v != 0.0 for v in agg.values()):
                return agg

    return {k: 0.0 for k in TG_KEYS}


def _pick_overlay_elements(report: Dict[str, Any], name: str) -> Dict[str, float]:
    """
    overlay(대운/세운/월운) 오행 기세 후보 탐색.
    name: "daewun" | "sewun" | "wolwoon"
    """
    candidates = (
        f"analysis.{name}.five_elements_strength",
        f"analysis.{name}.elements_strength",
        f"analysis.{name}.five_elements",
        f"analysis.{name}.elements",
        f"analysis.{name}_elements_strength",
        f"analysis.{name}_five_elements_strength",
        f"extra.{name}.five_elements_strength",
        f"extra.{name}.elements_strength",
    )
    for p in candidates:
        m = _safe_get(report, p)
        if isinstance(m, dict) and any(k in m for k in ELEM_KEYS):
            return _norm_map(m, ELEM_KEYS)
    return {k: 0.0 for k in ELEM_KEYS}


def _pick_overlay_tengods(report: Dict[str, Any], name: str) -> Dict[str, float]:
    candidates = (
        f"analysis.{name}.ten_gods_strength",
        f"analysis.{name}.ten_gods",
        f"analysis.{name}_ten_gods_strength",
        f"extra.{name}.ten_gods_strength",
    )
    for p in candidates:
        m = _safe_get(report, p)
        if isinstance(m, dict) and any(k in m for k in TG_KEYS):
            return _norm_map(m, TG_KEYS)
    return {k: 0.0 for k in TG_KEYS}


def build_dynamic_strength_v1(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    ✅ 동적 기세 엔진 v1
    - base + overlays(daewun/sewun/wolwoon)
    - 있으면 합산, 없으면 0으로 안전 통과
    - 결과를 analysis에 항상 저장
    """
    analysis = report.get("analysis")
    if not isinstance(analysis, dict):
        analysis = {}
        report["analysis"] = analysis

    # ---- base ----
    base_el = _pick_base_elements(report)
    base_tg = _pick_base_tengods(report)

    # ---- overlays ----
    # 가중치는 v1 기본값 (나중에 config/feature flag로 뺄 수 있음)
    W_DAEWUN = 0.35
    W_SEWUN = 0.45
    W_WOLWOON = 0.65

    ov_da_el = _pick_overlay_elements(report, "daewun")
    ov_sw_el = _pick_overlay_elements(report, "sewun")   # ✅ sewoon 아님: sewun
    ov_mw_el = _pick_overlay_elements(report, "wolwoon")

    ov_da_tg = _pick_overlay_tengods(report, "daewun")
    ov_sw_tg = _pick_overlay_tengods(report, "sewun")
    ov_mw_tg = _pick_overlay_tengods(report, "wolwoon")

    # ---- 합산 ----
    el = dict(base_el)
    el = _sum_maps(el, ov_da_el, W_DAEWUN)
    el = _sum_maps(el, ov_sw_el, W_SEWUN)
    el = _sum_maps(el, ov_mw_el, W_WOLWOON)

    tg = dict(base_tg)
    tg = _sum_maps(tg, ov_da_tg, W_DAEWUN)
    tg = _sum_maps(tg, ov_sw_tg, W_SEWUN)
    tg = _sum_maps(tg, ov_mw_tg, W_WOLWOON)

    # ---- 정규화(선택): 패턴 점수 안정화용 ----
    # 0~1 범위로 만들어두면 모델/문장화에서 일관성이 좋아짐
    analysis["five_elements_strength"] = _minmax_normalize(el, floor=0.0)
    analysis["ten_gods_strength"] = _minmax_normalize(tg, floor=0.0)

    # ======================================================
    # ✅ [B-v1] 용신 가중치 반영 (관성 축 자동 보정)
    # - yongshin element가 '관성 연결 오행'이면 관성 축 +0.15
    # - analysis["dynamic_strength_meta"]["yongshin_boost"]에 기록
    # ======================================================
    def _cap01(x: float) -> float:
        return 0.0 if x < 0 else (1.0 if x > 1 else x)

    # yongshin element 추출 (string or dict 모두 지원)
    ysh = analysis.get("yongshin")
    y_elem = None
    if isinstance(ysh, str):
        y_elem = ysh.strip()
    elif isinstance(ysh, dict):
        y_elem = (ysh.get("element") or ysh.get("yongshin") or ysh.get("yong") or "").strip()

    # 관성 연결 오행 추출(있으면 사용)
    link = analysis.get("ten_gods_element_link") if isinstance(analysis.get("ten_gods_element_link"), dict) else None
    gwan_elem = None
    if link and link.get("ok") and isinstance(link.get("axis_to_element"), dict):
        gwan_elem = link["axis_to_element"].get("관성")

    meta = analysis.setdefault("dynamic_strength_meta", {})

    if y_elem and gwan_elem and y_elem == gwan_elem:
        boost = 0.15
        _raw_tg = analysis.get("ten_gods_strength")
        tg_norm: Dict[str, Any] = dict(_raw_tg) if isinstance(_raw_tg, dict) else {}
        tg_norm["관성"] = _cap01(float(tg_norm.get("관성", 0.0)) + boost)
        analysis["ten_gods_strength"] = tg_norm
        meta["yongshin_boost"] = {"axis": "관성", "element": y_elem, "boost": boost, "applied": True}
    else:
        meta["yongshin_boost"] = {"applied": False, "y_elem": y_elem, "gwan_elem": gwan_elem}


    # 디버그/버전
    analysis["dynamic_strength"] = {
        "version": "v1",
        "weights": {"daewun": W_DAEWUN, "sewun": W_SEWUN, "wolwoon": W_WOLWOON},
        "base_present": {
            "elements": any(v != 0.0 for v in base_el.values()),
            "tengods": any(v != 0.0 for v in base_tg.values()),
        },
        "overlay_present": {
            "daewun_el": any(v != 0.0 for v in ov_da_el.values()),
            "sewun_el": any(v != 0.0 for v in ov_sw_el.values()),
            "wolwoon_el": any(v != 0.0 for v in ov_mw_el.values()),
            "daewun_tg": any(v != 0.0 for v in ov_da_tg.values()),
            "sewun_tg": any(v != 0.0 for v in ov_sw_tg.values()),
            "wolwoon_tg": any(v != 0.0 for v in ov_mw_tg.values()),
        },
    }
    return report


def attach_dynamic_strength_v1(report: Dict[str, Any]) -> Dict[str, Any]:
    return build_dynamic_strength_v1(report)
