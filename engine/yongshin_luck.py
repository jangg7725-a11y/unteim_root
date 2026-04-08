# yongshin_luck.py
# 용신 기반 대운/세운/월운 호운·주의 시기 분석 엔진

from typing import List, Dict, Any, Optional

def _as_dict(x):
    if isinstance(x, dict):
        return x
    if hasattr(x, "__dict__"):
        return dict(x.__dict__)
    return {"value": x}

# ---------------------------------------------------------
#  공통 오행 매핑 / 상생·상극 관계
# ---------------------------------------------------------

# 천간 → 오행
STEM_TO_ELEMENT: Dict[str, str] = {
    "갑": "목", "을": "목",
    "병": "화", "정": "화",
    "무": "토", "기": "토",
    "경": "금", "신": "금",
    "임": "수", "계": "수",
}

# 상생 관계 (기본형)
SANGSAENG: Dict[str, List[str]] = {
    "목": ["화"],
    "화": ["토"],
    "토": ["금"],
    "금": ["수"],
    "수": ["목"],
}

# 상극 관계 (기본형)
SANGGEUK: Dict[str, List[str]] = {
    "목": ["토"],
    "토": ["수"],
    "수": ["화"],
    "화": ["금"],
    "금": ["목"],
}


# ---------------------------------------------------------
#  공통 헬퍼
# ---------------------------------------------------------


def _element_from_ganji(ganji: str) -> Optional[str]:
    """간지에서 천간만 뽑아 오행으로 변환."""
    if not ganji:
        return None
    stem = ganji[0]
    return STEM_TO_ELEMENT.get(stem)


# ★★★ 여기 추가 ★★★
def _normalize_elem_value(v: Any) -> Optional[str]:
    """
    용신/희신/기신/일간 값이 문자열/리스트/딕셔너리 등
    여러 형태로 들어와도 오행 한 글자('목','화','토','금','수')로 정리해 주는 헬퍼.
    """
    if v is None:
        return None

    # 문자열인 경우
    if isinstance(v, str):
        for ch in ("목", "화", "토", "금", "수"):
            if ch in v:
                return ch
        return v

    # 리스트/튜플인 경우 → 첫 요소 사용
    if isinstance(v, (list, tuple)):
        if not v:
            return None
        return _normalize_elem_value(v[0])

    # 딕셔너리인 경우
    if isinstance(v, dict):
        for key in ("오행", "element", "elem", "오행값"):
            if key in v:
                return _normalize_elem_value(v[key])
        for vv in v.values():
            cand = _normalize_elem_value(vv)
            if cand:
                return cand
        return None

    return None
# ★★★ 여기까지 ★★★


def _get_yongshin_elements(info: Any) -> Dict[str, Optional[str]]:
    """
    yongshin_info 에서 용신/희신/기신/일간오행을 추출.
    - 한글 키(용신/희신/기신/일간오행 …)
    - 영문 키(yongshin/heeshin/gishin/day_element …)
    - 그 외 '용신', '희신', '기신', '일간' 이라는 글자만 들어가 있어도 전부 탐색.
    """
    # dict 가 아니면 바로 빈 값
    if not isinstance(info, dict):
        return {"y": None, "h": None, "g": None, "ilgan": None}

    # 1차: 대표 키들 먼저 시도
    y_raw = (
        info.get("용신")
        or info.get("yongshin")
        or info.get("yongshin_element")
    )
    h_raw = (
        info.get("희신")
        or info.get("heeshin")
        or info.get("heeshin_element")
    )
    g_raw = (
        info.get("기신")
        or info.get("gishin")
        or info.get("gishin_element")
    )
    ilgan_raw = (
        info.get("일간오행")
        or info.get("day_element")
        or info.get("일간 오행")
        or info.get("일간_오행")
    )

    y = _normalize_elem_value(y_raw)
    h = _normalize_elem_value(h_raw)
    g = _normalize_elem_value(g_raw)
    ilgan = _normalize_elem_value(ilgan_raw)

    # 2차: 키 이름에 특정 단어가 들어가 있으면 거기서 추가로 찾아오기 (fallback)
    if y is None or h is None or g is None or ilgan is None:
        for k, v in info.items():
            if not isinstance(k, str):
                continue
            key = k.lower()

            if y is None and ("용신" in k or "yong" in key):
                y = _normalize_elem_value(v)

            if h is None and ("희신" in k or "heesh" in key or "hee" in key):
                h = _normalize_elem_value(v)

            if g is None and ("기신" in k or "gish" in key or "gi_sh" in key):
                g = _normalize_elem_value(v)

            if ilgan is None and ("일간" in k or "day_elem" in key or "ilgan" in key):
                ilgan = _normalize_elem_value(v)

    # 마지막 한 번 더 정리
    y = _normalize_elem_value(y)
    h = _normalize_elem_value(h)
    g = _normalize_elem_value(g)
    ilgan = _normalize_elem_value(ilgan)

    return {"y": y, "h": h, "g": g, "ilgan": ilgan}



def _score_element(
    elem: Optional[str],
    y: Optional[str],
    h: Optional[str],
    g: Optional[str],
    ilgan: Optional[str],
    base_weight: int = 1,
) -> Dict[str, Any]:
    """
    하나의 오행(elem)에 대해 점수와 태그를 계산.
    - base_weight: 세운/대운/월운 비중 조절
    """

    score = 0
    tag = "neutral"

    if elem is None:
        return {"score": score, "tag": tag}

    # 1) 용신 / 희신 / 기신 기준
    if y and elem == y:
        score += 3 * base_weight
        tag = "favorable"
    elif h and elem == h:
        score += 1 * base_weight
        tag = "favorable"
    elif g and elem == g:
        score -= 2 * base_weight
        tag = "caution"

    # 2) 일간오행과의 상생/상극 보정
    if ilgan:
        # 상생(일간을 도와주는 기운)
        if elem in SANGSAENG.get(ilgan, []):
            score += 1
            if score > 0 and tag == "neutral":
                tag = "favorable"
        # 상극(일간을 누르는 기운)
        if elem in SANGGEUK.get(ilgan, []):
            score -= 2
            if score < 0 and tag == "neutral":
                tag = "caution"

    # 최종 태그 재조정
    if score > 0 and tag == "neutral":
        tag = "favorable"
    elif score < 0 and tag == "neutral":
        tag = "caution"

    return {"score": score, "tag": tag}


def _count_by_tag(items: List[Dict[str, Any]], tag: str) -> int:
    """리스트 안에서 tag가 일치하는 개수 합산."""
    return sum(1 for x in items if x.get("tag") == tag)


# =========================================================
#  1. 세운(연운) 점수화
# =========================================================

def analyze_seyun_for_yongshin(
    seyun_list: List[Dict[str, Any]],
    yongshin_info: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    세운 리스트 (각 연도별 간지)에 용신/희신/기신 기준 점수를 부여.
    - seyun_list 원소 예시: {"year": 2025, "ganji": "을사"}
    - 반환: {"year", "ganji", "element", "score", "tag"} 구조 리스트
    """
    elems = _get_yongshin_elements(yongshin_info)
    y, h, g, ilgan = elems["y"], elems["h"], elems["g"], elems["ilgan"]
    # 🔧 SewoonItem(dataclass 등) → dict 강제 변환
    seyun_list = [_as_dict(x) for x in (seyun_list or [])]

    scored: List[Dict[str, Any]] = []

    for item in seyun_list:
        year = item.get("year")
        ganji = item.get("ganji", "")
        elem = _element_from_ganji(ganji)

        # 세운은 중간 비중
        result = _score_element(elem, y, h, g, ilgan, base_weight=3)

        scored.append(
            {
                "year": year,
                "ganji": ganji,
                "element": elem,
                "score": result["score"],
                "tag": result["tag"],
            }
        )

    return scored


# =========================================================
#  2. 대운(10년 운) 점수화
# =========================================================

def analyze_dayun_for_yongshin(
    dayun_list: List[Dict[str, Any]],
    yongshin_info: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    대운 리스트 (10년 단위)에 용신/희신/기신 기준 점수를 부여.
    - dayun_list 원소 예시: {"age": 28, "ganji": "경신", ...}
    - 반환: {"age", "ganji", "element", "score", "tag"} 구조 리스트
    """
    elems = _get_yongshin_elements(yongshin_info)
    y, h, g, ilgan = elems["y"], elems["h"], elems["g"], elems["ilgan"]

    scored: List[Dict[str, Any]] = []

    for item in dayun_list:
        age = item.get("age")
        ganji = item.get("ganji", "")
        elem = _element_from_ganji(ganji)

        # 대운은 가장 큰 비중
        result = _score_element(elem, y, h, g, ilgan, base_weight=4)

        scored.append(
            {
                "age": age,
                "ganji": ganji,
                "element": elem,
                "score": result["score"],
                "tag": result["tag"],
            }
        )

    return scored


# =========================================================
#  3. 월운 점수화 (향후 확장용)
# =========================================================

def analyze_monthly_flow_for_yongshin(
    monthly_flow: List[Dict[str, Any]],
    yongshin_info: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    월운 흐름에 대해 점수화.
    - monthly_flow 원소 예시: {"year": 2025, "month": 3, "ganji": "정묘"}
    - 반환: {"year","month","ganji","element","score","tag"} 구조 리스트
    - 아직 월운 엔진이 없으면 monthly_flow는 [] 로 들어와서 빈 리스트 반환.
    """
    if not monthly_flow:
        return []

    elems = _get_yongshin_elements(yongshin_info)
    y, h, g, ilgan = elems["y"], elems["h"], elems["g"], elems["ilgan"]

    scored: List[Dict[str, Any]] = []

    for item in monthly_flow:
        year = item.get("year")
        month = item.get("month")
        ganji = item.get("ganji", "")
        elem = _element_from_ganji(ganji)

        # 월운은 세운보다 약간 낮은 비중
        result = _score_element(elem, y, h, g, ilgan, base_weight=2)

        scored.append(
            {
                "year": year,
                "month": month,
                "ganji": ganji,
                "element": elem,
                "score": result["score"],
                "tag": result["tag"],
            }
        )

    return scored


# =========================================================
#  4. 요약 텍스트 생성
# =========================================================

def build_yongshin_luck_summary(
    seyun_scored: List[Dict[str, Any]],
    dayun_scored: List[Dict[str, Any]],
    monthly_scored: List[Dict[str, Any]],
    yongshin_info: Dict[str, str],
) -> str:
    """
    세운/대운/월운 호운을 종합해서 한 문단 요약을 만든다.
    """

    # 1) 전체 호운/주의 비중 계산
    fav_total = (
        _count_by_tag(seyun_scored, "favorable")
        + _count_by_tag(dayun_scored, "favorable")
        + _count_by_tag(monthly_scored, "favorable")
    )
    cau_total = (
        _count_by_tag(seyun_scored, "caution")
        + _count_by_tag(dayun_scored, "caution")
        + _count_by_tag(monthly_scored, "caution")
    )

    if fav_total > cau_total:
        main_trend = "전체적으로는 용신 기운이 잘 살아나는 호운의 흐름입니다."
    elif fav_total < cau_total:
        main_trend = "전체적으로는 기신 기운이 과해지거나 주의 흐름이 더 강하게 나타납니다."
    else:
        main_trend = "전체적으로 균형적인 흐름이지만, 시기별로 기운이 엇갈릴 수 있는 구조입니다."

    # 2) 영역별 호운/주의 횟수 요약
    seyun_fav = _count_by_tag(seyun_scored, "favorable")
    seyun_cau = _count_by_tag(seyun_scored, "caution")
    dayun_fav = _count_by_tag(dayun_scored, "favorable")
    dayun_cau = _count_by_tag(dayun_scored, "caution")
    mon_fav = _count_by_tag(monthly_scored, "favorable")
    mon_cau = _count_by_tag(monthly_scored, "caution")

    seyun_line = f"● 세운: 호운 {seyun_fav}회 / 주의 {seyun_cau}회"
    dayun_line = f"● 대운: 호운 {dayun_fav}회 / 주의 {dayun_cau}회"
    mon_line = f"● 월운: 호운 {mon_fav}회 / 주의 {mon_cau}회"

    # 3) 용신/희신/기신 + 일간 오행 힌트
    y = yongshin_info.get("용신") or yongshin_info.get("yongshin")
    h = yongshin_info.get("희신") or yongshin_info.get("heeshin") or yongshin_info.get("hee")
    g = yongshin_info.get("기신") or yongshin_info.get("gishin") or yongshin_info.get("gi")

    lines: List[str] = []

    if y:
        lines.append(f"이 사주에서 핵심 키워드는 용신 『{y}』 기운이 얼마나 살아나느냐입니다.")
    if h:
        lines.append(f"보조적으로는 희신 『{h}』의 기운이 어떤 시기에 상황을 한 번 부드럽게 풀어주느냐가 중요합니다.")
    if g:
        lines.append(f"기신 『{g}』은(는) 과하거나 부족해지면 부담이 되는 기운이므로, 해당 시기에는 조절이 필요합니다.")

    if not lines:
        lines.append("현재 데이터 기준으로는 뚜렷한 호운·주의 패턴이 드러나지 않습니다.")

    final_text = (
        f"{main_trend}\n\n"
        "아래는 용신 기준 운의 전체적인 분포를 요약한 내용입니다:\n\n"
        f"{seyun_line}\n"
        f"{dayun_line}\n"
        f"{mon_line}\n\n"
        + "\n".join(lines)
    )

    return final_text


# =========================================================
#  5. 토털 엔트리 함수 (full_analyzer → 여기만 호출)
# =========================================================

def analyze_yongshin_luck(
    dayun_list: Optional[List[Dict[str, Any]]],
    seyun_list: Optional[List[Dict[str, Any]]],
    monthly_flow: Optional[List[Dict[str, Any]]],
    yongshin_info: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    main_report / full_analyzer 에서 바로 호출할 통합 함수.
    """

    # 용신 정보가 없더라도 계산은 계속 진행 (부분 분석 허용)
    if not yongshin_info:
     yongshin_info = {}  # 최소 방어: 빈 dict로 진행


    # None 방지
    dayun_list = dayun_list or []
    seyun_list = seyun_list or []
    monthly_flow = monthly_flow or []

    # 1) 세운/대운/월운 점수화
    seyun_scored = analyze_seyun_for_yongshin(seyun_list, yongshin_info)
    dayun_scored = analyze_dayun_for_yongshin(dayun_list, yongshin_info)
    monthly_scored = analyze_monthly_flow_for_yongshin(monthly_flow, yongshin_info)

    # 2) 요약 텍스트 생성
    summary = build_yongshin_luck_summary(
        seyun_scored, dayun_scored, monthly_scored, yongshin_info
    )

    # 3) 메인 리포트에서 바로 쓸 수 있도록 상위 리스트 정리
    #   - 연도: 세운 기준
    favorable_years = [
        x for x in seyun_scored if x.get("tag") == "favorable"
    ]
    caution_years = [
        x for x in seyun_scored if x.get("tag") == "caution"
    ]

    #   - 월운: monthly_scored 기준
    favorable_months = [
        x for x in monthly_scored if x.get("tag") == "favorable"
    ]
    caution_months = [
        x for x in monthly_scored if x.get("tag") == "caution"
    ]

    return {
        "favorable_years": favorable_years,
        "caution_years": caution_years,
        "dayun_scored": dayun_scored,
        "seyun_scored": seyun_scored,
        "monthly_scored": monthly_scored,
        "summary": summary,
        "monthly_highlights": {
            "favorable_months": favorable_months,
            "caution_months": caution_months,
        },
    }
