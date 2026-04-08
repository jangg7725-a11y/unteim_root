# unteim/engine/monthly_patterns_v1_1.py
# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


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


def _pick_ten_gods_bucket(report: Dict[str, Any]) -> Dict[str, float]:
    """
    analysis.ten_gods_strength(권장) 우선.
    """
    cand = (
        _safe_get(report, "analysis.ten_gods_strength")
        or _safe_get(report, "analysis.ten_gods.strength")
        or _safe_get(report, "analysis.tengods_strength")
        or {}
    )
    if not isinstance(cand, dict):
        return {}
    return {str(k): _to_num(v, 0.0) for k, v in cand.items()}


def _pick_elements_bucket(report: Dict[str, Any]) -> Dict[str, float]:
    cand = (
        _safe_get(report, "analysis.five_elements_strength")
        or _safe_get(report, "analysis.elements_strength")
        or _safe_get(report, "analysis.five_elements.strength")
        or {}
    )
    if not isinstance(cand, dict):
        return {}
    return {str(k): _to_num(v, 0.0) for k, v in cand.items()}


def _has_flag(report: Dict[str, Any], *paths: str) -> bool:
    for p in paths:
        v = _safe_get(report, p)
        if isinstance(v, bool) and v:
            return True
        if isinstance(v, (list, dict)) and v:
            return True
        if isinstance(v, str) and v.strip():
            return True
    return False


def _level(score: float) -> str:
    if score >= 2.2:
        return "high"
    if score >= 1.2:
        return "mid"
    return "low"


def _normalize_ji(x: Any) -> Optional[str]:
    if x is None:
        return None
    s = str(x).strip()
    if not s:
        return None
    return s


def _get_month_branch(report: Dict[str, Any]) -> Optional[str]:
    ji = (
        _safe_get(report, "pillars.month.ji")
        or _safe_get(report, "analysis.pillars.month.ji")
        or _safe_get(report, "analysis.month.ji")
        or _safe_get(report, "analysis.month_branch")
    )
    return _normalize_ji(ji)


def _get_yong_hee_gi_elements(report: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    fav: List[str] = []
    unfav: List[str] = []

    yong = _safe_get(report, "analysis.yongshin") or _safe_get(report, "analysis.yong_sin")
    hee = _safe_get(report, "analysis.heesin") or _safe_get(report, "analysis.hee_sin")
    gi = _safe_get(report, "analysis.gisin") or _safe_get(report, "analysis.gi_sin")
    yhg = _safe_get(report, "analysis.yong_hee_gi") or _safe_get(report, "analysis.yongheegi")

    def _pull(obj, keys) -> List[str]:
        if not isinstance(obj, dict):
            return []
        for k in keys:
            v = obj.get(k)
            if isinstance(v, str) and v.strip():
                return [v.strip()]
            if isinstance(v, list):
                return [str(x).strip() for x in v if str(x).strip()]
        return []

    fav += _pull(yong, ["elements", "element", "fav", "favorable"])
    fav += _pull(hee, ["elements", "element", "fav", "favorable"])
    unfav += _pull(gi, ["elements", "element", "unfav", "unfavorable"])

    if isinstance(yhg, dict):
        fav += _pull(yhg, ["favorable", "fav", "good", "support"])
        unfav += _pull(yhg, ["unfavorable", "unfav", "bad", "avoid"])

    fav = list(dict.fromkeys([x for x in fav if x]))
    unfav = list(dict.fromkeys([x for x in unfav if x]))
    return fav, unfav


def _month_branch_triggers(month_ji: Optional[str]) -> Dict[str, bool]:
    if not month_ji:
        return {
            "peach_blossom": False,
            "mobility": False,
            "clash_risk": False,
            "earth_heavy": False,
        }

    peach = month_ji in {"子", "午", "卯", "酉"}           # 도화
    mobility = month_ji in {"寅", "申", "巳", "亥"}        # 역마
    clash = month_ji in {"子", "午", "卯", "酉", "寅", "申", "巳", "亥"}  # 충/사고감
    earth = month_ji in {"辰", "戌", "丑", "未"}           # 토 과다 느낌

    return {
        "peach_blossom": peach,
        "mobility": mobility,
        "clash_risk": clash,
        "earth_heavy": earth,
    }


def _tone_by_yonghee(
    score: float,
    fav_elems: List[str],
    unfav_elems: List[str],
    elements_bucket: Dict[str, float],
) -> Tuple[float, str, List[str]]:
    fav_strength = sum(_to_num(elements_bucket.get(e), 0.0) for e in fav_elems)
    unf_strength = sum(_to_num(elements_bucket.get(e), 0.0) for e in unfav_elems)

    adj = 0.0
    sig: List[str] = []

    if fav_elems:
        boost = min(0.6, fav_strength * 0.15)
        adj += boost
        if boost > 0.15:
            sig.append("용/희신 기세↑")

    if unfav_elems:
        drop = min(0.7, unf_strength * 0.18)
        adj -= drop
        if drop > 0.15:
            sig.append("기신 기세↑(무리 금지)")

    new_score = score + adj

    if new_score >= 1.6 and adj >= 0:
        tone = "good"
    elif new_score >= 1.2:
        tone = "neutral"
    else:
        tone = "caution"

    return new_score, tone, sig


def apply_tengods_strength_to_month_patterns_v1(
    report: Dict[str, Any],
    patterns: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    ✅ [C-v1] 십신 강약(analysis.ten_gods_strength: 0~1)을
    월운 패턴 score에 '추가 보정'으로 반영한다.

    주의:
    - 이 함수는 detect_month_patterns_v1_1() 마지막에서 딱 1번만 호출한다.
    - detect 내부에서 이미 보정했다면, 그 보정은 제거해야 한다(중복 방지).
    """
    tg = _safe_get(report, "analysis.ten_gods_strength") or {}
    if not isinstance(tg, dict):
        return patterns

    for p in patterns:
        if not isinstance(p, dict):
            continue
        pid = str(p.get("id") or "")
        score = _to_num(p.get("score"), 0.0)

        # 관성/인성: 승진/시험
        if pid in {"promotion", "exam_pass"}:
            score += _to_num(tg.get("관성"), 0.0) * 0.6
            score += _to_num(tg.get("인성"), 0.0) * 0.3
            sigs = p.get("signals")
            if isinstance(sigs, list) and "관성/인성 강약 반영(+)" not in sigs:
                sigs.append("관성/인성 강약 반영(+)")

        # 재성: 재물
        if pid == "money":
            score += _to_num(tg.get("재성"), 0.0) * 0.6

        # 비겁: 관계
        if pid == "relationship":
            score += _to_num(tg.get("비겁"), 0.0) * 0.5

        # 식상: 이동/변동
        if pid == "move_change":
            score += _to_num(tg.get("식상"), 0.0) * 0.5

        # 상관: 사고/구설(리스크 강화)
        if pid == "accident_legal":
            score += _to_num(tg.get("상관"), 0.0) * 0.4
            # ✅ 디버그/가시화: apply가 실제로 돌았는지 signals에 표시(중복 방지)


        if score != _to_num(p.get("score"), 0.0):
            sigs = p.get("signals")
            if not isinstance(sigs, list):
                sigs = []
                p["signals"] = sigs
            if "십신강약-apply반영" not in sigs:
                sigs.append("십신강약-apply반영")

        p["score"] = round(score, 2)

        # score 바뀌었으니 level도 재계산
        p["level"] = _level(_to_num(p.get("score"), 0.0))

    return patterns


def detect_month_patterns_v1_1(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    tg = _pick_ten_gods_bucket(report)
    el = _pick_elements_bucket(report)

    has_conflict = _has_flag(
        report,
        "analysis.hyeongchung",
        "analysis.clashes",
        "analysis.conflicts",
        "analysis.shape_conflict",
        "analysis.hyeong_chung_hap",
    )
    has_kongmang = _has_flag(report, "analysis.kongmang", "analysis.kong_mang")
    has_shinsal_alert = _has_flag(report, "analysis.shinsal.alerts", "analysis.shinsal.warnings")

    month_ji = _get_month_branch(report)
    tr = _month_branch_triggers(month_ji)

    fav_elems, unfav_elems = _get_yong_hee_gi_elements(report)

    # 십신 점수(없으면 0) - raw score (엔진마다 키가 다를 수 있어 넉넉히 합산)
    score_insung = _to_num(tg.get("인성"), 0.0) + _to_num(tg.get("정인"), 0.0) + _to_num(tg.get("편인"), 0.0)
    score_siksang = _to_num(tg.get("식상"), 0.0) + _to_num(tg.get("식신"), 0.0) + _to_num(tg.get("상관"), 0.0)
    score_gwansung = _to_num(tg.get("관성"), 0.0) + _to_num(tg.get("정관"), 0.0) + _to_num(tg.get("편관"), 0.0)
    score_jaeseong = _to_num(tg.get("재성"), 0.0) + _to_num(tg.get("정재"), 0.0) + _to_num(tg.get("편재"), 0.0)
    score_bigub = _to_num(tg.get("비겁"), 0.0) + _to_num(tg.get("비견"), 0.0) + _to_num(tg.get("겁재"), 0.0)

    risk = 0.0
    if has_conflict:
        risk += 0.8
    if has_kongmang:
        risk += 0.6
    if has_shinsal_alert:
        risk += 0.6
    if tr["clash_risk"]:
        risk += 0.3

    patterns: List[Dict[str, Any]] = []

    def _pack(
        pid: str,
        title: str,
        base_score: float,
        base_signals: List[str],
        base_summary_good: str,
        base_summary_mid: str,
        base_summary_low: str,
        advice: List[str],
    ):
        # 1) 용/희/기신 보정
        adj_score, tone, ysig = _tone_by_yonghee(base_score, fav_elems, unfav_elems, el)
        sigs = list(base_signals) + list(ysig)

        # 2) 월지 트리거(해당 패턴과 연관된 경우만)
        if pid == "relationship" and tr["peach_blossom"]:
            adj_score += 0.35
            sigs.append("도화 기운(인연/매력)")

        if pid == "move_change" and tr["mobility"]:
            adj_score += 0.35
            sigs.append("역마 기운(이동/변동)")

        if pid == "accident_legal" and (tr["clash_risk"] or tr["earth_heavy"]):
            adj_score += 0.25
            if tr["earth_heavy"]:
                sigs.append("토기운 무거움(정체/컨디션)")

        lvl = _level(adj_score)

        # 톤 정교화
        if pid in {"relationship", "move_change"} and lvl in {"mid", "high"}:
            tone = "good" if tone != "caution" else tone
        if pid == "accident_legal" and lvl != "low":
            tone = "caution"

        # summary 선택
        if lvl == "high":
            summary = base_summary_good
        elif lvl == "mid":
            summary = base_summary_mid
        else:
            summary = base_summary_low

        if tone == "caution":
            summary = summary.rstrip() + " 무리하면 역효과가 날 수 있어 속도 조절이 필요합니다."

        obj = {
            "id": pid,
            "title": title,
            "level": lvl,
            "tone": tone,  # good | neutral | caution
            "signals": sigs,
            "summary": summary,
            "advice": advice,
            "score": round(adj_score, 2),
        }
        if month_ji:
            obj["month_branch"] = month_ji
        if fav_elems or unfav_elems:
            obj["yonghee"] = {"favorable": fav_elems, "unfavorable": unfav_elems}
        return obj

    # 1) 시험/합격
    exam_score = (score_insung * 0.9) + (score_gwansung * 0.6) - (risk * 0.3)
    patterns.append(_pack(
        "exam_pass",
        "시험/합격·평가 운",
        exam_score,
        ["인성↑", "관성 안정", "문서/자격 이슈"],
        "공부·자격·서류·평가에서 성과가 크게 나기 쉬운 달입니다. 집중이 곧 결과로 연결됩니다.",
        "준비한 만큼 성과가 드러나는 달입니다. 정리·복습의 힘이 커집니다.",
        "기초를 다지는 달입니다. 방향만 잡아도 다음 달 성과가 달라집니다.",
        ["루틴 고정", "서류/접수 마감 체크", "암기·정리 위주로 속도↑"],
    ))

    # 2) 승진/평가
    promo_score = (score_gwansung * 1.0) + (score_insung * 0.4) - (risk * 0.35)
    patterns.append(_pack(
        "promotion",
        "승진·평가·책임 운",
        promo_score,
        ["관성↑", "책임/역할 증가", "평가 이벤트"],
        "책임이 커지며 성과가 눈에 띄는 달입니다. 자리/직함의 변화 가능성이 큽니다.",
        "성과를 보이게 만드는 전략이 중요한 달입니다. 보고·기록이 곧 실력입니다.",
        "무리한 확장은 피하고 기본을 지키는 달입니다. 실수 방지가 1순위입니다.",
        ["보고·기록 강화", "약속/기한 준수", "상사/고객과 소통 간결하게"],
    ))

    # 3) 이동/이직/변동
    move_score = (score_siksang * 0.8) + (score_bigub * 0.4) + (0.7 if has_conflict else 0.0) - (risk * 0.2)
    patterns.append(_pack(
        "move_change",
        "이동·이직·변동 운",
        move_score,
        ["식상↑", "변동성↑", "정리/이동 이벤트"],
        "움직이면 풀리는 달입니다. 자리 이동·이직·업무 변동이 유리하게 전개될 수 있습니다.",
        "변동 욕구가 올라옵니다. 조건을 숫자로 비교하면 답이 빨리 나옵니다.",
        "성급한 이동은 손해가 될 수 있습니다. 계약·조건을 먼저 고정하세요.",
        ["조건표로 비교", "충동결정 금지(24시간 룰)", "이동 전 계약/문서 확인"],
    ))

    # 4) 재물/손재
    money_flow = (score_jaeseong * 0.9) - (score_bigub * 0.4) - (risk * 0.4)
    patterns.append(_pack(
        "money",
        "재물 흐름·손재 운",
        money_flow,
        ["재성↑", "지출/수입 이벤트", "거래/계약 주의"],
        "돈이 도는 달입니다. 수입 기회가 커지고 ‘현금화’가 되는 흐름이 들어옵니다.",
        "수입과 지출이 함께 커질 수 있습니다. 흐름을 잡으면 남는 달이 됩니다.",
        "현금흐름 방어가 중요한 달입니다. 한 번의 큰 지출이 피로로 남을 수 있습니다.",
        ["고정지출 점검", "큰 결제는 2번 확인", "계약은 문장 그대로 읽기"],
    ))

    # 5) 인연/관계·이별
    relation_score = (score_bigub * 0.8) + (0.6 if has_conflict else 0.0) - (risk * 0.25)
    patterns.append(_pack(
        "relationship",
        "인연·관계·이별 운",
        relation_score,
        ["비겁↑", "만남/정리 이벤트", "말 실수 주의"],
        "관계가 활발해지고 인연 이벤트가 강하게 들어옵니다. 새 만남도, 큰 정리도 가능합니다.",
        "관계를 유지·관리하는 태도가 중요한 달입니다. 말의 온도 조절이 운을 바꿉니다.",
        "오해가 쌓이기 쉬운 달입니다. 감정으로 밀어붙이면 관계 손실이 생길 수 있습니다.",
        ["감정 폭발 전에 시간 벌기", "문자/말을 짧게", "약속을 줄이고 질을 높이기"],
    ))

    # 6) 사고/관재/구설
    accident_score = (risk * 1.2) + (_to_num(tg.get("상관"), 0.0) * 0.3) - (_to_num(tg.get("정관"), 0.0) * 0.2)
    patterns.append(_pack(
        "accident_legal",
        "사고·관재·구설 리스크",
        accident_score,
        ["충/형/해/공망/신살 경고", "구설/사고 주의"],
        "실수·충돌·구설이 크게 번지기 쉬운 달입니다. 문서·운전·말이 리스크 포인트입니다.",
        "기본 안전수칙만 지켜도 피하는 달입니다. ‘한 번 더 확인’이 운을 지켜줍니다.",
        "크게 문제될 건 없어도 방심이 변수입니다. 안전·문서·대화에서 기준을 지키세요.",
        ["운전/이동 여유시간", "서류/계약 2중확인", "논쟁거리 회피"],
    ))

    # ✅ C-v1: 십신 강약(ten_gods_strength) 기반 보정은 여기서 딱 1번만!
    patterns = apply_tengods_strength_to_month_patterns_v1(report, patterns)

    return patterns

def _make_top3_cards_from_patterns(patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    patterns(list[dict])에서 score 기준 내림차순 Top3를 카드 데이터로 만든다.
    1위(is_main=True)만 강조 플래그를 준다.
    """
    safe = [p for p in patterns if isinstance(p, dict)]
    ranked = sorted(safe, key=lambda p: _to_num(p.get("score"), 0.0), reverse=True)[:3]

    cards: List[Dict[str, Any]] = []
    for idx, p in enumerate(ranked):
        cards.append({
            "rank": idx + 1,
            "id": str(p.get("id") or ""),
            "title": str(p.get("title") or ""),
            "score": round(_to_num(p.get("score"), 0.0), 2),
            "tone": str(p.get("tone") or ""),
            "signals": list(p.get("signals") or []),
            "is_main": (idx == 0),
        })
    return cards


def attach_month_patterns_v1_1(report: Dict[str, Any]) -> Dict[str, Any]:
    extra = report.get("extra")
    if not isinstance(extra, dict):
        extra = {}
        report["extra"] = extra
    extra["month_patterns"] = detect_month_patterns_v1_1(report)
    extra["monthly_top3_cards"] = _make_top3_cards_from_patterns(extra["month_patterns"])
    extra["month_patterns_version"] = "v1.1"
    return report
