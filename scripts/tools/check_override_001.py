# unteim/tools/check_override_001.py
# -*- coding: utf-8 -*-

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import inspect
from engine.full_analyzer import analyze_full

def main():
    s = inspect.getsource(analyze_full)
    print("HAS_OVERRIDE =", ("tf[\"samjae\"]" in s) or ("tf['samjae']" in s))

if __name__ == "__main__":
    main()