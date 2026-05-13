# tests/test_risk_fortune_interpreter.py
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.risk_fortune_interpreter import get_risk_slots, get_shinsal_risk_slots, has_risk_type


def test_ibyeolsu_slots():
    s = get_risk_slots("ibyeolsu", seed=42)
    assert s.get("found")
    assert s.get("risk_type") == "ibyeolsu"
    assert "이별수" in (s.get("label_ko") or "")


def test_accident_su_from_month_branch_shinsal():
    slots = get_shinsal_risk_slots("월살", seed=7)
    assert any(x.get("risk_type") == "accident_su" for x in slots)


def test_ibyeolsu_from_dohwa():
    slots = get_shinsal_risk_slots("도화", seed=11)
    rts = {x.get("risk_type") for x in slots}
    assert "ibyeolsu" in rts
    assert "guseolsu" in rts


def test_has_risk_type_ibyeolsu():
    assert has_risk_type("ibyeolsu")
