# unteim/engine/commentary_input.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class CommentaryInput:
    elements: Dict[str, Any]
    yong_meta: Dict[str, Any]
    ten_gods: Dict[str, Any]
    luck_stack: Dict[str, Any]
    conflicts: Dict[str, Any]
    shinsal_tone: Dict[str, Any]


def from_final_mapping(final_mapping: Dict[str, Any] | None) -> CommentaryInput:
    fm = final_mapping or {}
    return CommentaryInput(
        elements=fm.get("elements", {}) or {},
        yong_meta=fm.get("yong_meta", {}) or {},
        ten_gods=fm.get("ten_gods", {}) or {},
        luck_stack=fm.get("luck_stack", {}) or {},
        conflicts=fm.get("conflicts", {}) or {},
        shinsal_tone=fm.get("shinsal_tone", {}) or fm.get("shinsal_tone", {}) or {},
    )
