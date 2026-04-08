# unteim/engine/narrative/timing_hint.py
from __future__ import annotations
from typing import List, Optional, Tuple, Dict

def _clamp(a: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, a))

def _range_text(a: int, b: int) -> str:
    if a == b:
        return f"{a}세 전후"
    return f"{a}~{b}세 전후"

def split_phases(start_age: int, end_age: int) -> Tuple[Tuple[int,int], Tuple[int,int], Tuple[int,int]]:
    """
    대운 구간을 초/중/후 3구간으로 나눔(기본 10년 기준, 유연 처리)
    - 초반: start ~ start+2
    - 중반: start+3 ~ start+6
    - 후반: start+7 ~ end
    """
    s, e = start_age, end_age
    if e < s:
        s, e = e, s

    early = (s, _clamp(s + 2, s, e))
    mid   = (_clamp(s + 3, s, e), _clamp(s + 6, s, e))
    late  = (_clamp(s + 7, s, e), e)
    return early, mid, late

def split_early_half(start_age: int, end_age: int) -> Tuple[Tuple[int,int], Tuple[int,int]]:
    """
    초반을 상/하반기로 쪼갬
    - 초반 상반기: start ~ start
    - 초반 하반기: start+1 ~ start+2 (가능 범위)
    """
    s, e = start_age, end_age
    if e < s:
        s, e = e, s

    a = (s, _clamp(s, s, e))
    b = (_clamp(s + 1, s, e), _clamp(s + 2, s, e))
    return a, b

# -----------------------------
# 트리거(충/합/귀인/형/공망) 해석
# -----------------------------
TRIGGER_MAP: Dict[str, str] = {
    "충": "shock",     # 급변/전환
    "형": "strain",    # 마찰/압박(급변 성격 포함)
    "합": "merge",     # 성사/연결(앞당김)
    "귀인": "help",    # 도움/지지(앞당김)
    "공망": "delay",   # 공회전/허탈(지연)
}

def analyze_triggers(tags: Optional[List[str]]) -> Dict[str, int]:
    """
    tags(list[str]) 안의 키워드로 트리거 카운트 추출
    """
    counts = {"help": 0, "merge": 0, "shock": 0, "strain": 0, "delay": 0}
    if not tags:
        return counts

    for t in tags:
        for k, v in TRIGGER_MAP.items():
            if k in t:
                counts[v] += 1
    return counts

def infer_focus_window(start_age: int, end_age: int, hit_score: int = 0) -> str:
    """
    체감 구간(나이) 판단:
    - hit_score>=2: 초반 상반기
    - hit_score==1: 초반 하반기 또는 중반 초입
    - hit_score==0: 중반~후반
    """
    early, mid, late = split_phases(start_age, end_age)
    e1, e2 = split_early_half(start_age, end_age)

    if hit_score >= 2:
        return f"{_range_text(e1[0], e1[1])}(초반 상반기)"
    if hit_score == 1:
        return f"{_range_text(e2[0], e2[1])}(초반 하반기) 또는 {_range_text(mid[0], mid[0])}(중반 초입)"
    return f"{_range_text(mid[0], mid[1])}(중반) 이후 {_range_text(late[0], late[1])}(후반)"

def build_trigger_sentence(counts: Dict[str, int]) -> str:
    """
    트리거 조합에 따라 '앞당김/지연/급변' 문장 차등 생성
    우선순위:
      1) 공망(delay) 강하면: 지연 경고
      2) 충/형(shock/strain) 있으면: 급변 경고(+관리 팁)
      3) 귀인/합(help/merge) 있으면: 앞당김 안내
      4) 없으면: 중립
    """
    help_n  = counts["help"]
    merge_n = counts["merge"]
    shock_n = counts["shock"]
    strain_n= counts["strain"]
    delay_n = counts["delay"]

    # 1) 지연(공망)
    if delay_n >= 1 and (help_n + merge_n) == 0:
        return (
            "여기에는 **공망 성격(지연/공회전)**이 섞일 수 있어요. "
            "초반엔 결과가 비어 보이거나 헛힘이 들 수 있으니, "
            "**증빙·계약·현금흐름**부터 단단히 잡고 ‘늦게 열리는 운’으로 운영하세요."
        )

    # 2) 급변(충/형)
    if (shock_n + strain_n) >= 1:
        return (
            "이 구간은 **충/형 성격(급변·전환)**이 있어 체감이 ‘사건처럼’ 올 수 있어요. "
            "이직·이사·관계 재정렬 같은 변화가 빠르게 들어올 수 있으니, "
            "**결정은 빠르게 하되 리스크(돈/문서/몸)**는 잠깐 더 점검하세요."
        )

    # 3) 앞당김(귀인/합)
    if (help_n + merge_n) >= 1:
        return (
            "여기에는 **귀인/합 성격(연결·성사)**이 있어 체감 시점이 **앞당겨질 가능성**이 큽니다. "
            "사람·제안·협업이 ‘문을 여는 열쇠’가 되니, "
            "소개·네트워크·기회 제안에는 응답 속도를 조금 올려보세요."
        )

    # 4) 중립
    return "체감은 **정석 흐름(초→중→후)**대로 오기 쉬우니, 초반엔 기반 정리, 중반에 확장, 후반에 결실로 잡으면 안정적입니다."
def _to_int_age(v) -> int:
    """
    '34', 34, 34.0, '1.53', '11.53', '34세' 등
    다양한 입력을 '정수 나이'로 안전 변환
    """
    if v is None:
        return 0

    # 이미 숫자면
    if isinstance(v, (int,)):
        return int(v)
    if isinstance(v, (float,)):
        return int(v)

    s = str(v).strip()

    # '34세' 같은 글자 제거
    for ch in ["세", "살", "age", "AGE"]:
        s = s.replace(ch, "")
    s = s.strip()

    # '1.53' 같은 소수 문자열 처리
    try:
        return int(float(s))
    except Exception:
        # 마지막 방어: 숫자만 추출
        digits = "".join([c for c in s if c.isdigit() or c == "."])
        return int(float(digits)) if digits else 0

def timing_sentence(
    start_age: int,
    end_age: int,
    tags: Optional[List[str]] = None,
    hit_score: int = 0,
) -> str:
    
    """
    최종 체감 문장(트리거 세분화 버전)
    """
    start_age = _to_int_age(start_age)
    end_age = _to_int_age(end_age)

    window = infer_focus_window(start_age, end_age, hit_score)

    counts = analyze_triggers(tags)
    trigger_line = build_trigger_sentence(counts)

    base = f"이 대운의 체감 포인트는 **{window}** 쪽에 먼저 걸립니다."
    return f"{base}\n- {trigger_line}"
