# unteim/engine/ten_gods_counter_v1.py
# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Dict, Any

TEN_GODS = ["비견","겁재","식신","상관","편재","정재","편관","정관","편인","정인"]

def count_ten_gods_from_sipsin(sipsin: Dict[str, Any]) -> Dict[str, float]:
    """
    다양한 sipsin 결과 구조를 받아서 10십신 카운트를 최대한 복구한다.
    우선순위:
    1) sipsin['counts']
    2) sipsin['profiles']['stems'/'branches'] 값이 십신명인 경우
    3) sipsin 내부에서 TEN_GODS 문자열이 등장하는 모든 값을 스캔(최후 수단)
    """
    out = {k: 0.0 for k in TEN_GODS}
    if not isinstance(sipsin, dict):
        return out

    # 1) counts가 있으면 그대로
    c = sipsin.get("counts")
    if isinstance(c, dict) and c:
        for k, v in c.items():
            if k in out:
                try:
                    out[k] += float(v or 0)
                except Exception:
                    pass
        return out

    # 2) profiles의 stems/branches가 십신명인 경우
    prof = sipsin.get("profiles")
    if isinstance(prof, dict):
        for key in ("stems", "branches"):
            m = prof.get(key)
            if isinstance(m, dict):
                for _, v in m.items():
                    if isinstance(v, str) and v in out:
                        out[v] += 1.0

    # 3) 최후 수단: dict를 훑으며 십신 문자열 카운트
    def _walk(x):
        if isinstance(x, dict):
            for vv in x.values():
                _walk(vv)
        elif isinstance(x, list):
            for vv in x:
                _walk(vv)
        elif isinstance(x, str):
            if x in out:
                out[x] += 1.0

    _walk(sipsin)

    return out
