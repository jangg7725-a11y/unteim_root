"""kasi_client.fetch_solarterm — 로컬 SolarTermsLoader 기반 (HTTP/SESSION 없음)."""

from engine.kasi_client import SolarTermProbe, fetch_solarterm


def test_fetch_solarterm_returns_probe_for_valid_date() -> None:
    r = fetch_solarterm("1966-11-04")
    assert isinstance(r, SolarTermProbe)
    assert r.term_name
    assert r.term_datetime


def test_fetch_solarterm_empty_on_invalid_date_string() -> None:
    r = fetch_solarterm("not-a-date")
    assert isinstance(r, SolarTermProbe)
    assert r.term_name == ""
    assert r.term_datetime == ""
