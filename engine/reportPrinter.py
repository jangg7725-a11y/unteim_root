# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, Any, List, Optional, cast
import argparse
from datetime import date, datetime
from collections import Counter

# ── optional color support (설치되어 있으면 사용; 없으면 흑백) ───────────────
try:
    from colorama import init as colorama_init, Fore, Style  # type: ignore
    colorama_init()
    _COLOR_OK = True
except Exception:
    class _No:
        RESET_ALL = ""
    class _Fore(_No):
        RED = GREEN = CYAN = YELLOW = MAGENTA = BLUE = WHITE = ""
        LIGHTBLACK_EX = LIGHTWHITE_EX = ""
    class _Style(_No):
        BRIGHT = NORMAL = DIM = ""
    Fore, Style = _Fore(), _Style()
    _COLOR_OK = False

from .interpreter import interpret_day
from .daewoon_calculator import Gender, YinYang
from .luckTimeline import build_daewoon_sewun_timeline, SewunBoundary

# 🔗 이슈 태깅/천직 추천 모듈
from .issue_classifier import classify_issues
from .vocation_recommender import recommend_vocations

# 전역 args
args: argparse.Namespace

# 아이콘 매핑(이슈)
TAG_ICON = {
    "health": "🩺",
    "love": "💕",
    "money": "💰",
    "fraud": "🛑",
    "lawsuit": "⚖️",
    # 확장 여지: "career":"📈","move":"🧭","family":"🏠" ...
}

# ──────────────────────────────────────────────────────────────────────────────
# 유틸
# ──────────────────────────────────────────────────────────────────────────────
def _print_rule(width: int = 90) -> None:
    if _COLOR_OK and getattr(args, "color", False):
        print(Fore.WHITE + Style.DIM + ("─" * width) + Style.RESET_ALL)
    else:
        print("─" * width)

def _today() -> date:
    """--today YYYY-MM-DD 지정 시 그 날짜를 오늘로 사용. 없으면 시스템 날짜."""
    t = getattr(args, "today", None)
    if t:
        try:
            y, m, d = map(int, str(t).split("-"))
            return date(y, m, d)
        except Exception:
            return date.today()
    return date.today()

def _find_year_node(data: Dict[str, Any], target_year: int) -> Optional[Dict[str, Any]]:
    for dnode in data.get("daewoon", []):
        for yn in dnode.get("years", []):
            if int(yn["year"]) == int(target_year):
                return yn
    return None

def _wk_str(iso: str) -> str:
    WK = ["월","화","수","목","금","토","일"]
    try:
        y, m, d = map(int, iso.split("-"))
        return WK[datetime(y, m, d).weekday()]
    except Exception:
        return "?"

# ── 요일별 색상(옵션) ─────────────────────────────────────────────────────────
def _weekday_color(weekday: str) -> str:
    if not (_COLOR_OK and getattr(args, "color", False)):
        return ""
    if weekday == "일":
        return Fore.RED + Style.BRIGHT
    if weekday == "토":
        return Fore.BLUE + Style.BRIGHT
    return Fore.WHITE

# ── 라인 포매터: 정렬 + 오늘강조 + 주말 흐림/아이콘 + 이슈아이콘 ────────────
def _format_day_line(
    date_mmdd: str,
    weekday: str,
    day_ganji: str,
    text: str,
    *,
    is_today: bool,
    is_weekend: bool,
    use_icons: bool,
    dim_weekend: bool,
    tag_icons: str
) -> str:
    # 오늘/주말 아이콘
    base_icon = ""
    if use_icons:
        if is_today:
            base_icon = "📌"
        elif is_weekend:
            base_icon = "🌙"
        else:
            base_icon = " "

    # 색상
    prefix = ""
    suffix = Style.RESET_ALL if (_COLOR_OK and getattr(args, "color", False)) else ""
    if _COLOR_OK and getattr(args, "color", False):
        if is_today:
            prefix = Fore.YELLOW + Style.BRIGHT     # 오늘 노랑·굵게
        elif is_weekend and dim_weekend:
            prefix = Fore.CYAN + Style.DIM          # 주말 흐림
        else:
            prefix = _weekday_color(weekday)

    # 오늘 별표
    if is_today:
        text = (text + " ★").strip()

    # 고정폭 정렬
    col_date = date_mmdd.ljust(6)
    col_wk   = weekday.center(2)
    col_gj   = day_ganji.center(4)

    icons = f" {tag_icons}" if tag_icons else ""
    return f"{base_icon} {prefix}{col_date} {col_wk} {col_gj} {text}{icons}{suffix}"

# 해석문 키워드 기반 보조 태깅(실데이터 없을 때 보완)
_KEYWORDS = [
    ("health", ["건강","검진","수술","시술","피로","염증","통증","회복","휴식","면역"]),
    ("love",   ["연애","인연","만남","재회","이별","갈등","배우자","연인"]),
    ("money",  ["재물","수입","지출","투자","매매","보너스","수익","횡재"]),
    ("fraud",  ["사기","손실","도난","분실","파손","손재"]),
    ("lawsuit",["소송","법무","계약","세금","신고","분쟁","문서"]),
]
def _tags_from_text(text: str) -> List[str]:
    tags: List[str] = []
    t = (text or "").replace(" ", "")
    for tag, keys in _KEYWORDS:
        if any(k in t for k in keys):
            tags.append(tag)
    # 중복 제거(순서 유지)
    return list(dict.fromkeys(tags))

# ──────────────────────────────────────────────────────────────────────────────
# 1) 요약
# ──────────────────────────────────────────────────────────────────────────────
def print_timeline_summary(**kwargs) -> None:
    data: Dict[str, Any] = build_daewoon_sewun_timeline(
        include_months=False, include_days=False, **kwargs
    )
    meta = data.get("__meta__", {})
    sad = meta.get("start_age_detail", {})
    title = "=== 요약 ==="
    if _COLOR_OK and getattr(args, "color", False):
        title = Fore.CYAN + Style.BRIGHT + title + Style.RESET_ALL
    print(title)
    print(f"- 기준: 대운(10년) + 세운(연간지)")
    print(f"- 대운 시작세: {sad.get('years','?')}세 {sad.get('months',0)}개월 (절입일 보정)")
    print(f"- 진행방향: {meta.get('direction','?')}")
    print(f"- 시작 기준: {meta.get('base_mode','?')} | 월주 간지: {meta.get('base_pillar_ganji','?')}")
    print(f"- 세운 경계: {meta.get('sewun_boundary','ipchun')} ({meta.get('sewun_label_note','')})")
    _print_rule()
    print(f"{'대운나이(10년)':<14} | {'대운간지':<4} | 세운(연:간지)")
    _print_rule()
    for row in data.get("daewoon", []):
        age = int(row["age"]); deka = str(row["ganji"])
        ylist = ", ".join(f"{y['year']}:{y['ganji']}" for y in row.get("years", []))
        print(f"{f'{age}~{age+9}':<14} | {deka:<4} | {ylist}")
    _print_rule()

# ──────────────────────────────────────────────────────────────────────────────
# 2) 월운 표
# ──────────────────────────────────────────────────────────────────────────────
def print_month_table_for_year(target_year: int, **kwargs) -> None:
    data: Dict[str, Any] = build_daewoon_sewun_timeline(
        include_months=True, include_days=False, **kwargs
    )
    boundary = data["__meta__"].get("sewun_boundary","ipchun")
    meta_note = data["__meta__"].get("sewun_label_note","")
    header = f"== 월운 (기준: {boundary} | {meta_note} | 라벨연도={target_year}) =="
    if _COLOR_OK and getattr(args, "color", False):
        header = Fore.CYAN + Style.BRIGHT + header + Style.RESET_ALL
    print(header)

    yn = _find_year_node(data, target_year)
    if not yn:
        print("(해당 연도 없음)"); return

    _print_rule()
    head = f"{'월(인덱스)':<10} {'월간지':<4} {'시작일':<12} {'종료일(포함)':<12}"
    if _COLOR_OK and getattr(args, "color", False):
        head = Style.BRIGHT + head + Style.RESET_ALL
    print(head)
    _print_rule()

    today_iso = _today().isoformat()
    for m in yn.get("months", []):
        month_idx = int(m["month_idx"])
        month_label = f"({month_idx:02d})"
        row = f"{month_idx:>2}월{month_label:<6} {m['ganji']:<4} {m['start']:<12} {m['end_inclusive']:<12}"
        if getattr(args, "highlight_today", False) and (m["start"] <= today_iso <= m["end_inclusive"]) and _COLOR_OK and getattr(args, "color", False):
            row = (Fore.YELLOW + Style.BRIGHT) + row + Style.RESET_ALL + "  ← 오늘 포함"
        print(row)
    _print_rule()

# ──────────────────────────────────────────────────────────────────────────────
# 3) 월운 + 일운 (이슈 태그 + 월간 요약 + 적성/천직 추천)
# ──────────────────────────────────────────────────────────────────────────────
def print_month_and_days(
    target_year: int,
    month_idx: Optional[int],
    show_days: bool,
    preview: int,
    **kwargs
) -> None:
    """
    월운/일운 출력 + 이슈 태그 + 월간 요약 + 적성/천직 추천
    """
    explain = bool(kwargs.pop("explain", False))

    data: Dict[str, Any] = build_daewoon_sewun_timeline(
        include_months=True,
        include_days=show_days,
        **kwargs
    )
    boundary = data["__meta__"].get("sewun_boundary", "ipchun")
    meta_note = data["__meta__"].get("sewun_label_note", "")
    header = f"== 월운/일운 (기준: {boundary} | {meta_note} | 라벨연도={target_year}) =="
    if _COLOR_OK and getattr(args, "color", False):
        header = Fore.CYAN + Style.BRIGHT + header + Style.RESET_ALL
    print(header)

    yn = _find_year_node(data, target_year)
    if not yn:
        print("(해당 연도 없음)"); 
        return

    months: List[Dict[str, Any]] = yn.get("months", [])
    if month_idx:
        months = [m for m in months if int(m["month_idx"]) == int(month_idx)]
        if not months:
            print(f"(월 인덱스 {month_idx} 없음)"); 
            return

    # 헤더(일운 테이블)
    if show_days:
        _print_rule()
        head = f"{'날짜':<6} {'요일':<2} {'일간지':<4} 해석"
        if _COLOR_OK and getattr(args, "color", False):
            head = Style.BRIGHT + head + Style.RESET_ALL
        print(head)
        _print_rule()

    today_iso = _today().isoformat()
    base_gj = data.get("__meta__", {}).get("base_pillar_ganji", "")
    use_icons   = bool(getattr(args, "icons", False))
    dim_weekend = bool(getattr(args, "weekend_dim", False))
    show_today  = bool(getattr(args, "highlight_today", False))

    for m in months:
        # 월 헤더
        month_header = f"{m['month_idx']:>2}월 {m['ganji']:>4} : {m['start']} ~ {m['end_inclusive']}"
        if show_today and (m["start"] <= today_iso <= m["end_inclusive"]) and _COLOR_OK and getattr(args, "color", False):
            month_header = (Fore.YELLOW + Style.BRIGHT) + "★ " + month_header + Style.RESET_ALL
        print(month_header)

        # 월간 이슈 집계
        month_tag_counter: Counter[str] = Counter()

        if show_days:
            days = m.get("days", [])
            if preview > 0:
                days = days[:preview]

            # 월간 간지(룰용)
            month_ganji = m.get("ganji","")

            for d in days:
                di = d['date'][5:]      # "MM-DD"
                gj = d.get('ganji','')
                wk = _wk_str(d['date'])
                weekend = (wk in ("토","일"))

                # 기본 해석문
                tip = interpret_day(gj, base_gj) if explain else ""

                # 1) 정규 룰(오행/십신/신살 데이터 연결 전, 빈 값으로 호출)
                oheng_balance: Dict[str, int] = {}   # TODO: 실제 오행 분석 연결
                shinsal: List[str] = []             # TODO: 실제 신살 분석 연결
                sipshin: List[str] = []             # TODO: 실제 십신 분석 연결
                tags = classify_issues(oheng_balance, shinsal, sipshin, month_ganji)

                # 2) 해석문 키워드 보조 태깅
                if tip:
                    for t in _tags_from_text(tip):
                        if t not in tags:
                            tags.append(t)

                # 월 집계
                for t in tags:
                    month_tag_counter[t] += 1

                # 아이콘 문자열
                tag_icons = " ".join(TAG_ICON.get(t, "") for t in tags if t in TAG_ICON).strip()

                # 출력
                line = _format_day_line(
                    di, wk, gj, tip,
                    is_today=(d['date'] == today_iso),
                    is_weekend=weekend,
                    use_icons=use_icons,
                    dim_weekend=dim_weekend,
                    tag_icons=tag_icons
                )
                print(line)

            # 월간 요약(상위 1~3개)
            if month_tag_counter:
                _print_rule()
                top = month_tag_counter.most_common(3)
                summ = " · ".join(f"{TAG_ICON.get(k,'')} {k}×{v}".strip() for k, v in top)
                if _COLOR_OK and getattr(args, "color", False):
                    summ = Fore.CYAN + Style.BRIGHT + summ + Style.RESET_ALL
                print("월간 이슈 요약:", summ)

        _print_rule()

    # ── 여기서 적성/천직 추천 블록 추가 ──────────────────────────────────────
    print_vocation_block(data.get("__meta__", {}))
    _print_rule()

# ──────────────────────────────────────────────────────────────────────────────
# 4) 적성/천직 추천 섹션
# ──────────────────────────────────────────────────────────────────────────────
def print_vocation_block(meta: Dict[str, Any]) -> None:
    """
    meta에서 필요한 정보를 모아 적성/천직 추천을 출력.
    실제 엔진 연결 전까지는 안전한 기본값/추정값으로 동작.
    """
    # TODO: 실제 엔진 결과 연결 시 meta에서 값 주입
    day_master = meta.get("day_stem", "무")  # 일간(임시)
    five = meta.get("five_elements_balance", {"목": 1, "화": 1, "토": 0, "금": 0, "수": 1})
    ten  = meta.get("ten_gods_balance", {"정재": 1, "편재": 1, "정관": 0, "편관": 0, "정인": 1, "편인": 0, "식신": 1, "상관": 0, "비견": 0, "겁재": 0})
    useful = meta.get("useful_elements", ["목","화"])
    stage12 = meta.get("twelve_stage", "관대")

    recs = recommend_vocations(day_master, five, ten, useful, stage12)

    title = "== 적성/천직 추천 =="
    if _COLOR_OK and getattr(args, "color", False):
        title = Fore.CYAN + Style.BRIGHT + title + Style.RESET_ALL
    print(title)

    for name, score, reasons in recs[:5]:
        line = f"- {name}  점수: {score:+d}  근거: {', '.join(reasons) if reasons else '기본 적합'}"
        print(line)

# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────
def main():
    global args
    ap = argparse.ArgumentParser(description="운트임 리포트 프린터 (이슈 태그 + 천직 추천 통합)")
    ap.add_argument("--mode", choices=["summary","month-table","month-days"], default="summary")

    # 기준
    ap.add_argument("--sewun", choices=["ipchun","jan1"], default="ipchun")

    # 실전 입력
    ap.add_argument("--birth-year", type=int, required=True)
    ap.add_argument("--gender", choices=["남","여"], required=True)
    ap.add_argument("--yinyang", choices=["양","음"], required=True)
    ap.add_argument("--bm", type=int); ap.add_argument("--bd", type=int)
    ap.add_argument("--bh", type=int); ap.add_argument("--bmin", type=int)
    ap.add_argument("--cycles", type=int, default=8)

    # 월/일운 옵션
    ap.add_argument("--year", type=int, help="월운/일운 라벨 연도")
    ap.add_argument("--month-idx", type=int, help="특정 월 인덱스(1~12)")
    ap.add_argument("--show-days", action="store_true", help="일운까지 표시")
    ap.add_argument("--preview", type=int, default=0, help="일운 미리보기 갯수 (0=전부)")

    # 포맷 옵션
    ap.add_argument("--explain", action="store_true", help="일운 한 줄 해석 추가")
    ap.add_argument("--highlight-today", action="store_true", help="오늘 날짜/월 하이라이트")
    ap.add_argument("--weekend-dim", action="store_true", help="주말 흐리게 표시")
    ap.add_argument("--color", action="store_true", help="색상 출력 활성화")
    ap.add_argument("--icons", action="store_true", help="📌/🌙 + 태그 아이콘 표시")

    # 임의의 오늘 날짜
    ap.add_argument("--today", type=str, help="임의의 오늘 날짜 (YYYY-MM-DD)")

    args = ap.parse_args()

    common_kwargs = dict(
        birth_year=args.birth_year,
        gender=cast(Gender, args.gender),
        yin_yang=cast(YinYang, args.yinyang),
        birth_month=args.bm, birth_day=args.bd,
        birth_hour=args.bh, birth_minute=args.bmin,
        num_cycles=args.cycles,
        use_month_pillar=True,
        sewun_boundary=cast(SewunBoundary, args.sewun),
    )

    if args.mode == "summary":
        print_timeline_summary(**common_kwargs)
    elif args.mode == "month-table":
        if not args.year:
            raise SystemExit("--year 필요")
        print_month_table_for_year(args.year, **common_kwargs)
    else:
        if not args.year:
            raise SystemExit("--year 필요")
        print_month_and_days(
            args.year,
            args.month_idx,
            args.show_days,
            args.preview,
            explain=args.explain,   # 출력 로직에서만 사용
            **common_kwargs
        )

if __name__ == "__main__":
    main()
