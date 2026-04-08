# unteim/engine/sentences_v2_engine.py
# -*- coding: utf-8 -*-
"""
UNTEIM v2 문장 매핑 엔진

sentences_v2.json에 저장된 246개 문장을
analyze_full() 결과(packed dict)에서 추출한 분석 데이터에 따라
자동으로 매핑하여 리포트에 삽입할 수 있는 형태로 반환합니다.

사용법:
    from engine.sentences_v2_engine import attach_v2_sentences
    attach_v2_sentences(packed)  # packed dict에 "v2_sentences" 키 추가
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ============================================================
# 1. 데이터 로드
# ============================================================
# Repo root: engine/ -> parent.parent; data lives at repo root data/
_ROOT = Path(__file__).resolve().parent.parent
_DATA_DIR = _ROOT / "data"
_SENTENCES_FILE = _DATA_DIR / "sentences_v2.json"

_CACHE: Optional[Dict[str, Any]] = None


def _load_sentences() -> Dict[str, Any]:
    """sentences_v2.json을 한 번만 로드하고 캐싱"""
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    with open(_SENTENCES_FILE, "r", encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)
    _CACHE = data
    return data


def _all_sentences() -> List[Dict[str, Any]]:
    return _load_sentences().get("sentences", [])


def _oheng_table() -> List[Dict[str, Any]]:
    return _load_sentences().get("parts", {}).get("B", {}).get("oheng_table", [])


# ============================================================
# 2. 오행 매핑 유틸
# ============================================================
# 한자↔한글 오행 매핑
HANJA_TO_KR = {"木": "목", "火": "화", "土": "토", "金": "금", "水": "수"}
KR_TO_HANJA = {v: k for k, v in HANJA_TO_KR.items()}

# 천간→오행 매핑
GAN_TO_ELEMENT = {
    "甲": "목", "乙": "목", "丙": "화", "丁": "화", "戊": "토",
    "己": "토", "庚": "금", "辛": "금", "壬": "수", "癸": "수",
}

# 천간 한글 매핑
GAN_LABELS = {
    "甲": "갑목", "乙": "을목", "丙": "병화", "丁": "정화", "戊": "무토",
    "己": "기토", "庚": "경금", "辛": "신금", "壬": "임수", "癸": "계수",
}

# 오행별 condition 판단 임계치
BALANCE_THRESHOLD = {
    "적당할 때": (1.5, 3.5),  # 적당 범위 (min, max)
    "과다할 때": (3.5, 999),  # 과다
    "부족할 때": (0, 1.5),    # 부족
}


def _classify_element_condition(count: float) -> str:
    """오행 개수 기준으로 '적당할 때' / '과다할 때' / '부족할 때' 판별"""
    if count >= 3.5:
        return "과다할 때"
    elif count <= 1.5:
        return "부족할 때"
    return "적당할 때"


def _normalize_element(name: str) -> str:
    """다양한 입력(한자/한글)을 한글 오행으로 정규화"""
    name = str(name).strip()
    if name in HANJA_TO_KR:
        return HANJA_TO_KR[name]
    if name in KR_TO_HANJA:
        return name
    return name


# ============================================================
# 3. 섹션별 매핑 함수
# ============================================================

def _get_by_section(section_code: str) -> List[Dict[str, Any]]:
    """특정 섹션 코드의 문장들을 필터"""
    return [s for s in _all_sentences() if s.get("section_code") == section_code]


# ── A-1: 오행별 성격 & 패턴 인식 ──────────────────────────────
def map_a1_oheng_personality(oheng_counts: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    오행 분포에 따라 A-1 문장 자동 매핑
    
    Args:
        oheng_counts: {"木": 2, "火": 3, "土": 1, ...} 또는 {"목": 2, ...}
    
    Returns:
        매핑된 문장 리스트 (각 오행에 대해 해당 condition 문장들)
    """
    result = []
    a1 = _get_by_section("A-1")
    
    for raw_elem, count in oheng_counts.items():
        elem = _normalize_element(raw_elem)
        count_val = float(count) if count else 0.0
        condition = _classify_element_condition(count_val)
        
        matched = [
            s for s in a1
            if s.get("element") == elem and s.get("condition") == condition
        ]
        
        for m in matched:
            result.append({
                **m,
                "matched_by": {
                    "element": elem,
                    "count": count_val,
                    "condition": condition,
                },
            })
    
    return result


# ── A-2: 일간(天干) 성격 프로필 ───────────────────────────────
def map_a2_day_master(day_gan: str) -> List[Dict[str, Any]]:
    """
    일간(天干)에 따라 A-2 프로필 문장 자동 매핑
    
    Args:
        day_gan: "甲", "乙", ... 또는 "갑", "을", ...
    """
    a2 = _get_by_section("A-2")
    
    # 정규화
    gan = str(day_gan).strip()
    
    # 한글→한자 역매핑
    KOR_TO_GAN = {
        "갑": "甲", "을": "乙", "병": "丙", "정": "丁", "무": "戊",
        "기": "己", "경": "庚", "신": "辛", "임": "壬", "계": "癸",
    }
    if gan in KOR_TO_GAN:
        gan = KOR_TO_GAN[gan]
    
    matched = [s for s in a2 if s.get("element") == gan]
    return [{**m, "matched_by": {"day_gan": gan}} for m in matched]


# ── A-3 보조: 신살 이름 자동 정규화
def _normalize_shinsal_name(raw_name: str) -> str:
    name = str(raw_name).strip()
    if ":" in name:
        name = name.split(":")[-1].strip()
    if "_" in name and "운성" in name:
        name = name.split("_")[-1].strip()
    return name


# ── A-3: 신살 & 12운성 해석 ───────────────────────────────────
def map_a3_shinsal_and_fortunes(
    shinsal_items: List[Dict[str, Any]],
    twelve_fortunes: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    검출된 신살/12운성에 따라 A-3 문장 자동 매핑
    """
    a3 = _get_by_section("A-3")
    result = []

    # 12운성 매핑
    fortune_names = set()
    if isinstance(twelve_fortunes, dict):
        for pos, fortune_data in twelve_fortunes.items():
            if isinstance(fortune_data, dict):
                name = fortune_data.get("name") or fortune_data.get("fortune") or ""
            elif isinstance(fortune_data, str):
                name = fortune_data
            else:
                continue
            if name:
                fortune_names.add(_normalize_shinsal_name(name))

    # 신살 이름 수집 (자동 정규화)
    shinsal_names = set()
    if isinstance(shinsal_items, list):
        for item in shinsal_items:
            if isinstance(item, dict):
                raw_name = item.get("name", "")
                if raw_name:
                    normalized = _normalize_shinsal_name(raw_name)
                    shinsal_names.add(normalized)
                    if "운성" in raw_name or ":" in raw_name:
                        fortune_names.add(normalized)

    all_keywords = fortune_names | shinsal_names

    for s in a3:
        keyword = s.get("keyword", "")
        if not keyword:
            text = s.get("text", "")
            for kw in all_keywords:
                if kw in text:
                    result.append({
                        **s,
                        "matched_by": {"keyword": kw, "source": "text_match"},
                    })
                    break
        else:
            import re
            kr_name = re.sub(r'\(.*?\)', '', keyword).strip()
            if kr_name in all_keywords or keyword in all_keywords:
                result.append({
                    **s,
                    "matched_by": {"keyword": kr_name},
                })

    return result



# ── A-4: 궁합 해석 ───────────────────────────────────────────
def map_a4_compatibility(relationship_type: str = "general") -> List[Dict[str, Any]]:
    """
    궁합 유형에 따라 A-4 문장 자동 매핑
    
    Args:
        relationship_type: "상생" | "상극" | "비화" | "general"
    """
    a4 = _get_by_section("A-4")
    
    condition_map = {
        "상생": "상생(相生) 관계",
        "상극": "상극(相剋) 관계",
        "비화": "비화(比和) 관계",
        "general": "궁합 일반 조언",
    }
    
    target = condition_map.get(relationship_type, relationship_type)
    matched = [s for s in a4 if s.get("condition") == target]
    return [{**m, "matched_by": {"relationship_type": relationship_type}} for m in matched]


# ── B-1: 오행 개운법 표 ───────────────────────────────────────
def map_b1_oheng_practice_table(yongshin_element: str) -> Dict[str, Any]:
    """
    용신 오행에 해당하는 개운법 표 행 반환
    
    Args:
        yongshin_element: "목", "화", "토", "금", "수" 또는 한자
    """
    elem = _normalize_element(yongshin_element)
    table = _oheng_table()
    
    elem_map = {"목": "목(木)", "화": "화(火)", "토": "토(土)", "금": "금(金)", "수": "수(水)"}
    target = elem_map.get(elem, elem)
    
    for row in table:
        if row.get("오행") == target:
            return {"table_row": row, "matched_by": {"yongshin_element": elem}}
    
    return {"table_row": {}, "matched_by": {"yongshin_element": elem, "error": "not_found"}}


# ── B-2: 용신별 실천 개운법 조언 ──────────────────────────────
def map_b2_yongshin_advice(yongshin_element: str) -> List[Dict[str, Any]]:
    """
    용신 오행에 따라 B-2 실천 조언 자동 매핑
    """
    b2 = _get_by_section("B-2")
    elem = _normalize_element(yongshin_element)
    
    matched = [s for s in b2 if s.get("element") == elem]
    return [{**m, "matched_by": {"yongshin_element": elem}} for m in matched]


# ── B-3: 월운별 실천 가이드 ───────────────────────────────────
def map_b3_monthly_guide(month_quality: str = "good") -> List[Dict[str, Any]]:
    """
    월운 품질에 따라 B-3 가이드 문장 자동 매핑
    
    Args:
        month_quality: "good" | "caution" | "transition" | "stable" | "detail"
    """
    b3 = _get_by_section("B-3")
    
    condition_map = {
        "good": "기운이 좋은 달",
        "caution": "주의가 필요한 달",
        "transition": "전환과 안정의 달",
        "stable": "전환과 안정의 달",
        "detail": "영역별 디테일 조언",
    }
    
    target = condition_map.get(month_quality, month_quality)
    matched = [s for s in b3 if s.get("condition") == target]
    
    if not matched:
        # condition이 없는 경우 전체 B-3 반환
        matched = b3
    
    return [{**m, "matched_by": {"month_quality": month_quality}} for m in matched]


# ── B-4: 대운·세운 흐름 가이드 ────────────────────────────────
def map_b4_luck_guide(luck_phase: str = "ascending") -> List[Dict[str, Any]]:
    """
    대운/세운 단계에 따라 B-4 가이드 문장 자동 매핑
    
    Args:
        luck_phase: "ascending" | "adjusting" | "changing" | "harvesting" | "general"
    """
    b4 = _get_by_section("B-4")
    
    # B-4는 condition이 없으므로 키워드 기반 매핑
    phase_keywords = {
        "ascending": ["상승", "씨앗", "노력"],
        "adjusting": ["조정", "숨 고르기", "기초"],
        "changing": ["변화", "방향", "전환", "도전"],
        "harvesting": ["수확", "결실", "감사"],
        "general": [],  # 전체 반환
    }
    
    keywords = phase_keywords.get(luck_phase, [])
    
    if not keywords:
        return [{**m, "matched_by": {"luck_phase": luck_phase}} for m in b4]
    
    matched = []
    for s in b4:
        text = s.get("text", "")
        if any(kw in text for kw in keywords):
            matched.append({**s, "matched_by": {"luck_phase": luck_phase}})
    
    return matched if matched else [{**m, "matched_by": {"luck_phase": "fallback"}} for m in b4[:3]]


# ── B-5: 삼재(三災) 해석 ─────────────────────────────────────
def map_b5_samjae(samjae_type: str = "none") -> List[Dict[str, Any]]:
    """
    삼재 상태에 따라 B-5 문장 자동 매핑
    
    Args:
        samjae_type: "들삼재" | "눌삼재" | "날삼재" | "복삼재" | "none" | "general"
    """
    b5 = _get_by_section("B-5")
    
    type_keywords = {
        "들삼재": "들삼재",
        "눌삼재": "눌삼재",
        "날삼재": "날삼재",
        "복삼재": "복삼재",
        "none": "삼재가 아닌",
        "general": "성장통",
    }
    
    keyword = type_keywords.get(samjae_type, samjae_type)
    
    matched = [s for s in b5 if keyword in s.get("text", "")]
    
    # 공통 문장 (개운법) 항상 포함
    common = [s for s in b5 if "개운법" in s.get("text", "") or "성장통" in s.get("text", "")]
    
    # 합치되 중복 제거
    seen_ids = set()
    result = []
    for s in matched + common:
        if s["id"] not in seen_ids:
            seen_ids.add(s["id"])
            result.append({**s, "matched_by": {"samjae_type": samjae_type}})
    
    return result


# ── C: 마무리 & 코칭 문장 ────────────────────────────────────
def map_c_closing(section: str = "all") -> List[Dict[str, Any]]:
    """
    C파트 문장 매핑
    
    Args:
        section: "C-1" | "C-2" | "C-3" | "C-4" | "C-5" | "all"
    """
    if section == "all":
        c_all = []
        for code in ["C-1", "C-2", "C-3", "C-4", "C-5"]:
            c_all.extend(_get_by_section(code))
        return c_all
    
    return _get_by_section(section)


# ============================================================
# 4. 통합 매핑 함수 (analyze_full 결과 연동)
# ============================================================

def build_v2_sentences(packed: Dict[str, Any]) -> Dict[str, Any]:
    """
    analyze_full()의 결과(packed dict)에서 분석 데이터를 추출하여
    sentences_v2.json의 문장을 자동 매핑하고 구조화된 결과를 반환.
    
    Args:
        packed: analyze_full() 반환 dict
        
    Returns:
        {
            "A1_oheng_personality": [...],
            "A2_day_master": [...],
            "A3_shinsal_fortunes": [...],
            "A4_compatibility": [...],
            "B1_practice_table": {...},
            "B2_yongshin_advice": [...],
            "B3_monthly_guide": [...],
            "B4_luck_guide": [...],
            "B5_samjae": [...],
            "C_opening": [...],      # C-1
            "C_philosophy": [...],   # C-2
            "C_closing": [...],      # C-3
            "C_affirmation": [...],  # C-4
            "C_coaching": [...],     # C-5
            "meta": {...},
        }
    """
    result: Dict[str, Any] = {}
    analysis = packed.get("analysis", {}) or {}
    extra = packed.get("extra", {}) or {}
    
    # ── A-1: 오행별 성격 ──
    oheng = analysis.get("oheng") or packed.get("oheng") or {}
    oheng_counts = oheng.get("counts", {}) if isinstance(oheng, dict) else {}
    result["A1_oheng_personality"] = map_a1_oheng_personality(oheng_counts)
    
    # ── A-2: 일간 프로필 ──
    day_master = analysis.get("day_master") or packed.get("day_master") or {}
    if isinstance(day_master, dict):
        day_gan = day_master.get("gan") or day_master.get("day_gan") or ""
    else:
        # pillars에서 직접 추출
        pillars = analysis.get("pillars") or packed.get("pillars") or {}
        if isinstance(pillars, dict):
            day_pillar = pillars.get("day", {})
            day_gan = day_pillar.get("gan") or day_pillar.get("stem") or ""
        else:
            day_gan = ""
    result["A2_day_master"] = map_a2_day_master(day_gan)
    
    # ── A-3: 신살 & 12운성 ──
    shinsal = analysis.get("shinsal") or packed.get("shinsal") or {}
    shinsal_items = shinsal.get("items", []) if isinstance(shinsal, dict) else []
    twelve_fortunes = analysis.get("twelve_fortunes") or packed.get("twelve_fortunes") or {}
    result["A3_shinsal_fortunes"] = map_a3_shinsal_and_fortunes(shinsal_items, twelve_fortunes)
    
    # ── A-4: 궁합 (기본은 general) ──
    result["A4_compatibility_general"] = map_a4_compatibility("general")
    
    # ── B-1: 개운법 표 ──
    yongshin_data = analysis.get("yongshin") or extra.get("yongshin") or {}
    yongshin_element = ""
    if isinstance(yongshin_data, dict):
        # 용신 오행 추출 (다양한 키 대응)
        yongshin_element = (
            yongshin_data.get("yongshin_element")
            or yongshin_data.get("element")
            or yongshin_data.get("yongshin", {}).get("element", "")
            if isinstance(yongshin_data.get("yongshin"), dict)
            else yongshin_data.get("yongshin", "")
        )
    
    # 용신 자동 추론: 용신 데이터가 없으면 오행 중 가장 부족한 것을 용신으로
    if not yongshin_element and oheng_counts:
        try:
            min_elem = min(oheng_counts, key=lambda k: float(oheng_counts[k]))
            yongshin_element = _normalize_element(min_elem)
        except Exception:
            pass

    if yongshin_element:
        result["B1_practice_table"] = map_b1_oheng_practice_table(yongshin_element)
        result["B2_yongshin_advice"] = map_b2_yongshin_advice(yongshin_element)
    else:
        result["B1_practice_table"] = {"table_row": {}, "matched_by": {"error": "no_yongshin"}}
        result["B2_yongshin_advice"] = []

    
    # ── B-3: 월운 가이드 ──
    # 현재 월의 기운 평가 (total_fortune에서 추출)
    total_fortune = extra.get("total_fortune", {})
    month_fortune = total_fortune.get("month", {}) if isinstance(total_fortune, dict) else {}
    month_score = month_fortune.get("score", 50) if isinstance(month_fortune, dict) else 50
    
    if month_score >= 70:
        month_quality = "good"
    elif month_score <= 30:
        month_quality = "caution"
    else:
        month_quality = "stable"
    
    result["B3_monthly_guide"] = map_b3_monthly_guide(month_quality)
    
    # ── B-4: 대운/세운 가이드 ──
    result["B4_luck_guide"] = map_b4_luck_guide("general")
    
    # ── B-5: 삼재 ──
    samjae = total_fortune.get("samjae", {}) if isinstance(total_fortune, dict) else {}
    samjae_type = "none"
    if isinstance(samjae, dict):
        samjae_type = samjae.get("type") or samjae.get("samjae_type") or "none"
        if samjae.get("is_samjae") is False:
            samjae_type = "none"
    result["B5_samjae"] = map_b5_samjae(samjae_type)
    
    # ── C: 마무리 & 코칭 ──
    result["C_opening"] = map_c_closing("C-1")
    result["C_philosophy"] = map_c_closing("C-2")
    result["C_closing"] = map_c_closing("C-3")
    result["C_affirmation"] = map_c_closing("C-4")
    result["C_coaching"] = map_c_closing("C-5")
    
    # ── 메타 정보 ──
    total_mapped = sum(
        len(v) if isinstance(v, list) else (1 if isinstance(v, dict) and v.get("table_row") else 0)
        for v in result.values()
    )
    result["meta"] = {
        "version": "v2",
        "total_mapped": total_mapped,
        "day_gan": day_gan,
        "yongshin_element": yongshin_element,
        "samjae_type": samjae_type,
        "month_quality": month_quality,
    }
    
    return result


def attach_v2_sentences(packed: Dict[str, Any]) -> None:
    """
    analyze_full() 결과에 v2 문장을 자동으로 부착.
    packed["v2_sentences"]에 결과가 추가됩니다.
    
    Usage:
        packed = analyze_full(pillars, birth_str=...)
        attach_v2_sentences(packed)
        # packed["v2_sentences"]에서 문장 접근 가능
    """
    try:
        v2 = build_v2_sentences(packed)
        packed["v2_sentences"] = v2
    except Exception as e:
        packed["v2_sentences"] = {
            "error": f"{type(e).__name__}: {e}",
            "meta": {"version": "v2", "total_mapped": 0},
        }


# ============================================================
# 5. 텍스트 추출 유틸 (리포트 렌더링용)
# ============================================================

def get_texts(sentences: List[Dict[str, Any]]) -> List[str]:
    """매핑 결과에서 텍스트만 추출"""
    return [s.get("text", "") for s in sentences if s.get("text")]


def get_random_text(sentences: List[Dict[str, Any]], n: int = 1) -> List[str]:
    """매핑 결과에서 랜덤으로 n개 텍스트 추출"""
    import random
    texts = get_texts(sentences)
    if not texts:
        return []
    return random.sample(texts, min(n, len(texts)))


def format_report_section(
    title: str,
    sentences: List[Dict[str, Any]],
    max_sentences: int = 5,
) -> str:
    """리포트 섹션 포맷팅"""
    texts = get_texts(sentences)[:max_sentences]
    if not texts:
        return ""
    
    lines = [f"\n{'='*50}", f"  {title}", f"{'='*50}"]
    for i, text in enumerate(texts, 1):
        lines.append(f"  {i}. {text}")
    lines.append("")
    
    return "\n".join(lines)
