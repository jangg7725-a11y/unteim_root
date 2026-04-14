# -*- coding: utf-8 -*-
"""
data/fortune_app_dataset_ko_2000_deduped.json → frontend/public/data/fortune_lines.json

- 전역 중복 문장 제거(정규화된 텍스트 기준)
- 피드 카테고리 id(monthly, saju, love, work, mind, all)별 버킷에 배치
- 소스에 category/태그가 없으면 본문 키워드로 보조 분류(여러 버킷 가능)

사용: 프로젝트 루트에서
  python scripts/build_fortune_lines.py
옵션:
  --source PATH   기본: data/fortune_app_dataset_ko_2000_deduped.json
  --out PATH      기본: frontend/public/data/fortune_lines.json
  --no-infer      키워드로 버킷 추정하지 않음(명시 태그만, 나머지는 all)
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = ROOT / "data" / "fortune_app_dataset_ko_2000_deduped.json"
DEFAULT_OUT = ROOT / "frontend" / "public" / "data" / "fortune_lines.json"

CAT_IDS = ("all", "monthly", "saju", "love", "work", "mind")

# 키워드 → 카테고리 (보조 분류)
KEYWORD_BUCKETS: List[Tuple[str, str]] = [
    ("love", "연애|사랑|연인|배우자|결혼|인연|소개팅|썸|이별|재회"),
    ("work", "직장|업무|돈|재물|투자|사업|승진|연봉|프로젝트|커리어"),
    ("mind", "마음|감정|스트레스|휴식|내면|성향|불안|긴장|심리"),
    ("monthly", "이번 달|이번달|오늘|이번 주|이번주|월간|월운"),
    (
        "saju",
        "사주|팔자|대운|세운|월주|일간|십성|신살|명리|원국|용신|오행|성운|월건|궁합",
    ),
]

# category 필드 문자열 → id
LABEL_TO_ID: List[Tuple[str, str]] = [
    ("love", "love|연애|사랑|연인|인연|heart"),
    ("work", "work|일|직장|재물|돈|job|money"),
    ("mind", "mind|마음|성향|감정|mental"),
    ("monthly", "monthly|이번달|이번 달|달|오늘|calendar|today"),
    ("saju", "saju|사주|팔자|운세|fortune"),
    ("all", "all|전체|general|default"),
]

# fortune_app_dataset_ko_2000 등: schema의 category enum → 피드 버킷
SOURCE_CATEGORY_TO_IDS: Dict[str, Set[str]] = {
    "today": {"monthly", "all"},
    "emotion": {"mind", "all"},
    "relationship": {"love", "all"},
    "love": {"love", "all"},
    "work": {"work", "all"},
    "study": {"work", "all"},
    "money": {"work", "all"},
    "health": {"mind", "all"},
    "change": {"mind", "all"},
    "advice": {"all"},
}


def _map_category_token(val: Any) -> Set[str]:
    if val is None:
        return set()
    s = str(val).strip()
    if not s:
        return set()
    key = s.casefold()
    if key in SOURCE_CATEGORY_TO_IDS:
        return set(SOURCE_CATEGORY_TO_IDS[key])
    lbl = _labels_from_field(s)
    return set(lbl) if lbl else set()


def _norm_text(s: str) -> str:
    s = unicodedata.normalize("NFC", s.strip())
    s = re.sub(r"\s+", " ", s)
    return s


def _dedupe_key(s: str) -> str:
    return _norm_text(s).casefold()


def _match_any(pattern: str, text: str) -> bool:
    return re.search(pattern, text, re.IGNORECASE) is not None


def _labels_from_field(val: Any) -> List[str]:
    if val is None:
        return []
    if isinstance(val, (int, float)):
        return []
    if isinstance(val, list):
        out: List[str] = []
        for x in val:
            out.extend(_labels_from_field(x))
        return out
    s = str(val).strip()
    if not s:
        return []
    for cid, pat in LABEL_TO_ID:
        if _match_any(pat, s):
            return [cid]
    return []


def _infer_from_text(text: str) -> Set[str]:
    found: Set[str] = set()
    for cid, pat in KEYWORD_BUCKETS:
        if _match_any(pat, text):
            found.add(cid)
    return found


def _extract_text(obj: Dict[str, Any]) -> Optional[str]:
    for key in ("text", "sentence", "message", "content", "body", "quote", "line", "ko", "ko_text"):
        v = obj.get(key)
        if isinstance(v, str) and v.strip():
            return v
    return None


def _iter_raw_entries(data: Any) -> Iterable[Any]:
    if isinstance(data, list):
        yield from data
        return
    if not isinstance(data, dict):
        return
    for key in ("sentences", "items", "data", "lines", "quotes", "records", "rows"):
        v = data.get(key)
        if isinstance(v, list):
            yield from v
            return
    # 단일 래퍼 없이 키가 모두 숫자/문자열인 경우
    if data and all(isinstance(k, str) for k in data.keys()):
        for v in data.values():
            if isinstance(v, (str, dict)):
                yield v


def _parse_entry(raw: Any) -> List[Tuple[str, Set[str]]]:
    """(원문, 카테고리 집합) — 한 줄에 여러 버킷 가능"""
    if isinstance(raw, str):
        t = _norm_text(raw)
        if not t:
            return []
        return [(t, {"all"})]

    if not isinstance(raw, dict):
        return []

    if raw.get("active") is False:
        return []

    text = _extract_text(raw)
    if not text:
        return []
    t = _norm_text(text)
    if not t:
        return []

    cats: Set[str] = set()

    for key in ("categoryIds", "categories", "tags"):
        v = raw.get(key)
        if isinstance(v, list):
            for x in v:
                cats |= _map_category_token(x)
        elif v is not None:
            cats |= _map_category_token(v)

    for key in ("category", "cat", "theme", "type", "tag", "group", "bucket", "slot"):
        v = raw.get(key)
        if isinstance(v, list):
            for x in v:
                cats |= _map_category_token(x)
        elif v is not None:
            cats |= _map_category_token(v)

    if not cats:
        cats = {"all"}
    else:
        cats.add("all")

    return [(t, cats)]


def gather_entries(data: Any) -> List[Tuple[str, Set[str]]]:
    out: List[Tuple[str, Set[str]]] = []
    for raw in _iter_raw_entries(data):
        out.extend(_parse_entry(raw))
    return out


def build_buckets(
    entries: List[Tuple[str, Set[str]]],
    infer: bool,
) -> Dict[str, List[str]]:
    """전역 텍스트 중복 제거(동일 정규화 문장은 카테고리 합침) 후 버킷별 리스트(순서 유지)"""
    merged: Dict[str, Tuple[str, Set[str]]] = {}
    order: List[str] = []
    for text, cats in entries:
        key = _dedupe_key(text)
        if not key:
            continue
        if key in merged:
            _t, prev = merged[key]
            prev |= set(cats)
        else:
            merged[key] = (text, set(cats))
            order.append(key)

    unique_rows: List[Tuple[str, Set[str]]] = []
    for key in order:
        text, row_cats = merged[key]
        if infer:
            row_cats |= _infer_from_text(text)
            row_cats.add("all")
        if row_cats == set() or row_cats == {"all"}:
            row_cats = {"all"}
        unique_rows.append((text, row_cats))

    buckets: Dict[str, List[str]] = {c: [] for c in CAT_IDS}
    seen_in_bucket: Dict[str, Set[str]] = {c: set() for c in CAT_IDS}

    for text, cats in unique_rows:
        for cid in cats:
            if cid not in buckets:
                continue
            dk = _dedupe_key(text)
            if dk in seen_in_bucket[cid]:
                continue
            seen_in_bucket[cid].add(dk)
            buckets[cid].append(text)

    return buckets


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--no-infer", action="store_true")
    args = ap.parse_args()

    src: Path = args.source
    out: Path = args.out

    if not src.is_file():
        print(f"[build_fortune_lines] 소스 없음: {src}")
        print("  data/fortune_app_dataset_ko_2000_deduped.json 을 두고 다시 실행하세요.")
        # 빈 스켈레톤으로 프론트가 깨지지 않게
        payload = {
            "version": 1,
            "sourceFile": src.name,
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "counts": {c: 0 for c in CAT_IDS},
            "byCategory": {c: [] for c in CAT_IDS},
            "note": "source missing — run after adding data/fortune_app_dataset_ko_2000_deduped.json",
        }
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return

    with open(src, "r", encoding="utf-8") as f:
        data = json.load(f)

    entries = gather_entries(data)
    buckets = build_buckets(entries, infer=not args.no_infer)

    payload = {
        "version": 1,
        "sourceFile": src.name,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "counts": {c: len(buckets[c]) for c in CAT_IDS},
        "byCategory": buckets,
    }

    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"[build_fortune_lines] wrote {out}")
    for c in CAT_IDS:
        print(f"  {c}: {payload['counts'][c]}")


if __name__ == "__main__":
    main()
