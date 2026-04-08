# -*- coding: utf-8 -*-
"""
shinsal_explainer.py
- detect_shinsal() 결과 + 고객 프로필 → 조건부 템플릿 매칭
"""

from __future__ import annotations
from typing import Dict, List, Any
from pathlib import Path
import json

# ------------------------------------------------
# 데이터 경로
# ------------------------------------------------
DATA_PATH = Path(__file__).resolve().parent / "data" / "shinsal_explanations.json"


# ------------------------------------------------
# JSON 로더
# ------------------------------------------------
def load_rules() -> Dict[str, Any]:
    with DATA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


# ------------------------------------------------
# 유틸: 위치 한글 라벨
# ------------------------------------------------
def where_kor_label(where: str) -> str:
    return {
        "year": "년지",
        "month": "월지",
        "day": "일지",
        "hour": "시지"
    }.get(where, where)


# ------------------------------------------------
# 유틸: 나이 → 연령대 분류
# ------------------------------------------------
def build_profile(
    name: str,
    age: int,
    sex: str,
    job_group: str,
    *,
    marital_status: str = "single",
) -> Dict[str, Any]:
    """
    CLI/리포트용 최소 프로필 dict — explain_shinsal_items() 입력 형식.
    """
    s = str(sex).strip().lower()
    gender = "F" if s in ("f", "여", "여성", "woman", "female") else "M"
    return {
        "name": name,
        "age": age,
        "gender": gender,
        "marital_status": marital_status,
        "job_group": job_group,
    }


def age_to_band(age: int) -> str:
    """
    20~35 → youth (청년)
    36~55 → mid   (장년)
    56+   → senior(중장년/노년)
    """
    if age < 36:
        return "youth"
    elif age < 56:
        return "mid"
    return "senior"


# ------------------------------------------------
# 룰 매칭
# ------------------------------------------------
def match_condition(rule_match: Dict[str, Any], ctx: Dict[str, Any]) -> bool:
    """
    rule_match 예: {"shinsal":"도화", "marital_status":["single","divorced"]}
    ctx 예: {"shinsal":"도화","marital_status":"single","gender":"F",...}
    """
    for key, expect in rule_match.items():
        actual = ctx.get(key)
        if isinstance(expect, list):
            if actual not in expect:
                return False
        else:
            if actual != expect:
                return False
    return True


def choose_rule(rules: List[Dict[str, Any]], ctx: Dict[str, Any]) -> Dict[str, Any] | None:
    """
    여러 룰 중 가장 구체적인(조건 수 많은) 룰 선택
    """
    candidates = []
    for r in rules:
        rm = r.get("match", {})
        if match_condition(rm, ctx):
            candidates.append((len(rm.keys()), r))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


# ------------------------------------------------
# 메인: 신살 해설 변환
# ------------------------------------------------
def explain_shinsal_items(
    items: List[Dict[str, Any]],
    profile: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    items: detect_shinsal() 결과 리스트
      예) [{"name":"도화","where":"month","branch":"酉","detail":"..."}]

    profile: {
      "marital_status": "single|married|divorced|widowed",
      "gender": "F|M",
      "age": 43,
      "job_group": "service|public|creator|sales|student|..."
    }
    """
    data = load_rules()
    rules = data["rules"]

    # age_band 자동 주입
    age_val = profile.get("age")
    if age_val is not None:
        profile["age_band"] = age_to_band(int(age_val))

    out: List[Dict[str, Any]] = []
    for it in items:
        ctx = {
            "shinsal": it["name"],
            "where": it["where"],
            "where_label": where_kor_label(it["where"]),
            "branch": it.get("branch", "")
        }
        ctx.update(profile)  # 결혼유무/성별/직업/연령대 병합

        rule = choose_rule(rules, ctx)

        if rule is None:
            # 기본형(백업 문장)
            out.append({
                "title": f"{it['name']} ({where_kor_label(it['where'])})",
                "bullets": [
                    f"위치: {where_kor_label(it['where'])} {it.get('branch','')}",
                    "상황에 따라 긍·부정 해석이 달라집니다."
                ],
                "advice": "현재 관계/직업/나이에 맞춰 균형 있게 판단하세요."
            })
            continue

        # 템플릿 렌더 (간단치환)
        advice = rule.get("advice", "").format(**ctx)

        out.append({
            "title": f"{rule['title']} · {where_kor_label(it['where'])}",
            "tone": rule.get("tone", "neutral"),
            "bullets": rule.get("bullets", []),
            "advice": advice,
            "flags": rule.get("flags", {}),
            "raw": it  # 원자료 포함(디버그/리포트)
        })
    return out


# ------------------------------------------------
# 단독 실행 테스트
# ------------------------------------------------
if __name__ == "__main__":
    sample_items = [
        {"name": "도화", "where": "month", "branch": "酉", "detail": "일지[申] 기준 도화"}
    ]
    sample_profile = {"marital_status": "single", "gender": "F", "age": 27, "job_group": "service"}
    result = explain_shinsal_items(sample_items, sample_profile)
    for r in result:
        print(r["title"])
        print(" - " + "\n - ".join(r["bullets"]))
        print(" ✦ " + r["advice"])
