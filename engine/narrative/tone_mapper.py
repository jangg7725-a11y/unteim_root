# unteim/engine/narrative/tone_mapper.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .sentence_templates import TONE_RULES, COUNSEL_ENDINGS


@dataclass
class ToneOptions:
    mode: str = "counsel"  # "raw" | "counsel"
    add_hint: bool = True   # 문장 끝 힌트(괄호) 추가 여부
    max_insert: int = 1     # 한 문장에 톤 보강 최대 삽입 수


def _contains_any(text: str, keywords: List[str]) -> bool:
    return any(k in text for k in keywords)


def _apply_endings(text: str) -> str:
    for a, b in COUNSEL_ENDINGS:
        if text.strip().endswith(a):
            return text.rstrip()[:-len(a)] + b
    return text


def convert_sentence(sentence: str, opt: Optional[ToneOptions] = None) -> str:
    """
    한 문장을 상담가 톤으로 변환.
    - 원문을 유지하면서, 키워드 기반으로 보강 문장을 덧붙이는 방식
    """
    opt = opt or ToneOptions()

    if opt.mode == "raw":
        return sentence

    s = sentence.strip()
    if not s:
        return s

    inserted = 0
    addons: List[str] = []

    for rule in TONE_RULES:
        if inserted >= opt.max_insert:
            break
        if _contains_any(s, rule.get("contains", [])):
            addons.append(rule.get("counsel", ""))
            inserted += 1

    if opt.add_hint:
        s = _apply_endings(s)

    # 이미 충분히 긴 문장에는 과삽입 방지
    if len(s) > 140:
        addons = addons[:1]

    if addons:
        return s + "\n" + "\n".join([a for a in addons if a])
    return s


def convert_text_block(text: str, opt: Optional[ToneOptions] = None) -> str:
    """
    여러 줄 텍스트 블록을 줄 단위로 변환.
    (대운/세운/월운 코멘터리 문자열에 바로 적용 가능)
    """
    opt = opt or ToneOptions()
    lines = text.splitlines()
    out_lines: List[str] = []
    for line in lines:
        # 목록/헤더는 그대로
        if line.strip().startswith(("✅", "❌", "📌", "—", "-", "*", "#")):
            out_lines.append(line)
            continue
        out_lines.append(convert_sentence(line, opt))
    return "\n".join(out_lines)
