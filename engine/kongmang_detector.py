# kongmang_detector.py
# ---------------------------------------------------------
# 운트임 공망(空亡) 전용 모듈
# - 일주 기준 공망 지지 계산
# - 원국(사주팔자) 공망 태깅
# - 대운/세운 공망 태깅
# - 리포트용 요약 텍스트 생성 (기본 버전)
# ---------------------------------------------------------
# ⚠️ 사용 전 확인할 것:
# 1) 천간/지지 표기 방식 (한자 vs 한글) 맞추기
# 2) 사주 엔진에서 쓰는 Pillar / TenGod / SixKin 구조에 연결하기

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

# ---------------------------------------------------------
# 0. 기본 상수 정의
# ---------------------------------------------------------

# 천간(한자 기준) – 엔진에서 '갑','을'을 쓰면 그쪽에 맞게 바꿔도 됨
STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

# 지지(한자 기준)
BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

KOR_TO_HANJA_STEM = {
    "갑":"甲","을":"乙","병":"丙","정":"丁","무":"戊","기":"己","경":"庚","신":"辛","임":"壬","계":"癸"
}
KOR_TO_HANJA_BRANCH = {
    "자":"子","축":"丑","인":"寅","묘":"卯","진":"辰","사":"巳","오":"午","미":"未","신":"申","유":"酉","술":"戌","해":"亥"
}

# ---------------------------------------------------------
# 1. 데이터 구조 (엔진과 연결용 최소형)
# ---------------------------------------------------------

@dataclass
class Pillar:
    """사주의 한 기둥(년/월/일/시)을 표현하는 최소 구조."""
    kind: str              # "year", "month", "day", "hour", "luck", "year_luck" 등
    stem: str              # 천간 (예: "甲")
    branch: str            # 지지 (예: "子")
    ten_god: Optional[str] = None   # 이 기둥 지지 기준 십신 (예: "정재", "편관" 등)
    six_kin: Optional[str] = None   # 육친명 (예: "부", "모", "자", "배우자" 등)
    is_void: bool = False          # 공망 여부 (지지 기준)
    void_reason: Optional[str] = None  # 왜 공망인지 간단 설명


@dataclass
class VoidInfo:
    """일주 기준 공망 정보 + 원국/운 공망 요약."""
    day_stem: str
    day_branch: str
    void_branches: Tuple[str, str]      # (공망1, 공망2)
    natal_void_pillars: List[Pillar]    # 원국에서 공망인 기둥들
    luck_void_pillars: List[Pillar]     # 대운/세운 등 운에서 공망인 기둥들
    summary: Dict[str, str]             # 리포트용 요약 문장들


# ---------------------------------------------------------
# 2. 공망 계산 로직 (일주 기준)
# ---------------------------------------------------------

def get_stem_index(stem: str) -> int:
    """
    천간 인덱스 (1~10) 반환.
    - 블로그 글에서처럼 甲乙丙丁戊己庚辛壬癸 = 1~10으로 번호 매긴 것을 구현.
    """
    try:
        stem = str(stem).strip()
        stem = KOR_TO_HANJA_STEM.get(stem, stem)
        return STEMS.index(stem) + 1
    except ValueError:
        raise ValueError(f"알 수 없는 천간: {stem}")


def get_branch_index(branch: str) -> int:
    """
    지지 인덱스 (1~12) 반환.
    - 子丑寅卯辰巳午未申酉戌亥 = 1~12
    """
    try:
        branch = str(branch).strip()
        branch = KOR_TO_HANJA_BRANCH.get(branch, branch)
        return BRANCHES.index(branch) + 1
    except ValueError:
        raise ValueError(f"알 수 없는 지지: {branch}")


def calc_void_branches(day_stem: str, day_branch: str) -> Tuple[str, str]:
    """
    ✔ 블로그에 나온 공식 그대로 구현:
        - 천간 1~10, 지지 1~12 번호 부여
        - m = branch_no - stem_no
        - m ≤ 0 이면 +12 반복
        - 그 결과 m-1, m 번에 해당하는 두 지지가 공망

      예) 庚午일주:
        stem_no = 7, branch_no = 7
        m = 7 - 7 = 0 → +12 = 12
        → 11, 12번 지지 = 戌, 亥 → 戌亥 공망
    """
    stem_no = get_stem_index(day_stem)
    branch_no = get_branch_index(day_branch)

    m = branch_no - stem_no
    while m <= 0:
        m += 12

    void2_no = m              # 두 번째 공망
    void1_no = m - 1          # 첫 번째 공망
    if void1_no <= 0:
        void1_no += 12

    void1 = BRANCHES[void1_no - 1]
    void2 = BRANCHES[void2_no - 1]
    return void1, void2


# ---------------------------------------------------------
# 3. 원국/운 기둥에 공망 태깅
# ---------------------------------------------------------

def tag_void_on_pillars(
    pillars: List[Pillar],
    void_branches: Tuple[str, str],
    is_luck_layer: bool = False
) -> List[Pillar]:
    """
    각 기둥의 지지가 공망인지 체크하고 플래그를 세팅.
    - void_branches: (공망1, 공망2)
    - is_luck_layer: True면 대운/세운 등 '운' 기둥이라고 표기
    """
    vb1, vb2 = void_branches
    tagged: List[Pillar] = []

    for p in pillars:
        is_void = p.branch in (vb1, vb2)
        if is_void:
            reason = "원국 공망" if not is_luck_layer else "운 공망"
            tagged_p = Pillar(
                kind=p.kind,
                stem=p.stem,
                branch=p.branch,
                ten_god=p.ten_god,
                six_kin=p.six_kin,
                is_void=True,
                void_reason=reason
            )
        else:
            tagged_p = p
        tagged.append(tagged_p)

    return tagged


# ---------------------------------------------------------
# 4. 공망 요약 해석 (기본버전)
#    👉 나중에 운트임 스타일로 더 감성/전문 버전으로 바꿔도 됨
# ---------------------------------------------------------

def summarize_natal_void(pillars: List[Pillar], void_branches: Tuple[str, str]) -> str:
    """
    원국 공망 요약.
    - 어떤 기둥(kind)과 육친(six_kin/ten_god)이 공망인지 간단 요약.
    """
    if not pillars:
        return "원국에서 공망 작용은 두드러지지 않습니다."

    parts = []
    vb1, vb2 = void_branches
    parts.append(f"이 사주는 일주 기준으로 **{vb1}·{vb2} 공망** 구조입니다.")

    affected = [p for p in pillars if p.is_void]
    if not affected:
        parts.append("다만 원국 네 기둥에는 직접적인 공망 지지가 없어, 공망의 영향은 비교적 약한 편입니다.")
        return " ".join(parts)

    # 기둥/육친 목록 만들기
    detail_list = []
    for p in affected:
        label = p.kind
        if p.six_kin:
            label += f"({p.six_kin})"
        elif p.ten_god:
            label += f"({p.ten_god})"
        detail_list.append(label)

    parts.append("원국에서는 다음 자리가 공망의 영향을 받습니다:")
    parts.append(" · " + ", ".join(detail_list))

    parts.append(
        "해당 영역은 한 번에 순조롭게 채워지기보다는 **지연·반복·조정**을 거쳐 서서히 안정되는 패턴으로 해석할 수 있습니다."
    )

    return " ".join(parts)


def summarize_luck_void(pillars: List[Pillar]) -> str:
    """
    대운/세운 공망 요약.
    """
    affected = [p for p in pillars if p.is_void]
    if not affected:
        return "현재 운에서는 공망 작용이 두드러지지 않습니다."

    parts = []
    kinds = set(p.kind for p in affected)
    parts.append("현재 운에서는 다음 영역에 공망이 작용합니다:")
    parts.append(" · " + ", ".join(sorted(kinds)))
    parts.append(
        "이 시기에는 **일이 한 번에 매듭지어지기보다는, 재도전·수정·보완** 과정을 거친 뒤 성취되는 패턴으로 보는 것이 좋습니다."
    )
    parts.append(
        "큰 성과를 욕심내기보다는, 내실을 다지고 틈을 메우는 시기로 활용하면 공망이 오히려 안전장치처럼 작동할 수 있습니다."
    )
    return " ".join(parts)


# ---------------------------------------------------------
# 5. 통합 진입 함수
# ---------------------------------------------------------

def analyze_kongmang(
    natal_pillars: List[Pillar],
    luck_pillars: Optional[List[Pillar]] = None,
    day_pillar: Optional[Pillar] = None,
) -> VoidInfo:
    """
    공망(空亡) 전체 분석을 한 번에 수행하는 진입 함수.

    사용법(예시):
        day_pillar = Pillar(kind="day", stem="庚", branch="午")
        natal = [year_p, month_p, day_p, hour_p]
        luck = [daewoon_p, sewun_p]  # 필요하면

        void_info = analyze_kongmang(natal, luck, day_pillar)

    반환:
        - day_stem, day_branch
        - void_branches (공망 지지 2개)
        - natal_void_pillars (공망 플래그가 찍힌 원국 기둥들)
        - luck_void_pillars (운 공망 기둥들)
        - summary (원국/운 공망 요약문)
    """

    if day_pillar is None:
        # 보통 natal_pillars에서 kind == "day"를 찾아 씀
        dp_candidates = [p for p in natal_pillars if p.kind == "day"]
        if not dp_candidates:
            raise ValueError("일주(일간·일지) 정보가 필요합니다. day_pillar를 넘겨 주세요.")
        day_pillar = dp_candidates[0]

    void_branches = calc_void_branches(day_pillar.stem, day_pillar.branch)

    # 원국에 공망 태깅
    natal_tagged = tag_void_on_pillars(natal_pillars, void_branches, is_luck_layer=False)

    # 운(대운/세운 등)이 있으면 거기도 공망 태깅
    luck_tagged: List[Pillar] = []
    if luck_pillars:
        luck_tagged = tag_void_on_pillars(luck_pillars, void_branches, is_luck_layer=True)

    # 요약 생성
    natal_summary = summarize_natal_void(natal_tagged, void_branches)
    luck_summary = summarize_luck_void(luck_tagged) if luck_tagged else "현재 운 공망 정보 없음."

    summary = {
        "natal": natal_summary,
        "luck": luck_summary,
    }

    return VoidInfo(
        day_stem=day_pillar.stem,
        day_branch=day_pillar.branch,
        void_branches=void_branches,
        natal_void_pillars=natal_tagged,
        luck_void_pillars=luck_tagged,
        summary=summary,
    )


