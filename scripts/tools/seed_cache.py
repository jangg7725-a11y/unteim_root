# unteim/tools/seed_cache.py
import os, json

# cache 파일 경로: unteim/engine/data/cache_kasi.json
HERE = os.path.dirname(__file__)
cache_path = os.path.abspath(os.path.join(HERE, "..", "engine", "data", "cache_kasi.json"))
os.makedirs(os.path.dirname(cache_path), exist_ok=True)

# 대표 절기 3건 시드
seed = {
    "1966-11-04": {"term_name": "입동", "term_datetime": "1966-11-07T05:31:00+09:00", "is_leap_month": False},
    "1966-12-22": {"term_name": "동지", "term_datetime": "1966-12-22T00:16:00+09:00", "is_leap_month": False},
    "1967-01-05": {"term_name": "소한", "term_datetime": "1967-01-05T00:00:00+09:00", "is_leap_month": False},
}

# 기존 캐시와 병합
try:
    with open(cache_path, "r", encoding="utf-8") as f:
        old = json.load(f)
except Exception:
    old = {}

old.update(seed)

with open(cache_path, "w", encoding="utf-8") as f:
    json.dump(old, f, ensure_ascii=False, indent=2)

print("[ok] cache seeded:", cache_path)
