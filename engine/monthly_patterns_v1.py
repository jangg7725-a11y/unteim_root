# unteim/engine/monthly_patterns_v1.py
# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List, Optional


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
    다양한 키/형태를 허용해서 '십신 기세'를 숫자로 뽑는다.
    기대 형태(예시):
      report["analysis"]["ten_gods_strength"] = {"인성": 1.2, "관성": 0.8, ...}
    또는:
      report["analysis"]["ten_gods"] 안에 strength가 있을 수도 있음
    """
    cand = (
        _safe_get(report, "analysis.ten_gods_strength")
        or _safe_get(report, "analysis.ten_gods.strength")
        or _safe_get(report, "analysis.tengods_strength")
        or {}
    )
    if not isinstance(cand, dict):
        return {}
    out: Dict[str, float] = {}
    for k, v in cand.items():
        out[str(k)] = _to_num(v, 0.0)
    return out


def _pick_elements_bucket(report: Dict[str, Any]) -> Dict[str, float]:
    """
    오행 기세(월운/세운 반영된 총합이 있으면 최우선 사용)
    기대 형태(예시):
      report["analysis"]["five_elements_strength"] = {"목": 1.1, ...}
    """
    cand = (
        _safe_get(report, "analysis.five_elements_strength")
        or _safe_get(report, "analysis.elements_strength")
        or _safe_get(report, "analysis.five_elements.strength")
        or {}
    )
    if not isinstance(cand, dict):
        return {}
    out: Dict[str, float] = {}
    for k, v in cand.items():
        out[str(k)] = _to_num(v, 0.0)
    return out


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


def detect_month_patterns_v1(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    ✅ 절대 '에러'로 죽지 않게 설계
    - 존재하는 데이터만 읽어서 점수화
    - 없으면 조용히 low 또는 빈 리스트
    """
    tg = _pick_ten_gods_bucket(report)          # 인성/식상/관성/재성/비겁 등
    el = _pick_elements_bucket(report)          # 목/화/토/금/수

    # 충/형/해/합 등은 구현 형태가 제각각이라 "있으면 위험도 가산"만
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

    # 기본 점수(없으면 0)
    score_insung = _to_num(tg.get("인성"), 0.0) + _to_num(tg.get("정인"), 0.0) + _to_num(tg.get("편인"), 0.0)
    score_siksang = _to_num(tg.get("식상"), 0.0) + _to_num(tg.get("식신"), 0.0) + _to_num(tg.get("상관"), 0.0)
    score_gwansung = _to_num(tg.get("관성"), 0.0) + _to_num(tg.get("정관"), 0.0) + _to_num(tg.get("편관"), 0.0)
    score_jaeseong = _to_num(tg.get("재성"), 0.0) + _to_num(tg.get("정재"), 0.0) + _to_num(tg.get("편재"), 0.0)
    score_bigub = _to_num(tg.get("비겁"), 0.0) + _to_num(tg.get("비견"), 0.0) + _to_num(tg.get("겁재"), 0.0)

    # 위험 가산치(있을 때만)
    risk = 0.0
    if has_conflict:
        risk += 0.8
    if has_kongmang:
        risk += 0.6
    if has_shinsal_alert:
        risk += 0.6

    patterns: List[Dict[str, Any]] = []

    # 1) 시험/합격/평가(문서) 운: 인성 + 관성 조합이 유리
    exam_score = (score_insung * 0.9) + (score_gwansung * 0.6) - (risk * 0.3)
    patterns.append({
        "id": "exam_pass",
        "title": "시험/합격·평가 운",
        "level": _level(exam_score),
        "signals": ["인성↑", "관성 안정", "문서/자격 이슈 유리"],
        "summary": "공부·자격·서류·평가에서 성과가 나기 쉬운 달입니다." if exam_score >= 1.2 else "준비한 만큼 성과가 갈리는 달입니다. 기본기 점검이 핵심입니다.",
        "advice": ["루틴 고정", "서류/접수 마감 체크", "암기·정리 위주로 속도↑"],
        "score": round(exam_score, 2),
    })

    # 2) 승진/인정 운: 관성 중심 + 인성 보조
    promo_score = (score_gwansung * 1.0) + (score_insung * 0.4) - (risk * 0.35)
    patterns.append({
        "id": "promotion",
        "title": "승진·평가·책임 운",
        "level": _level(promo_score),
        "signals": ["관성↑", "책임/역할 증가", "평가 이벤트"],
        "summary": "책임이 늘고 성과가 드러나는 달입니다. 자리/직함 이슈가 생기기 쉽습니다." if promo_score >= 1.2 else "성과를 ‘보이게’ 만드는 전략이 중요한 달입니다.",
        "advice": ["보고·기록 강화", "약속/기한 준수", "상사/고객과 소통 간결하게"],
        "score": round(promo_score, 2),
    })

    # 3) 이동/이직/변동 운: 식상(움직임) + 비겁(환경 변화) + (충 있으면 가산)
    move_score = (score_siksang * 0.8) + (score_bigub * 0.4) + (0.7 if has_conflict else 0.0) - (risk * 0.2)
    patterns.append({
        "id": "move_change",
        "title": "이동·이직·변동 운",
        "level": _level(move_score),
        "signals": ["식상↑", "변동성↑", "이동/정리 이벤트"],
        "summary": "움직이면 풀리는 달입니다. 자리 이동/이직/업무 변동이 현실화되기 쉽습니다." if move_score >= 1.2 else "변동 욕구가 올라오지만, 조건 비교가 필요합니다.",
        "advice": ["조건표로 비교", "충동결정 금지(24시간 룰)", "이동 전 계약/문서 확인"],
        "score": round(move_score, 2),
    })

    # 4) 재물/손재 운: 재성↑이면 돈 흐름↑, 다만 비겁↑/리스크↑면 손재↑
    money_flow = (score_jaeseong * 0.9) - (score_bigub * 0.4) - (risk * 0.4)
    patterns.append({
        "id": "money",
        "title": "재물 흐름·손재 운",
        "level": _level(money_flow),
        "signals": ["재성↑", "지출/수입 이벤트", "거래/계약 주의"],
        "summary": "돈이 도는 달입니다. 수입 기회도 있지만 지출도 함께 커질 수 있습니다." if money_flow >= 1.2 else "현금흐름을 단단히 관리해야 하는 달입니다.",
        "advice": ["고정지출 점검", "큰 결제는 2번 확인", "계약은 문장 그대로 읽기"],
        "score": round(money_flow, 2),
    })

    # 5) 관계/인연·이별 운: 비겁↑이면 관계 사건↑, 리스크↑면 갈등/정리↑
    relation_score = (score_bigub * 0.8) + (0.6 if has_conflict else 0.0) - (risk * 0.25)
    patterns.append({
        "id": "relationship",
        "title": "인연·관계·이별 운",
        "level": _level(relation_score),
        "signals": ["비겁↑", "만남/정리 이벤트", "말 실수 주의"],
        "summary": "관계가 활발해지고 사건이 생기기 쉬운 달입니다. 새로운 인연/정리 모두 가능." if relation_score >= 1.2 else "관계를 유지·관리하는 태도가 중요한 달입니다.",
        "advice": ["감정 폭발 전에 시간 벌기", "문자/말을 짧게", "약속을 줄이고 질을 높이기"],
        "score": round(relation_score, 2),
    })

    # 6) 사고/관재/구설 운: 리스크(충/공망/신살경고) 중심
    accident_score = (risk * 1.2) + (_to_num(tg.get("상관"), 0.0) * 0.3) - (_to_num(tg.get("정관"), 0.0) * 0.2)
    patterns.append({
        "id": "accident_legal",
        "title": "사고·관재·구설 리스크",
        "level": _level(accident_score),
        "signals": ["충/형/해/공망/신살 경고", "구설/사고 주의"],
        "summary": "실수·충돌·구설이 커지기 쉬운 달입니다. 특히 문서/운전/말이 리스크 포인트입니다." if accident_score >= 1.2 else "크게 문제될 건 없지만, 기본 안전수칙이 도움이 됩니다.",
        "advice": ["운전/이동 여유시간", "서류/계약 2중확인", "논쟁거리 회피"],
        "score": round(accident_score, 2),
    })

    # 점수 숨기고 싶으면 여기서 score 필드 제거해도 됩니다(현재는 디버그용으로 유지)
    # UI/리포트에서는 level/summary/advice만 쓰면 됩니다.

    # low만 잔뜩이면 보기 안 좋을 수 있어서, 최소 mid 이상만 뽑는 옵션도 가능
    return patterns


def attach_month_patterns_v1(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    report dict에 extra.month_patterns로 붙여줌(항상 안전).
    """
    extra = report.get("extra")
    if not isinstance(extra, dict):
        extra = {}
        report["extra"] = extra

    extra["month_patterns"] = detect_month_patterns_v1(report)
    return report
