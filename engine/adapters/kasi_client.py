from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path
from typing import Optional, Dict, Any

import requests


@dataclass(frozen=True)
class KasiConfig:
    api_key: str
    timeout_sec: int = 8
    cache_dir: str = "unteim/engine/cache"


class KasiError(RuntimeError):
    pass


def _cache_path(cfg: KasiConfig, y: int) -> Path:
    p = Path(cfg.cache_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p / f"kasi_solar_terms_{y}.json"


def _read_cache(cfg: KasiConfig, y: int) -> Optional[Dict[str, Any]]:
    p = _cache_path(cfg, y)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_cache(cfg: KasiConfig, y: int, data: Dict[str, Any]) -> None:
    p = _cache_path(cfg, y)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _safe_get_env_key() -> str:
    k = os.getenv("KASI_API_KEY", "").strip()
    if not k:
        raise KasiError("KASI_API_KEY is missing. Set environment variable KASI_API_KEY.")
    return k


def fetch_solar_terms_year(
    year: int,
    cfg: Optional[KasiConfig] = None,
) -> Dict[str, Any]:
    """
    Returns: dict with solar term list for a year (KST timestamps).
    캐시 우선 → 없으면 API 호출 → 저장
    """
    if cfg is None:
        cfg = KasiConfig(api_key=_safe_get_env_key())

    cached = _read_cache(cfg, year)
    if cached is not None:
        return cached

    # ✅ 여기는 오슈님이 이미 키를 가지고 있고,
    # KASI 문서에 맞는 endpoint/params로 "연도 절기 시각"을 받아오도록 구성해야 함.
    # (현재는 틀만 제공: 이미 오슈님이 6번방에서 작업한 URL/파라미터가 있으면 그대로 꽂으면 됩니다.)
    #
    # 예시 형태(가짜): url = "https://apis.data.go.kr/B090041/openapi/service/SpcdeInfoService/get24DivisionsInfo"
    # params = {...}
    #
    # 오슈님 기존 코드에 있는 URL/params를 그대로 가져와서 여기만 표준화하면 끝입니다.

    url = os.getenv("KASI_SOLARTERM_URL", "").strip()
    if not url:
        raise KasiError("KASI_SOLARTERM_URL is missing. Set env var or hardcode the endpoint.")

    params = {
        "serviceKey": cfg.api_key,
        "solYear": str(year),
        # 기타 파라미터는 오슈님 기존 코드 기준으로 추가
    }

    try:
        r = requests.get(url, params=params, timeout=cfg.timeout_sec)
        r.raise_for_status()
    except Exception as e:
        raise KasiError(f"KASI request failed: {type(e).__name__}: {e}")

    # ✅ 응답 파싱: XML/JSON 무엇이든, 최종 반환은 "절기명 -> KST datetime"으로 표준화하세요.
    # 아래는 “표준 반환 형태” 예시:
    data = {
        "year": year,
        "timezone": "Asia/Seoul",
        # "terms": [{"name":"입춘","dt":"2026-02-04Txx:xx:xx+09:00"}, ...]
        "terms": [],
        "raw": r.text,  # 디버그용(원하면 빼도 됨)
    }

    _write_cache(cfg, year, data)
    return data
