import math

import pytest

from src.engineering.rheology import (
    annular_velocity_m_s,
    reynolds_number,
    classify_flow_regime,
    frictional_pressure_drop_pa,
    ecd_from_calculated_friction_kg_m3,
    minimum_transport_velocity_m_s,
    analyze_annular_hydraulics,
)


def test_annular_velocity_matches_hand_calc():
    flow_rate = 0.025  # m3/s
    hole_d = 0.216
    pipe_od = 0.127
    expected_area = (math.pi / 4.0) * (hole_d**2 - pipe_od**2)
    assert math.isclose(
        annular_velocity_m_s(flow_rate, hole_d, pipe_od),
        flow_rate / expected_area,
        rel_tol=1e-9,
    )


def test_annular_velocity_rejects_pipe_larger_than_hole():
    with pytest.raises(ValueError):
        annular_velocity_m_s(0.02, 0.1, 0.2)


def test_annular_velocity_rejects_nonpositive_flow_rate():
    with pytest.raises(ValueError):
        annular_velocity_m_s(0.0, 0.216, 0.127)


def test_reynolds_number_positive_for_typical_inputs():
    re = reynolds_number(
        density_kg_m3=1200,
        velocity_m_s=1.5,
        hydraulic_diameter_m=0.089,
        plastic_viscosity_pa_s=0.025,
        yield_point_pa=12.0,
    )
    assert re > 0


def test_reynolds_number_rejects_negative_pv():
    with pytest.raises(ValueError):
        reynolds_number(1200, 1.5, 0.089, -0.01, 12.0)


def test_classify_flow_regime_thresholds():
    assert classify_flow_regime(500) == "laminar"
    assert classify_flow_regime(2099) == "laminar"
    assert classify_flow_regime(2100) == "transitional"
    assert classify_flow_regime(2900) == "transitional"
    assert classify_flow_regime(2901) == "turbulent"
    assert classify_flow_regime(10000) == "turbulent"


def test_classify_flow_regime_rejects_nonpositive():
    with pytest.raises(ValueError):
        classify_flow_regime(0)


def test_frictional_pressure_drop_increases_with_length():
    short_dp = frictional_pressure_drop_pa(1200, 1.5, 0.089, 500, 1500, "laminar")
    long_dp = frictional_pressure_drop_pa(1200, 1.5, 0.089, 1000, 1500, "laminar")
    assert long_dp > short_dp
    assert math.isclose(long_dp, short_dp * 2.0, rel_tol=1e-9)


def test_frictional_pressure_drop_rejects_unknown_regime():
    with pytest.raises(ValueError):
        frictional_pressure_drop_pa(1200, 1.5, 0.089, 500, 1500, "supersonic")


def test_ecd_from_calculated_friction_matches_hand_calc():
    expected = 1200 + 500_000 / (9.81 * 2000)
    assert math.isclose(
        ecd_from_calculated_friction_kg_m3(1200, 500_000, 2000),
        expected,
        rel_tol=1e-9,
    )


def test_ecd_from_calculated_friction_rejects_zero_tvd():
    with pytest.raises(ValueError):
        ecd_from_calculated_friction_kg_m3(1200, 500_000, 0)


def test_minimum_transport_velocity_decreases_with_yield_point():
    low_yp = minimum_transport_velocity_m_s(5.0)
    high_yp = minimum_transport_velocity_m_s(40.0)
    assert high_yp < low_yp


def test_minimum_transport_velocity_has_floor():
    assert minimum_transport_velocity_m_s(1000.0) >= 0.15


def test_analyze_annular_hydraulics_end_to_end():
    result = analyze_annular_hydraulics(
        flow_rate_m3_s=0.025,
        hole_diameter_m=0.216,
        pipe_od_m=0.127,
        interval_length_m=1200,
        tvd_m=1200,
        static_density_kg_m3=1200,
        plastic_viscosity_pa_s=0.025,
        yield_point_pa=12.0,
    )
    assert result["annular_velocity_m_s"] > 0
    assert result["reynolds_number"] > 0
    assert result["flow_regime"] in ("laminar", "transitional", "turbulent")
    assert result["friction_pressure_drop_pa"] > 0
    assert result["ecd_kg_m3"] > 1200  # ECD must exceed static density
    assert isinstance(result["cuttings_transport_ok"], bool)


def test_analyze_annular_hydraulics_propagates_geometry_errors():
    with pytest.raises(ValueError):
        analyze_annular_hydraulics(
            flow_rate_m3_s=0.025,
            hole_diameter_m=0.1,
            pipe_od_m=0.2,  # invalid: pipe OD > hole diameter
            interval_length_m=1200,
            tvd_m=1200,
            static_density_kg_m3=1200,
            plastic_viscosity_pa_s=0.025,
            yield_point_pa=12.0,
        )
