import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from backend.desolidify_engine.settings import _clamp
from backend.api.schemas import coerce_and_clamp_params


def test_clamp():
    # lo/hi style
    assert _clamp(5, lo=1, hi=10) == 5
    assert _clamp(0, lo=1, hi=10) == 1
    assert _clamp(15, lo=1, hi=10) == 10

    # min/max style
    assert _clamp(5, min=1, max=10) == 5
    assert _clamp(0, min=1, max=10) == 1
    assert _clamp(15, min=1, max=10) == 10


def test_coerce_and_clamp_params():
    params = {"spacing": 0}
    out = coerce_and_clamp_params(params)
    assert out["spacing"] >= 8.0
