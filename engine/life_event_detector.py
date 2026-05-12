# engine/life_event_detector.py
# -*- coding: utf-8 -*-
"""
월운(月運)에서 주요 인생 사건 신호를 감지한다.

근거:
1. 지지 충(沖) — 월지가 사주 원국 기둥과 충
2. 신살(神殺) — 백호·양인·상문·원진 등
3. 육친(六親) 충극 — 월지의 십신이 어떤 육친인가
4. 오행 불균형 — 일간이 강하게 극받는 경우

출력:
각 월(row)에 life_event_signals 리스트 주입
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Set

from utils.narrative_loader import load_sentences

_DB_FILE = "life_event_signals_db"

# 홍염살 — 일간 기준 지지
_HONGNYEOM_TABLE: Dict[str, str] = {
    '甲': '午', '乙': '午',
    '丙': '寅', '丁': '未',
    '戊': '辰', '己': '辰',
    '庚': '戌', '辛': '酉',
    '壬': '子', '癸': '申',
}

# 원진살 — 지지 쌍
_WONJIN_MAP: Dict[str, str] = {
    '子': '未', '未': '子',
    '丑': '午', '午': '丑',
    '寅': '酉', '酉': '寅',
    '卯': '申', '申': '卯',
    '辰': '亥', '亥': '辰',
    '巳': '戌', '戌': '巳',
}

# 도화살 — 일지/년지 기준 지지
_DOHWA_TABLE: Dict[str, str] = {
    '子': '卯', '午': '酉', '卯': '子', '酉': '午',
    '寅': '午', '戌': '午', '巳': '酉', '丑': '酉',
    '申': '子', '辰': '子', '亥': '卯', '未': '卯',
}

# 지지 충 쌍
_CHUNG_PAIRS: List[tuple] = [
    ("子", "午"), ("丑", "未"), ("寅", "申"),
    ("卯", "酉"), ("辰", "戌"), ("巳", "亥"),
]
_CHUNG_MAP: Dict[str, str] = {}
for a, b in _CHUNG_PAIRS:
    _CHUNG_MAP[a] = b
    _CHUNG_MAP[b] = a

# 지지 형(刑) 쌍
_HYEONG_MAP: Dict[str, List[str]] = {
    "寅": ["巳"], "巳": ["申"], "申": ["寅"],
    "丑": ["戌"], "戌": ["未"], "未": ["丑"],
    "子": ["卯"], "卯": ["子"],
}

# 십신 → 육친 역할
_SIPSIN_TO_ROLE: Dict[str, str] = {
    "편관": "편관", "정관": "정관",
    "편인": "편인", "정인": "정인",
    "식신": "식신", "상관": "상관",
    "편재": "편재", "정재": "정재",
    "비견": "비견", "겁재": "겁재",
}

# 천간 극 관계 (극하는 쪽 → 극받는 쪽)
_GAN_克: Dict[str, str] = {
    "甲": "戊", "乙": "己",  # 木克土
    "丙": "庚", "丁": "辛",  # 火克金
    "戊": "壬", "己": "癸",  # 土克水
    "庚": "甲", "辛": "乙",  # 金克木
    "壬": "丙", "癸": "丁",  # 水克火
}
# 반대: 일간이 극받는 천간 세트
_GAN_克_REVERSE: Dict[str, str] = {v: k for k, v in _GAN_克.items()}


def _db() -> Dict[str, Any]:
    return load_sentences(_DB_FILE)


def _pick(pool: List[str], seed: int) -> str:
    if not pool:
        return ""
    rng = random.Random(seed)
    return rng.choice(pool)


def _get_natal_branches(packed: Dict[str, Any]) -> List[str]:
    """사주 원국 4개 지지 추출."""
    pillars = packed.get("pillars") or {}
    branches = []
    for key in ["year", "month", "day", "hour"]:
        p = pillars.get(key) or {}
        ji = str(p.get("ji") or "").strip()
        if ji:
            branches.append(ji)
    return branches


def _get_day_gan(packed: Dict[str, Any]) -> str:
    """일간 추출."""
    pillars = packed.get("pillars") or {}
    day = pillars.get("day") or {}
    return str(day.get("gan") or "").strip()


def _get_shinsal_names(packed: Dict[str, Any]) -> List[str]:
    """사주 원국 신살 목록 추출."""
    analysis = packed.get("analysis") or {}
    shinsal = analysis.get("shinsal") or {}
    items = shinsal.get("items") or []
    names = []
    for item in items:
        if isinstance(item, dict):
            name = str(item.get("name") or "").strip()
            if name and not name.startswith("12운성:"):
                names.append(name)
    return names


def _get_month_shinsal(packed: Dict[str, Any], month_row: Dict[str, Any]) -> List[str]:
    """월운 row에서 해당 월 신살 목록 추출."""
    # monthly_fortune months에서 신살 정보 추출
    shinsal_list = month_row.get("shinsalHighlights") or []
    gongmang = month_row.get("gongmangLine") or ""
    result = list(shinsal_list)
    if gongmang and "공망" in gongmang:
        result.append("공망")
    return result


def _check_chung(month_ji: str, natal_branches: List[str]) -> List[str]:
    """월지가 원국 어느 기둥과 충인지 반환."""
    target = _CHUNG_MAP.get(month_ji)
    if not target:
        return []
    return [b for b in natal_branches if b == target]


def _check_hyeong(month_ji: str, natal_branches: List[str]) -> List[str]:
    """월지가 원국과 형(刑)인지 반환."""
    targets = _HYEONG_MAP.get(month_ji, [])
    return [b for b in natal_branches if b in targets]


def _check_ilgan_keuk(month_gan: str, day_gan: str) -> bool:
    """월간이 일간을 극하는지 확인."""
    return _GAN_克.get(month_gan) == day_gan


def _get_month_sipsin(month_row: Dict[str, Any]) -> str:
    """월운 row에서 이달 십신 추출."""
    sipsin = month_row.get("sipsin") or {}
    return str(sipsin.get("stem") or "").strip()


def detect_life_events(
    packed: Dict[str, Any],
    month_row: Dict[str, Any],
    *,
    seed: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    월운 row 하나에 대해 인생 사건 신호를 감지한다.

    Parameters
    ----------
    packed     : full_analyzer 전체 결과
    month_row  : monthly_reports 개별 월 dict
    seed       : 랜덤 시드

    Returns
    -------
    감지된 사건 신호 리스트. 각 항목:
        {
          event_id, label_ko, icon, category,
          signal, action, reframe, trigger_reason
        }
    """
    db = _db()
    events_db = db.get("life_events", {})
    engine_map = db.get("engine_mapping", {})
    shinsal_to_event = engine_map.get("shinsal_to_event", {})
    yukchink_to_event = engine_map.get("yukchink_to_event", {})

    # 기초 데이터 추출
    natal_branches = _get_natal_branches(packed)
    day_gan = _get_day_gan(packed)
    natal_shinsal = _get_shinsal_names(packed)
    month_ji = str(month_row.get("ji") or "").strip()
    month_gan = str(month_row.get("gan") or "").strip()
    month_sipsin = _get_month_sipsin(month_row)
    month_num = int(month_row.get("month") or 1)
    _seed = seed if seed is not None else month_num * 13

    triggered_events: Dict[str, Dict[str, Any]] = {}

    def _add_event(event_id: str, reason: str) -> None:
        if event_id in triggered_events:
            triggered_events[event_id]["trigger_reasons"].append(reason)
            return
        entry = events_db.get(event_id)
        if not entry:
            return
        triggered_events[event_id] = {
            "event_id": event_id,
            "label_ko": entry.get("label_ko", ""),
            "icon": entry.get("icon", "⚠️"),
            "category": entry.get("category", "caution"),
            "signal": _pick(entry.get("signal_pool", []), _seed),
            "action": _pick(entry.get("action_pool", []), _seed + 1),
            "reframe": _pick(entry.get("reframe_pool", []), _seed + 2),
            "trigger_reasons": [reason],
        }

    # ── 1. 원국 신살 기반 감지 ─────────────────────────────────────
    for sal in natal_shinsal:
        event_ids = shinsal_to_event.get(sal, [])
        for eid in event_ids:
            _add_event(eid, f"원국신살:{sal}")

    # ── 2. 월간이 일간을 극하는 경우 → 건강 주의 ─────────────────────
    if month_gan and day_gan and _check_ilgan_keuk(month_gan, day_gan):
        _add_event("health_caution", f"월간{month_gan}이 일간{day_gan}을 극")

    # ── 3. 월지 충(沖) 기반 감지 ─────────────────────────────────────
    chung_branches = _check_chung(month_ji, natal_branches) if month_ji else []
    if chung_branches:
        # 충이 있는 기둥 파악
        pillars = packed.get("pillars") or {}
        for pillar_key in ["year", "month", "day", "hour"]:
            p = pillars.get(pillar_key) or {}
            p_ji = str(p.get("ji") or "").strip()
            if p_ji in chung_branches:
                # 해당 기둥의 십신 확인
                p_sipsin = ""
                sipsin_data = (packed.get("analysis") or {}).get("sipsin") or {}
                if isinstance(sipsin_data, dict):
                    profiles = sipsin_data.get("profiles") or {}
                    if isinstance(profiles, dict):
                        for key, val in profiles.items():
                            if pillar_key in key.lower() or key == pillar_key:
                                p_sipsin = str(val or "").strip()
                                break

                # 충 → 육친 이벤트 연결
                event_ids = yukchink_to_event.get(p_sipsin, [])
                for eid in event_ids:
                    _add_event(eid, f"월지{month_ji} → {pillar_key}주{p_ji} 충")

                # 일주 충 → 건강 주의
                if pillar_key == "day":
                    _add_event("health_caution", f"월지{month_ji}가 일지{p_ji}와 충")

    # ── 4. 월 십신 기반 육친 이벤트 ──────────────────────────────────
    if month_sipsin:
        event_ids = yukchink_to_event.get(month_sipsin, [])
        for eid in event_ids:
            # 충이 없어도 십신이 강하면 경미하게 표시
            # (월지 충이 있는 경우에만 강하게 표시하기 위해 별도 처리)
            # 여기서는 충이 있을 때만 추가 → 위에서 처리됨
            pass

    # ── 5. 공망 기반 ─────────────────────────────────────────────────
    gongmang_line = str(month_row.get("gongmangLine") or "")
    if gongmang_line and ("재" in gongmang_line or "관" in gongmang_line):
        if "재" in gongmang_line:
            _add_event("financial_risk", f"공망:{gongmang_line[:20]}")
        if "관" in gongmang_line:
            _add_event("legal_trouble", f"공망:{gongmang_line[:20]}")

    # ── 6. 오행 기반 신체 부위 주의 ──────────────────────────────────
    oheng_body = db.get("oheng_body_map", {})
    analysis = packed.get("analysis") or {}
    five_elements = analysis.get("five_elements_strength") or analysis.get("oheng_strength") or {}
    if isinstance(five_elements, dict):
        _oheng_ko = {"wood": "목", "fire": "화", "earth": "토", "metal": "금", "water": "수"}
        for en_key, ko_key in _oheng_ko.items():
            val = five_elements.get(en_key, 0)
            # 특정 오행이 0이거나 과다 (3이상) 이면 해당 장기 주의
            if val == 0 or float(val) >= 3.0:
                body_info = oheng_body.get(ko_key, {})
                sig = body_info.get("signal", "")
                if sig and "health_caution" not in triggered_events:
                    _add_event("health_caution", f"{ko_key}오행 불균형(강도:{val})")

    # ── A군: 이별 삼합 감지 ─────────────────────────────────────────
    _has_chung = bool(chung_branches)
    _has_hyeong = bool(_check_hyeong(month_ji, natal_branches)) if month_ji else False

    # 원진 실시간 계산 (월지 기준)
    _wonjin_target = _WONJIN_MAP.get(month_ji, "")
    _has_wonjin_month = bool(_wonjin_target and _wonjin_target in natal_branches)

    # 일지 충 여부 (부부궁 충)
    _day_ji = str((packed.get("pillars") or {}).get("day", {}).get("ji") or "")
    _has_day_chung = (_CHUNG_MAP.get(month_ji) == _day_ji) if (month_ji and _day_ji) else False

    _ibyeol_count = sum([_has_chung, _has_hyeong, _has_wonjin_month])
    if _ibyeol_count >= 2 or (_has_day_chung and _has_wonjin_month):
        _add_event("ibyeol_samhap",
                   f"충{'O' if _has_chung else 'X'}+형{'O' if _has_hyeong else 'X'}+원진{'O' if _has_wonjin_month else 'X'}")

    # ── A군: 삼총살 감지 ─────────────────────────────────────────────
    _dohwa_target = _DOHWA_TABLE.get(_day_ji, "")
    _has_dohwa = bool(_dohwa_target and (_dohwa_target == month_ji or _dohwa_target in natal_branches))

    _hongnyeom_target = _HONGNYEOM_TABLE.get(day_gan, "")
    _has_hongnyeom = bool(_hongnyeom_target and (
        _hongnyeom_target == month_ji or _hongnyeom_target in natal_branches))

    _samchong_count = sum([_has_dohwa, _has_hongnyeom, _has_wonjin_month])
    if _samchong_count >= 2:
        _add_event("samchongsal",
                   f"도화{'O' if _has_dohwa else 'X'}+홍염{'O' if _has_hongnyeom else 'X'}+원진{'O' if _has_wonjin_month else 'X'}")

    # ── A군: 상관견관 감지 ──────────────────────────────────────────
    _has_jeonggwan_in_natal = False
    sipsin_data = (packed.get("analysis") or {}).get("sipsin") or {}
    if isinstance(sipsin_data, dict):
        counts = sipsin_data.get("counts") or {}
        if isinstance(counts, dict):
            _has_jeonggwan_in_natal = float(counts.get("정관", 0)) >= 1.0

    if month_sipsin == "상관" and _has_jeonggwan_in_natal:
        _add_event("sangkwan_gyeonan", "상관(월십신)+정관(원국) 충극")

    # ── A군: 재성/관성 혼잡 감지 ──────────────────────────────────
    if isinstance(sipsin_data, dict):
        counts2 = sipsin_data.get("counts") or {}
        if isinstance(counts2, dict):
            _pyunjae = float(counts2.get("편재", 0))
            _jungjae = float(counts2.get("정재", 0))
            _pyungwan = float(counts2.get("편관", 0))
            _jungwan  = float(counts2.get("정관", 0))

            if _pyunjae + _jungjae >= 2.0:
                _add_event("jaeseong_honjap",
                           f"재성혼잡(편재{_pyunjae}+정재{_jungjae})")
            if _pyungwan + _jungwan >= 2.0:
                _add_event("gwanseong_honjap",
                           f"관성혼잡(편관{_pyungwan}+정관{_jungwan})")

    # ── 결과 정렬: caution 먼저, positive 나중 ───────────────────────
    result = sorted(
        triggered_events.values(),
        key=lambda x: (0 if x["category"] == "caution" else 1)
    )

    # ── B군: 삼재 월별 감지 ────────────────────────────────────────
    try:
        from engine.samjae_engine_v1 import build_samjae_result
        samjae = build_samjae_result(packed)
        if samjae.get("is_samjae"):
            stage = samjae.get("stage", "")
            # stage 값에 따라 분기
            if "입력" in str(stage) or "들" in str(stage) or stage == 3:
                _add_event("samjae_incoming", f"삼재진입(들삼재)")
            elif "끝" in str(stage) or "날" in str(stage) or stage == 1:
                _add_event("samjae_outgoing", f"삼재마무리(날삼재)")
            else:
                _add_event("samjae_mid", f"삼재진행중(눌삼재)")
    except Exception:
        pass

    # ── B군: 대운 흐름 감지 ─────────────────────────────────────────
    try:
        analysis = packed.get("analysis") or {}
        daewoon_flow = analysis.get("daewoon_flow") or analysis.get("current_daewoon_flow") or ""
        if daewoon_flow in ("rising_strong", "rising_building", "peak"):
            _add_event("daewoon_rising", f"대운상승({daewoon_flow})")
        elif daewoon_flow in ("transition", "challenge_growth"):
            _add_event("daewoon_challenge", f"대운전환({daewoon_flow})")
    except Exception:
        pass

    # 최대 3개만 반환 (너무 많으면 효과 희석)
    return result[:3]


def get_monthly_life_event_slots(
    packed: Dict[str, Any],
    month_row: Dict[str, Any],
    *,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    월운 row에 대한 인생 사건 슬롯 반환.

    Returns
    -------
    {
        "found": bool,
        "events": [{ event_id, label_ko, icon, category, signal, action, reframe }]
    }
    """
    events = detect_life_events(packed, month_row, seed=seed)
    return {
        "found": len(events) > 0,
        "events": events,
    }
