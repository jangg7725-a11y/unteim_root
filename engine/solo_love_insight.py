# -*- coding: utf-8 -*-
"""상대 사주 없이 — 본인 원국만으로 인연·썸 흐름 참고 문장 생성 (가능성·경향, 단정 금지)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Tuple

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None  # type: ignore[misc, assignment]

from engine.full_analyzer import analyze_full
from engine.sajuCalculator import calculate_saju


def _kr_counts(analysis: Dict[str, Any]) -> Dict[str, float]:
    fe = analysis.get("five_elements_count") or analysis.get("oheng", {}).get("counts") or {}
    if not isinstance(fe, dict):
        return {"목": 0.0, "화": 0.0, "토": 0.0, "금": 0.0, "수": 0.0}
    H = {"木": "목", "火": "화", "土": "토", "金": "금", "水": "수"}
    out = {"목": 0.0, "화": 0.0, "토": 0.0, "금": 0.0, "수": 0.0}
    for k, v in fe.items():
        kk = H.get(str(k), str(k))
        if kk in out:
            try:
                out[kk] += float(v or 0)
            except (TypeError, ValueError):
                pass
    return out


def _sipsin_group_counts(profiles: Dict[str, Any]) -> Dict[str, int]:
    g = {"비겁": 0, "식상": 0, "재성": 0, "관성": 0, "인성": 0}
    if not isinstance(profiles, dict):
        return g
    for name, raw in profiles.items():
        try:
            n = int(raw)
        except (TypeError, ValueError):
            continue
        if not n:
            continue
        k = str(name)
        if "비견" in k or "겁재" in k:
            g["비겁"] += n
        elif "식신" in k or "상관" in k:
            g["식상"] += n
        elif "편재" in k or "정재" in k:
            g["재성"] += n
        elif "편관" in k or "정관" in k:
            g["관성"] += n
        elif "편인" in k or "정인" in k:
            g["인성"] += n
    return g


def _max_key(d: Dict[str, int]) -> Tuple[str, int]:
    best_k, best_v = "", -1
    for k, v in d.items():
        if v > best_v:
            best_k, best_v = k, v
    return best_k, best_v


def _monthly_one_line(mf: Any, month: int) -> str:
    if not isinstance(mf, dict):
        return ""
    months = mf.get("months")
    if not isinstance(months, list):
        return ""
    for m in months:
        if not isinstance(m, dict):
            continue
        try:
            if int(m.get("month", 0)) == month:
                for key in ("oneLineConclusion", "overallFlow", "flow", "narrative"):
                    t = (m.get(key) or "").strip()
                    if t:
                        return t[:220] + ("…" if len(t) > 220 else "")
        except (TypeError, ValueError):
            continue
    return ""


def build_solo_love_insight(
    birth_str: str,
    gender: str,
    topic: str = "general",
) -> Dict[str, Any]:
    """
    topic: general | sseom | timing | emotion
    """
    topic = (topic or "general").strip().lower()
    if topic not in ("general", "sseom", "timing", "emotion"):
        topic = "general"

    pillars = calculate_saju(birth_str)
    full = analyze_full(pillars, birth_str=birth_str)
    if not isinstance(full, dict):
        full = {}

    analysis = full.get("analysis") if isinstance(full.get("analysis"), dict) else {}
    sipsin = analysis.get("sipsin") if isinstance(analysis.get("sipsin"), dict) else {}
    profiles = sipsin.get("profiles") if isinstance(sipsin.get("profiles"), dict) else {}
    sg = _sipsin_group_counts(profiles)
    top_name, top_val = _max_key(sg)
    counts = _kr_counts(analysis)

    weak_el = min(counts, key=lambda k: counts[k])
    strong_el = max(counts, key=lambda k: counts[k])

    if ZoneInfo:
        now = datetime.now(ZoneInfo("Asia/Seoul"))
    else:
        now = datetime.now()
    cm = now.month
    mf = full.get("monthly_fortune")
    monthly_line = _monthly_one_line(mf, cm)

    # 연애·감정 축 서술 (비겁/식상/재/관/인)
    if top_name == "식상" or sg["식상"] >= max(2, top_val):
        emotion_line = (
            "표현·감정이 드러나는 축이 상대적으로 강하게 보일 수 있어, "
            "인연은 상대적으로 말·행동으로 이어지기 쉬운 경향이 있을 수 있습니다."
        )
    elif top_name == "인성" or sg["인성"] >= max(2, top_val):
        emotion_line = (
            "내면·사유·정리 쪽 에너지가 비중 있게 보일 수 있어, "
            "인연은 상대적으로 천천히 깊어지는 패턴을 보일 수 있습니다."
        )
    elif top_name == "관성" or sg["관성"] >= max(2, top_val):
        emotion_line = (
            "책임·관계·규칙을 의식하는 축이 강하게 보일 수 있어, "
            "인연은 상대적으로 진지한 만남·약속으로 이어지기 쉬운 경향이 있을 수 있습니다."
        )
    elif top_name == "재성" or sg["재성"] >= max(2, top_val):
        emotion_line = (
            "현실·실속·조건을 함께 보는 축이 있을 수 있어, "
            "인연은 상대적으로 안정·실질을 고려하는 흐름으로 이어질 수 있습니다."
        )
    else:
        emotion_line = (
            "자기 주도·관계 균형을 함께 보는 축이 있을 수 있어, "
            "인연은 상대적으로 서로의 속도를 맞추는 과정이 중요해질 수 있습니다."
        )

    balance_line = (
        f"오행 분포(참고)상으로는 {strong_el} 기운이 상대적으로 두드러지고, "
        f"{weak_el} 쪽은 보완 여지가 있을 수 있습니다. 이는 성향·리듬을 읽는 참고용입니다."
    )

    pulls_in = (
        "지금은 ‘감정 표현 방식’과 ‘현실·조건의 무게’가 어떻게 맞물리는지에 따라 "
        "끌림의 형태가 달라질 수 있습니다. 위 십신 분포(경향)를 보면, "
        f"{emotion_line.strip()}"
    )

    likely_bond = (
        "상대 사주 없이 본인 원국만으로 보면, ‘들어올 인연’을 단정할 수는 없습니다. "
        "다만 지금의 기운은 "
        f"{weak_el}·{strong_el} 균형과 {top_name or '십신'} 축이 함께 작용하며, "
        "비슷한 리듬·비슷한 가치관을 가진 만남이 상대적으로 이어지기 쉬운 시기일 수 있습니다."
    )

    energy = (
        "연애 에너지(참고)는 ‘감정·표현·현실’의 비중이 어떻게 나뉘는지로 읽을 수 있습니다. "
        + emotion_line
    )

    if monthly_line:
        month_note = f"이번 달({cm}월) 월운 요약(참고): {monthly_line}"
    else:
        month_note = f"이번 달({cm}월) 월운 요약은 리포트 생성 시점·데이터에 따라 길이가 달라질 수 있습니다."

    # topic별 한 문장
    extra = ""
    if topic == "timing":
        extra = (
            "‘지금 연락/움직임’은 월운·감정 리듬이 함께 맞을 때 부담이 줄어드는 경향이 있을 수 있습니다. "
            "급한 결정보다는 짧은 한 번의 점검(상대·나의 상태)을 먼저 해 보는 편이 유리할 수 있습니다."
        )
    elif topic == "emotion":
        extra = (
            "‘지금 내 마음’은 감정·현실·책임을 동시에 고려하는 패턴이 겹치면 흔들릴 수 있습니다. "
            "한 줄로 정리하면, 오늘의 감정은 ‘방향’일 수 있고, ‘결론’이 아닐 수 있습니다."
        )
    elif topic == "sseom":
        extra = (
            "썸·초기 관계에서는 상대 사주를 모를 때가 많습니다. "
            "이때는 본인 원국의 ‘감정·현실·책임’ 비중을 먼저 이해하고, "
            "상대의 속도를 확인하는 대화가 도움이 될 수 있습니다."
        )

    summary = (
        "본인 사주만으로 본 인연·연애 흐름 참고 요약입니다. "
        "상대 정보가 없어도 원국의 오행·십신 분포·월운 흐름을 바탕으로 경향을 짚어 봅니다."
    )

    disclaimer = (
        "이 내용은 참고 가능성·경향이며, 관계·미래를 단정할 수 없습니다. "
        "법·의료·투자 등 전문 판단을 대체하지 않습니다."
    )

    return {
        "summary": summary,
        "pullsIn": pulls_in,
        "likelyBond": likely_bond,
        "energy": energy,
        "balanceNote": balance_line,
        "monthlyFlow": month_note,
        "topicNote": extra,
        "disclaimer": disclaimer,
        "topic": topic,
        "meta": {
            "gender": gender,
            "weakElement": weak_el,
            "strongElement": strong_el,
            "sipsinTopGroup": top_name,
            "sipsinGroups": sg,
        },
    }
