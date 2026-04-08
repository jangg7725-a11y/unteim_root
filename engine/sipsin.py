# unteim/engine/sipsin.py
from __future__ import annotations

from typing import Any, Dict, List, Tuple, Optional

# -----------------------------
# 기본 데이터 (천간/지지/오행/음양)
# -----------------------------
# ---------------------------------------------------------------------
# normalize: 한자/한글/기타 표기 → 표준 한글(갑을병정… / 자축인묘…)
# ---------------------------------------------------------------------
STEM_TO_KOR = {
    # 한자 천간
    "甲": "갑", "乙": "을", "丙": "병", "丁": "정", "戊": "무",
    "己": "기", "庚": "경", "辛": "신", "壬": "임", "癸": "계",
    # 한글 천간(그대로)
    "갑": "갑", "을": "을", "병": "병", "정": "정", "무": "무",
    "기": "기", "경": "경", "신": "신", "임": "임", "계": "계",
}

BRANCH_TO_KOR = {
    # 한자 지지
    "子": "자", "丑": "축", "寅": "인", "卯": "묘", "辰": "진", "巳": "사",
    "午": "오", "未": "미", "申": "신", "酉": "유", "戌": "술", "亥": "해",
    # 한글 지지(그대로)
    "자": "자", "축": "축", "인": "인", "묘": "묘", "진": "진", "사": "사",
    "오": "오", "미": "미", "신": "신", "유": "유", "술": "술", "해": "해",
}

def _norm_stem(x: Any) -> str:
    if x is None:
        return ""
    t = str(x).strip()
    return STEM_TO_KOR.get(t, t)

def _norm_branch(x: Any) -> str:
    if x is None:
        return ""
    t = str(x).strip()
    return BRANCH_TO_KOR.get(t, t)


# 천간 -> 오행 (한자 + _norm_stem 한글 결과 모두 지원)
STEM_ELEM = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水",
    "갑": "木", "을": "木",
    "병": "火", "정": "火",
    "무": "土", "기": "土",
    "경": "金", "신": "金",
    "임": "水", "계": "水",
}

# 천간 -> 음양 (한자 + 한글)
# True=양, False=음 (same_polar 비교용)
STEM_YINYANG = {
    "甲": True,  "乙": False,
    "丙": True,  "丁": False,
    "戊": True,  "己": False,
    "庚": True,  "辛": False,
    "壬": True,  "癸": False,
    "갑": True, "을": False,
    "병": True, "정": False,
    "무": True, "기": False,
    "경": True, "신": False,
    "임": True, "계": False,
}

# 오행 상생 / 상극 (한자 오행 기준)
GEN = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}  # 생(내가 생하는 것)
CTL = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}  # 극(내가 극하는 것)


# -----------------------------
# 내부 유틸: pillars 읽기 (dataclass/ dict 모두 대응)
# -----------------------------
def _get_pillar(pillars: Any, key: str) -> Tuple[str, str]:
    """
    key: "year" | "month" | "day" | "hour"
    SajuPillars 구조(확정):
      - pillars.gan: list[str] 길이 4
      - pillars.ji:  list[str] 길이 4
      순서: [year, month, day, hour]
    return: (gan, ji)
    """
    if key not in ("year", "month", "day", "hour"):
        raise ValueError(f"[sipsin] invalid key: {key}")

    idx_map = {"year": 0, "month": 1, "day": 2, "hour": 3}
    idx = idx_map[key]

    def _as_pair(v: Any) -> Optional[Tuple[str, str]]:
        # ("갑","자") / ["갑","자"]
        if isinstance(v, (list, tuple)) and len(v) == 2:
            return _norm_stem(v[0]), _norm_branch(v[1])

        # {"gan":"갑","ji":"자"} 또는 {"stem":"갑","branch":"자"}
        if isinstance(v, dict):
            g = v.get("gan") if v.get("gan") is not None else v.get("stem")
            j = v.get("ji") if v.get("ji") is not None else v.get("branch")
            if g is not None and j is not None:
                return _norm_stem(g), _norm_branch(j)

        # GanJi 객체처럼 .gan / .ji
        g = getattr(v, "gan", None)
        j = getattr(v, "ji", None)
        if g is not None and j is not None:
            return _norm_stem(g), _norm_branch(j)

        return None

    # 0) SajuPillars(정석): gan/ji 리스트
    gan_obj = getattr(pillars, "gan", None)
    ji_obj = getattr(pillars, "ji", None)
    if isinstance(gan_obj, (list, tuple)) and isinstance(ji_obj, (list, tuple)):
        if len(gan_obj) >= 4 and len(ji_obj) >= 4:
            g = gan_obj[idx]
            j = ji_obj[idx]
            if g is not None and j is not None:
                return _norm_stem(g), _norm_branch(j)


    # 1) dict 형태: {"year": ("갑","자"), ...}
    if isinstance(pillars, dict):
        v = pillars.get(key)
        pair = _as_pair(v)
        if pair:
            return pair

        # 2) dict 형태: {"gan": {...}, "ji": {...}} 또는 {"gan":[...], "ji":[...]}
        gmap = pillars.get("gan")
        jmap = pillars.get("ji")

        # 2-1) gan/ji dict
        if isinstance(gmap, dict) and isinstance(jmap, dict):
            if key in gmap and key in jmap:
                return _norm_stem(gmap[key]), _norm_branch(jmap[key])

        # 2-2) gan/ji list
        if isinstance(gmap, (list, tuple)) and isinstance(jmap, (list, tuple)):
            if len(gmap) >= 4 and len(jmap) >= 4:
                return _norm_stem(gmap[idx]), _norm_branch(jmap[idx])

    # 3) 혹시 year/month/day/hour 자체가 속성으로 있는 경우
    if hasattr(pillars, key):
        pair = _as_pair(getattr(pillars, key))
        if pair:
            return pair


    raise ValueError(
        f"[sipsin] pillars에서 '{key}' 기둥을 읽을 수 없습니다. type={type(pillars)} "
        f"/ gan_type={type(gan_obj)} / ji_type={type(ji_obj)}"
    )


def _elem(stem: str) -> Optional[str]:
    """천간 -> 오행"""
    return STEM_ELEM.get(stem)


def _yy(stem: str) -> Optional[bool]:
    """천간 -> 음양"""
    return STEM_YINYANG.get(stem)


# =========================================
# 십신 판정 (천간-천간 기준)
# - 입력: day_stem(일간), other_stem(상대 천간)
# - 출력: 비견/겁재/식신/상관/정재/편재/정관/편관/정인/편인
# =========================================


def ten_god_stem(day_stem: str, other_stem: str) -> str:
    """
    일간(day_stem) 기준으로 타 천간(other_stem)의 십신을 반환.
    - 표기 통일: 입력은 반드시 '甲乙丙丁戊己庚辛壬癸'
    """
    de = _elem(day_stem)
    oe = _elem(other_stem)
    dy = _yy(day_stem)
    oy = _yy(other_stem)

    # 데이터 이상 방어
    if not de or not oe or dy is None or oy is None:
        return "미상"

    same_polar = (dy == oy)

    # 1) 비견/겁재 (같은 오행)
    if de == oe:
        return "비견" if same_polar else "겁재"

    # 2) 식신/상관 (내가 생하는 오행) : GEN[de] == oe
    if GEN.get(de) == oe:
        return "식신" if same_polar else "상관"

    # 3) 정재/편재 (내가 극하는 오행) : CTL[de] == oe
    if CTL.get(de) == oe:
        return "편재" if same_polar else "정재"

    # 4) 정관/편관 (나를 극하는 오행) : CTL[oe] == de  ★핵심
    if CTL.get(oe) == de:
        return "편관" if same_polar else "정관"

    # 5) 정인/편인 (나를 생하는 오행) : GEN[oe] == de  ★핵심
    if GEN.get(oe) == de:
        return "편인" if same_polar else "정인"

    return "미상"


# 기존 코드 호환용 별칭(이미 ten_god()를 쓰는 곳이 있으면 그대로 유지)
def ten_god(day_stem: str, target_stem: str) -> str:
    """
    호환 함수: ten_god(day_stem, target_stem) -> 십신
    (내부는 ten_god_stem()을 사용)
    """
    return ten_god_stem(day_stem, target_stem)

# ===============================
# 지장간(藏干) → 십신 연결 로직
# ===============================

HIDDEN_STEMS = {
    "子": [("癸", 1.0)],
    "丑": [("己", 1.0), ("癸", 0.6), ("辛", 0.3)],
    "寅": [("甲", 1.0), ("丙", 0.6), ("戊", 0.3)],
    "卯": [("乙", 1.0)],
    "辰": [("戊", 1.0), ("乙", 0.6), ("癸", 0.3)],
    "巳": [("丙", 1.0), ("戊", 0.6), ("庚", 0.3)],
    "午": [("丁", 1.0), ("己", 0.6)],
    "未": [("己", 1.0), ("丁", 0.6), ("乙", 0.3)],
    "申": [("庚", 1.0), ("壬", 0.6), ("戊", 0.3)],
    "酉": [("辛", 1.0)],
    "戌": [("戊", 1.0), ("辛", 0.6), ("丁", 0.3)],
    "亥": [("壬", 1.0), ("甲", 0.6)],
}

def hidden_stems_of_ji(ji: str):
    return HIDDEN_STEMS.get(ji, [])


def ten_god_from_hidden_stems(day_stem: str, ji: str):
    result = []
    for stem, weight in hidden_stems_of_ji(ji):
        tg = ten_god_stem(day_stem, stem)   # ✅ 십신판정 함수
        result.append({
            "hidden_stem": stem,
            "weight": weight,
            "ten_god": tg,
        })
    return result


# -----------------------------
# 지지 십신(지장간 기준)
# -----------------------------
def branch_ten_gods(day_stem: str, branch: str) -> Dict[str, str]:
    """
    지지의 지장간(본/중/여기)을 각각 십신으로 변환.
    """
    hs = HIDDEN_STEMS.get(branch, [])
    out: Dict[str, str] = {}
    if not hs:
        return out

    labels = ["본기", "중기", "여기"]
    for i, (stem, _w) in enumerate(hs[:3]):
        out[labels[i]] = ten_god(day_stem, stem)
    return out

# -----------------------------
# 메인: compute_sipsin (항상 채움)
# -----------------------------
def compute_sipsin(pillars: Any) -> Dict[str, Any]:
    """
    결과는 run_pdf_report.py가 바로 쓰기 좋게 dict로 반환.
    - profiles: 표에 넣을 '기둥별' 십신 요약
    - summary : 문장용 핵심 요약
    """
    y_g, y_j = _get_pillar(pillars, "year")
    m_g, m_j = _get_pillar(pillars, "month")
    d_g, d_j = _get_pillar(pillars, "day")
    h_g, h_j = _get_pillar(pillars, "hour")

    day_master = d_g  # 일간

    # 천간 십신(연/월/일/시)
    stem_map = {
        "연간": ten_god(day_master, y_g),
        "월간": ten_god(day_master, m_g),
        "일간": "일간(자기)" ,
        "시간": ten_god(day_master, h_g),
    }

    # 지지 십신(지장간 기반)
    branch_map = {
        "연지": branch_ten_gods(day_master, y_j),
        "월지": branch_ten_gods(day_master, m_j),
        "일지": branch_ten_gods(day_master, d_j),
        "시지": branch_ten_gods(day_master, h_j),
    }

    # 카운트(천간+지장간 모두)
    counts: Dict[str, int] = {}
    def _inc(k: str):
        if not k:
            return
        counts[k] = counts.get(k, 0) + 1

    for k, v in stem_map.items():
        if v not in ("일간(자기)", "미상"):
            _inc(v)

    for k, sub in branch_map.items():
        for _, v in sub.items():
            if v and v != "미상":
                _inc(v)

    # 핵심 요약(현실형 문장용)
    # - 많이 나온 십신 TOP3 뽑기
    top = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:3]
    top_str = ", ".join([f"{k}×{v}" for k, v in top]) if top else "데이터 부족"

    summary = {
        "day_master": day_master,
        "top": top_str,
        "stem": f"연간({stem_map['연간']}), 월간({stem_map['월간']}), 시간({stem_map['시간']})",
        "note": "지지 십신은 지장간(본/중/여기) 기준입니다.",
    }

    # PDF 표 출력용 profiles 구조(무조건 채움)
    profiles = {
        "day_master": day_master,
        "stems": stem_map,
        "branches": branch_map,
        "counts": counts,
    }

    return {
        "profiles": profiles,
        "summary": summary,
    }


# =========================
# Compatibility Adapter
# - report_core / hidden_stems 가 기대하는 표준 엔트리
# =========================


def map_sipsin(pillars: Any, *args, **kwargs) -> Dict[str, Any]:
    """
    ✅ 표준 엔트리: map_sipsin(pillars) -> dict
    우리 프로젝트 ten_god 시그니처가 (day_stem, target_stem) 형태일 때도 동작.
    - hidden_stems가 (pillars, something) 으로 불러도 안전(*args 처리)
    """

    # ten_god가 있으면 그걸 최우선으로 사용
    ten_god_fn = globals().get("ten_god")
    if not callable(ten_god_fn):
        return {
            "error": "map_sipsin failed",
            "reason": "ten_god function not found in sipsin.py",
        }

    # pillars dict 구조: pillars["year"]["stem"], ["month"]["stem"], ["day"]["stem"], ["hour"]["stem"]
    if not isinstance(pillars, dict) or "day" not in pillars:
        return {
            "error": "map_sipsin failed",
            "reason": "pillars must be dict with key 'day'",
            "pillars_type": str(type(pillars)),
        }

    day_stem = (pillars.get("day") or {}).get("stem")
    if not day_stem:
        return {
            "error": "map_sipsin failed",
            "reason": "day stem (일간) not found in pillars['day']['stem']",
        }

    out: Dict[str, Any] = {}

    # 각 기둥의 천간 십신
    for key in ("year", "month", "day", "hour"):
        p = pillars.get(key) or {}
        target_stem = p.get("stem")
        if not target_stem:
            out[key] = {"stem": None, "ten_god": None}
            continue

        try:
            tg = ten_god_fn(day_stem, target_stem)
        except TypeError as e:
            return {
                "error": "map_sipsin failed",
                "reason": "ten_god signature mismatch",
                "hint": "expected ten_god(day_stem, target_stem)",
                "detail": str(e),
            }
        except Exception as e:
            return {
                "error": "map_sipsin failed",
                "reason": f"ten_god error: {type(e).__name__}: {e}",
            }

        out[key] = {
            "stem": target_stem,
            "ten_god": tg,
        }

    return out

