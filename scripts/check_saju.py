import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from engine.sajuCalculator import calculate_saju

for birth in ["1990-01-01 09:30", "1990-05-15 14:30"]:
    p = calculate_saju(birth).as_dict()
    print("입력:", birth)
    print("년주:", p["year"]["gan"] + p["year"]["ji"])
    print("월주:", p["month"]["gan"] + p["month"]["ji"])
    print("일주:", p["day"]["gan"] + p["day"]["ji"])
    print("시주:", p["hour"]["gan"] + p["hour"]["ji"])
    print("-" * 30)