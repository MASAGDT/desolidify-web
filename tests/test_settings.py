import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from backend.desolidify_engine.settings import _clamp
from backend.api.schemas import coerce_and_clamp_params


def test_clamp():
    assert _clamp(5, min=1, max=10) == 5
    assert _clamp(0, min=1, max=10) == 1
    assert _clamp(15, min=1, max=10) == 10
    # ignore unknown keys (mirrors PARAM_SPECS structure)
    assert _clamp(5, min=1, max=10, tip="extra") == 5


def test_coerce_and_clamp_params():
    params = {"spacing": 0}
    out = coerce_and_clamp_params(params)
    # spacing must be clamped to the minimum defined in PARAM_SPECS
    assert out["spacing"] >= 8.0
