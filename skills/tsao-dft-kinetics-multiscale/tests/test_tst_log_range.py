"""Extreme values test numerical identities, not physically meaningful temperatures."""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "tst_math.py"
SPEC = importlib.util.spec_from_file_location("tsao_tst_math_log_range", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
TST_MATH = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = TST_MATH
SPEC.loader.exec_module(TST_MATH)

H_J_S = TST_MATH.H_J_S
KB_J_PER_K = TST_MATH.KB_J_PER_K
log_tst_rate = TST_MATH.log_tst_rate
tst_rate = TST_MATH.tst_rate
tst_rate_interval = TST_MATH.tst_rate_interval


@pytest.mark.parametrize("temperature", [1e-310, 1e-300, 1e300, 1e308])
def test_log_prefactor_is_computed_without_materializing_extreme_products(temperature: float) -> None:
    expected = math.log(KB_J_PER_K) + math.log(temperature) - math.log(H_J_S)
    assert log_tst_rate(0.0, temperature) == pytest.approx(expected, abs=1e-12)


def test_transmission_and_temperature_can_cancel_extreme_prefactors() -> None:
    assert tst_rate(0.0, 1e300, kappa=1e-300) == pytest.approx(KB_J_PER_K / H_J_S, rel=1e-12)


def test_zero_barrier_and_zero_uncertainty_do_not_divide_by_underflowed_rt() -> None:
    temperature = float.fromhex("0x0.0000000000001p-1022")
    interval = tst_rate_interval(0.0, 0.0, temperature)
    assert math.isfinite(interval["central_ln_rate"])
    assert interval["lower_ln_rate"] == interval["central_ln_rate"] == interval["upper_ln_rate"]


@pytest.mark.parametrize("argument", ["barrier", "temperature", "transmission", "degeneracy"])
def test_unrepresentable_integer_inputs_raise_validation_errors(argument: str) -> None:
    values = dict(barrier=0, temperature=300, transmission=1, degeneracy=1)
    values[argument] = 10**400
    with pytest.raises(ValueError, match="finite numeric"):
        log_tst_rate(values["barrier"], values["temperature"], values["transmission"], values["degeneracy"])
