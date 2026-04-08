# unteim/tests/test_env.py
import os, sys
from dotenv import load_dotenv  # ← 이 줄이 꼭 필요!

# 1) 경로 보정: tests/ 상위(un teim)를 import 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 2) .env 로드 (unteim/.env)
ENV_PATH = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(ENV_PATH)

# 3) 대상 임포트
from engine.kasi_client import fetch_solarterm, fetch_kasi_data

def test_env_and_clients():
    a = fetch_solarterm("1966-11-04")
    assert a.term_name and a.term_datetime

    b = fetch_kasi_data(1966)
    assert isinstance(b, list) and len(b) >= 1
    assert "name" in b[0] and "dt" in b[0]

if __name__ == "__main__":
    print("첫 번째 호출 (로컬 절기):", fetch_solarterm("1966-11-04"))
    print("두 번째 호출 (연간 절기 리스트):", fetch_kasi_data(1966)[:2], "...")
