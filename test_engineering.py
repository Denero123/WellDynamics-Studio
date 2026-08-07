import math

from src.engineering.mud import (
    hydrostatic_pressure_pa,
    required_mud_density_kg_m3,
    bingham_shear_stress_pa,
)
from src.engineering.cementing import annular_volume_m3
from src.engineering.hydraulics import ecd_kg_m3


def test_hydrostatic_pressure():
    assert math.isclose(
        hydrostatic_pressure_pa(1000, 100),
        981000,
        rel_tol=1e-9,
    )


def test_required_density():
    assert math.isclose(
        required_mud_density_kg_m3(981000, 100),
        1000,
        rel_tol=1e-9,
    )


def test_bingham_model():
    assert math.isclose(
        bingham_shear_stress_pa(10, 0.03, 100),
        13,
        rel_tol=1e-9,
    )


def test_annular_volume():
    expected = math.pi / 4 * (0.216**2 - 0.14**2) * 1000
    assert math.isclose(
        annular_volume_m3(0.216, 0.14, 1000),
        expected,
        rel_tol=1e-9,
    )


def test_ecd():
    expected = 1200 + 2_000_000 / (9.81 * 2500)
    assert math.isclose(
        ecd_kg_m3(1200, 2_000_000, 2500),
        expected,
        rel_tol=1e-9,
    )
