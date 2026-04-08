# unteim/engine/flow_interactions_v1.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


# -----------------------------
# 0) 유틸
# -----------------------------
def _as_dict(v: Any) -> Dict[str, Any]:
    return v if isinstance(v, dict) else {}

def _as_list(v: Any) -> List[Any]:
    return v if isinstance(v, list) else []

def _pick_top_k(items: List[str], k: int = 2) -> List[str]:
    out: List[str] = []
    for x in items:
        if x and x not in out:
            out.append(x)
        if len(out) >= k:
            break
    return out


# -----------------------------
# 1) 사건 영역 매핑(상담 언어)
# -----------------------------
SIPSIN_TO_DOMAIN = {
    # 비겁
    "비견": ["자립", "경쟁", "관계"], "겁재": ["경쟁", "손재", "갈등"],
    # 식상
    "식신": ["결과", "생산", "건강"], "상관": ["표현", "구설", "충돌"],
    # 재성
    "정재": ["수입", "지출", "문서"], "편재": ["기회", "거래", "이동"],
    # 관성
    "정관": ["직장", "평가", "문서"], "편관": ["압박", "경쟁", "리스크"],
    # 인성
    "정인": ["학습", "회복", "보호"], "편인": ["직관", "연구", "변동"],
}

LABEL_TEXT = {
    "BOOST": "강화",
    "CLASH": "충돌",
    "DRAIN": "무력화",
    "AMPLIFY": "증폭",
}


# -----------------------------
# 2) 상호작용 판정 규칙 (핵심)
# -----------------------------
def _extract_yhg(base: Dict[str, Any]) -> Tuple[Optional[str], List[str], List[str]]:
    """
    base에서 yongshin/heesin/gisin을 최대한 방어적으로 추출.
    프로젝트마다 키가 조금씩 다를 수 있어 '있는 것 중'을 씁니다.
    """
    y = base.get("yongshin") or base.get("ysh") or base.get("yongshin_axis") or {}
    y = _as_dict(y)

    yong = y.get("yongshin") or y.get("yong") or y.get("main")
    hee = y.get("heesin") or y.get("hee") or y.get("support") or []
    gis = y.get("gisin") or y.get("gi") or y.get("avoid") or []

    if isinstance(hee, str): hee = [hee]
    if isinstance(gis, str): gis = [gis]
    return (yong if isinstance(yong, str) else None, _as_list(hee), _as_list(gis))

def _extract_sipsin_state(base: Dict[str, Any]) -> Dict[str, Any]:
    """
    십신 과다/부족 판단은 이미 sipsin 모듈에서 만들었거나,
    만들 예정인 summary를 받는 형태가 가장 안정적.
    여기서는 방어적으로 dominant/excess/lack를 기대합니다.
    """
    s = base.get("sipsin") or {}
    s = _as_dict(s)
    summary = s.get("summary") or s.get("distribution") or s.get("state") or {}
    summary = _as_dict(summary)

    return {
        "dominant": summary.get("dominant"),
        "excess": _as_list(summary.get("excess")),
        "lack": _as_list(summary.get("lack")),
    }

def _extract_gongmang(base: Dict[str, Any]) -> List[str]:
    """
    공망이 어디에 걸렸는지(십신/지지/주 등) 다양한 방식 가능.
    최소: 리스트면 그대로, dict면 items 중 'targets'를 사용.
    """
    km = base.get("kongmang") or base.get("gongmang") or {}
    if isinstance(km, list):
        return [str(x) for x in km]
    km = _as_dict(km)
    targets = km.get("targets") or km.get("items") or []
    return [str(x) for x in _as_list(targets)]

def _extract_12fs(base: Dict[str, Any]) -> Dict[str, str]:
    """
    십이운성: 지지별 라벨을 dict로 기대 (예: {"year":"제왕",...})
    """
    tf = base.get("twelve_fortunes") or base.get("12fs") or {}
    tf = _as_dict(tf)
    # 어떤 구현은 {"items":[...]} 형태일 수 있음 → 여기서는 dict만 우선 처리
    return {k: str(v) for k, v in tf.items() if isinstance(v, (str, int))}

def _extract_shinsal(base: Dict[str, Any]) -> List[str]:
    sh = base.get("shinsal") or {}
    if isinstance(sh, list):
        return [str(x) for x in sh]
    sh = _as_dict(sh)
    items = sh.get("items") or sh.get("names") or []
    # items가 dict 리스트면 name 키가 있을 수 있음
    out: List[str] = []
    for it in _as_list(items):
        if isinstance(it, str):
            out.append(it)
        elif isinstance(it, dict):
            n = it.get("name") or it.get("label")
            if n:
                out.append(str(n))
    return out

def _luck_to_hits(luck: Dict[str, Any]) -> Dict[str, Any]:
    """
    대운/세운/월운 각각에서 강조되는 십신/오행을 표준 스키마로 정리.
    - 이미 엔진에 결과가 있으면 그 키를 그대로 매핑만 하면 됩니다.
    """
    luck = _as_dict(luck)

    # 예시 스키마:
    # {"theme_sipsin": "정관", "theme_elements": ["금"], "repeat_sipsin": ["상관"], "notes": "..."}
    return {
        "theme_sipsin": luck.get("theme_sipsin") or luck.get("dominant_sipsin"),
        "theme_elements": _as_list(luck.get("theme_elements")),
        "repeat_sipsin": _as_list(luck.get("repeat_sipsin")),
        "notes": luck.get("notes") or "",
    }

def judge_interactions(
    base: Dict[str, Any],
    daewoon: Dict[str, Any],
    sewun: Dict[str, Any],
    wolwoon: Dict[str, Any],
) -> Dict[str, Any]:
    """
    반환:
      {
        "labels": [{"code":"CLASH","why":"...","evidence":[...]}...],
        "key_domains": ["직장","문서"],
        "core_summary": "한 문단"
      }
    """
    yong, hee, gis = _extract_yhg(base)
    s_state = _extract_sipsin_state(base)
    gongmang_targets = _extract_gongmang(base)
    tf = _extract_12fs(base)
    shinsal = _extract_shinsal(base)

    d = _luck_to_hits(daewoon)
    y = _luck_to_hits(sewun)
    m = _luck_to_hits(wolwoon)

    labels: List[Dict[str, Any]] = []
    evidence: List[str] = []

    # 1) BOOST: 운의 중심 십신이 용/희신 축과 맞으면 강화
    for item, tag in [(d, "대운"), (y, "세운"), (m, "월운")]:
        ts = item.get("theme_sipsin")
        if ts and (ts == yong or ts in hee):
            labels.append({"code": "BOOST", "why": f"{tag}의 중심 흐름({ts})이 용/희신과 맞음", "evidence": [f"{tag}:theme_sipsin={ts}"]})
            evidence.append(f"{tag} 용/희신 정합")

        if ts and ts in gis:
            labels.append({"code": "CLASH", "why": f"{tag}의 중심 흐름({ts})이 기신을 자극", "evidence": [f"{tag}:theme_sipsin={ts}"]})
            evidence.append(f"{tag} 기신 자극")

    # 2) DRAIN: 공망이 핵심축(용신/중심십신)에 걸렸으면 무력화
    # 공망 타겟 문자열 안에 yong / dominant 등이 포함되는 형태(프로젝트마다 다름) 가정
    dom = s_state.get("dominant")
    if yong and any(yong in t for t in gongmang_targets):
        labels.append({"code": "DRAIN", "why": "용신이 공망에 걸려 체감/결과가 약해질 수 있음", "evidence": ["gongmang targets include yongshin"]})
        evidence.append("용신 공망")
    if dom and any(str(dom) in t for t in gongmang_targets):
        labels.append({"code": "DRAIN", "why": "중심 십신이 공망에 걸려 힘이 빠질 수 있음", "evidence": ["gongmang targets include dominant sipsin"]})
        evidence.append("중심십신 공망")

    # 3) AMPLIFY: 반복 작동 + 운성 강 + 신살(귀인/백호 등)로 체감 증폭
    repeats = []
    repeats += _as_list(d.get("repeat_sipsin"))
    repeats += _as_list(y.get("repeat_sipsin"))
    repeats += _as_list(m.get("repeat_sipsin"))
    repeats = [str(x) for x in repeats if x]

    if repeats:
        labels.append({"code": "AMPLIFY", "why": f"같은 십신 이슈가 반복 작동({', '.join(_pick_top_k(repeats, 3))})", "evidence": ["repeat_sipsin present"]})
        evidence.append("반복 작동")

    # 운성 증폭(매우 거칠게: 제왕/임관이 있으면 체감↑, 쇠/병/사/절이면 체감↓)
    strong_12fs = [v for v in tf.values() if v in ("제왕", "임관", "관대", "장생")]
    weak_12fs = [v for v in tf.values() if v in ("쇠", "병", "사", "묘", "절")]
    if strong_12fs:
        labels.append({"code": "AMPLIFY", "why": f"십이운성 강한 구간({', '.join(_pick_top_k(strong_12fs, 2))})으로 체감이 커질 수 있음", "evidence": ["twelve_fortunes strong"]})
        evidence.append("운성 강")
    if weak_12fs:
        labels.append({"code": "DRAIN", "why": f"십이운성 약한 구간({', '.join(_pick_top_k(weak_12fs, 2))})으로 결과가 늦거나 약할 수 있음", "evidence": ["twelve_fortunes weak"]})
        evidence.append("운성 약")

    # 신살 증폭(귀인/백호/역마/도화 등은 프로젝트별 이름 다름 → 문자열 포함으로 처리)
    if any("귀인" in x for x in shinsal):
        labels.append({"code": "AMPLIFY", "why": "귀인 계열 신살로 도움/연결이 강해질 수 있음", "evidence": ["shinsal contains 귀인"]})
        evidence.append("귀인")
    if any(("백호" in x or "겁" in x or "혈" in x) for x in shinsal):
        labels.append({"code": "CLASH", "why": "강한 리스크 계열 신살이 있어 무리하면 충돌/손상 가능", "evidence": ["shinsal risk"]})
        evidence.append("리스크 신살")
    if any("역마" in x for x in shinsal):
        labels.append({"code": "AMPLIFY", "why": "역마 계열로 이동/변동 이슈가 사건화되기 쉬움", "evidence": ["shinsal contains 역마"]})
        evidence.append("역마")

    # 영역(도메인) 우선순위: (운의 중심 십신, base dominant, repeats)로 결정
    domains: List[str] = []
    for ts in [d.get("theme_sipsin"), y.get("theme_sipsin"), m.get("theme_sipsin"), dom]:
        if ts and ts in SIPSIN_TO_DOMAIN:
            domains += SIPSIN_TO_DOMAIN[ts]
    # 반복 십신이 있으면 그 영역도 추가
    for rs in repeats[:3]:
        if rs in SIPSIN_TO_DOMAIN:
            domains += SIPSIN_TO_DOMAIN[rs]
    # 정리
    domains = _pick_top_k([x for x in domains if x], 3)

    return {
        "labels": labels,
        "key_domains": domains,
        "evidence": _pick_top_k(evidence, 6),
    }


# -----------------------------
# 3) 문장 생성(Flow Summary)
# -----------------------------
def build_flow_summary_v1(
    base: Dict[str, Any],
    daewoon: Dict[str, Any],
    sewun: Dict[str, Any],
    wolwoon: Dict[str, Any],
) -> Dict[str, Any]:
    """
    최종 반환:
      {
        "year_summary": "...(대운→세운→월운→제안 1문단)",
        "labels": [...],
        "key_domains": [...],
        "bullets": [...]
      }
    """
    base = _as_dict(base)
    inter = judge_interactions(base, daewoon, sewun, wolwoon)

    yong, hee, gis = _extract_yhg(base)
    dom = _extract_sipsin_state(base).get("dominant")

    d = _luck_to_hits(daewoon)
    y = _luck_to_hits(sewun)
    m = _luck_to_hits(wolwoon)

    # 핵심 라벨 2개만 (과잉 방지)
    main_labels = [x.get("code") for x in inter["labels"] if x.get("code")]
    main_labels = _pick_top_k(main_labels, 2)
    main_label_text = " · ".join(LABEL_TEXT.get(x, x) for x in main_labels) if main_labels else "흐름 정리"

    # 문장 1문단(상담형)
    parts: List[str] = []
    if dom:
        parts.append(f"타고난 구조의 중심은 {dom} 흐름이며")
    if yong or hee or gis:
        yhg_txt = []
        if yong: yhg_txt.append(f"용신은 {yong}")
        if hee: yhg_txt.append(f"희신은 {', '.join(_pick_top_k([str(x) for x in hee], 2))}")
        if gis: yhg_txt.append(f"기신은 {', '.join(_pick_top_k([str(x) for x in gis], 2))}")
        parts.append(", ".join(yhg_txt) + "으로 작동합니다.")

    if d.get("theme_sipsin") or d.get("theme_elements"):
        parts.append(f"현재 대운은 {d.get('theme_sipsin') or '특정'} 흐름이 인생의 큰 방향을 잡고")
    if y.get("theme_sipsin") or y.get("theme_elements"):
        parts.append(f"올해 세운은 {y.get('theme_sipsin') or '특정'} 테마가 겹치며")
    if m.get("theme_sipsin") or m.get("theme_elements"):
        parts.append(f"이번 달은 {m.get('theme_sipsin') or '특정'} 이슈로 사건이 구체화되기 쉽습니다.")

    # 라벨 기반 제안
    suggest: List[str] = []
    if "CLASH" in main_labels:
        suggest.append("충돌이 나기 쉬우니 말·계약·감정 결정을 ‘한 박자 늦추는’ 전략이 유리합니다.")
    if "BOOST" in main_labels:
        suggest.append("강화 흐름을 타면 성과가 빠르니 ‘핵심 1~2개 목표’에 집중하는 게 좋습니다.")
    if "DRAIN" in main_labels:
        suggest.append("체감이 약하거나 지연될 수 있어 ‘기록·문서·루틴’으로 결과를 붙잡는 방식이 필요합니다.")
    if "AMPLIFY" in main_labels:
        suggest.append("작은 일이 크게 체감될 수 있으니 확장보다 ‘리스크 관리/선택과 집중’이 안전합니다.")
    if not suggest:
        suggest.append("올해는 기본 구조를 안정적으로 쓰는 쪽이 유리합니다.")

    domains = inter.get("key_domains") or []
    if domains:
        suggest.append(f"특히 {', '.join(domains)} 영역에서 체감이 강해질 가능성이 큽니다.")

    year_summary = f"[{main_label_text}] " + " ".join([p for p in parts if p]).strip()
    if year_summary and not year_summary.endswith("."):
        year_summary += "."
    year_summary += " " + " ".join(suggest)

    # bullets (근거를 보여주면 신뢰도↑)
    bullets: List[str] = []
    for lb in inter["labels"][:6]:
        code = lb.get("code")
        why = lb.get("why")
        if code and why:
            bullets.append(f"- ({LABEL_TEXT.get(code, code)}) {why}")

    return {
        "year_summary": year_summary,
        "labels": inter["labels"],
        "key_domains": domains,
        "bullets": bullets,
        "evidence": inter.get("evidence", []),
    }
