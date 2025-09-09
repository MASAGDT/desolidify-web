import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from backend.desolidify_engine.settings import _clamp


def test_clamp():
    assert _clamp(5, lo=1, hi=10) == 5
    assert _clamp(5, min=1, max=10) == 5
    assert _clamp(0, min=1, max=10) == 1
    assert _clamp(15, lo=1, hi=10) == 10
