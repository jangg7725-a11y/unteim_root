# unteim/engine/kasi_api_adapter.py
from __future__ import annotations

import os
from typing import Dict, Any, Optional

import requests
from dotenv import load_dotenv

# 프로젝트 루트의 .env 자동 로드
load_dotenv()


class KasiApiError(RuntimeError):
    pass


def _get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(name)
    if v is None:
        return default
    v = v.strip()
    return v if v else default


def call_kasi_lunar_api(*, year: int, month: int, day: int, timeout_sec: float = 7.0) -> Dict[str, Any]:
    """
    KASI 음양력(음력) 정보 조회 (양력 -> 음력)

    반환 예:
      {"year": 2024, "month": 11, "day": 2, "is_leap": False}

    주의:
    - ServiceKey는 여기서 quote(인코딩)하지 않습니다.
      requests가 params를 URL 인코딩하면서, 우리가 quote까지 하면 %25... 형태의 '이중 인코딩'이 발생할 수 있습니다.
    """

    service_key = _get_env("KASI_SERVICE_KEY")
    if not service_key:
        raise KasiApiError("KASI_SERVICE_KEY 환경변수가 설정되지 않았습니다. (.env 확인)")

    _default_base = "http://apis.data.go.kr/B090041/openapi/service"
    _default_path = "/LrsrCldInfoService/getLunCalInfo"
    base_url = _get_env("KASI_BASE_URL", _default_base) or _default_base
    path = _get_env("KASI_PATH", _default_path) or _default_path

    url = base_url.rstrip("/") + path

    # ✅ 여기서 quote 하지 말 것 (double encoding 방지)
    params = {
        "ServiceKey": service_key,
        "solYear": f"{year:04d}",
        "solMonth": f"{month:02d}",
        "solDay": f"{day:02d}",
        "_type": "json",  # 일부 환경에서 무시될 수 있어도 OK
    }

    try:
        res = requests.get(url, params=params, timeout=timeout_sec)
        # 401/403/500 등 에러면 raise
        res.raise_for_status()
    except Exception as e:
        # URL 전체는 너무 길어질 수 있어 일부만
        raise KasiApiError(f"KASI API 요청 실패: {e} (url={url})") from e

    # 1) JSON 우선 파싱 시도
    data: Any
    try:
        data = res.json()
    except Exception:
        data = None

    if isinstance(data, dict):
        # 예상 JSON 구조: response > body > items > item
        try:
            item = data["response"]["body"]["items"]["item"]
            if isinstance(item, list):
                item = item[0]

            lun_year = int(item["lunYear"])
            lun_month = int(item["lunMonth"])
            lun_day = int(item["lunDay"])
            # 윤달 표기는 API별로 달라 방어
            # 'lunLeapmonth' == '윤' / '1' / True 등 다양한 케이스가 있어 모두 처리
            leap_raw = item.get("lunLeapmonth")
            is_leap = str(leap_raw).strip() in ("윤", "1", "true", "True", "Y", "y")

            return {"year": lun_year, "month": lun_month, "day": lun_day, "is_leap": is_leap}
        except Exception as e:
            raise KasiApiError(f"KASI JSON 응답 파싱 실패: {e}, data={data}") from e

    # 2) JSON이 아니면(XML 등) → 최소한 에러 확인 가능한 형태로 출력
    #   (지금은 디버깅 우선: 실제 운영에서는 XML 파서 추가 가능)
    text = (res.text or "").strip()
    raise KasiApiError(
        "KASI 응답이 JSON이 아닙니다. "
        "포털/서비스 설정에 따라 XML로 오는 경우가 있습니다. "
        f"응답 일부: {text[:400]}"
    )
