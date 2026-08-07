import math

import pytest

from src.engineering.mud_weight_window import (
    validate_profile,
    interpolate_gradients_pa_m,
    evaluate_mud_weight_at_depth,
    evaluate_profile,
)

# Profile: (depth_m, pore_pressure_grad_pa_m, fracture_grad_pa_m)
SIMPLE_PROFILE = [
    (0.0, 9810.0, 14715.0),      # 1.0 SG / 1.5 SG equivalent
    (1500.0, 11281.5, 16677.0),  # 1.15 SG / 1.70 SG equivalent
    (3000.0, 12753.0, 18639.0),  # 1.30 SG / 1.90 SG equivalent
]


def test_validate_profile_requires_two_points():
    with pytest.raises(ValueError):
        validate_profile([(0.0, 9810.0, 14715.0)])


def test_validate_profile_rejects_unsorted_depths():
    with pytest.raises(ValueError):
        validate_profile([(1500.0, 11281.5, 16677.0), (0.0, 9810.0, 14715.0)])


def test_validate_profile_rejects_duplicate_depths():
    with pytest.raises(ValueError):
        validate_profile([(0.0, 9810.0, 14715.0), (0.0, 9900.0, 14800.0)])


def test_validate_profile_rejects_pore_pressure_above_fracture():
    with pytest.raises(ValueError):
        validate_profile([(0.0, 15000.0, 14715.0), (1000.0, 11281.5, 16677.0)])


def test_interpolate_at_control_point_is_exact():
    pore, frac = interpolate_gradients_pa_m(SIMPLE_PROFILE, 1500.0)
    assert math.isclose(pore, 11281.5, rel_tol=1e-9)
    assert math.isclose(frac, 16677.0, rel_tol=1e-9)


def test_interpolate_midpoint():
    pore, frac = interpolate_gradients_pa_m(SIMPLE_PROFILE, 750.0)
    expected_pore = (9810.0 + 11281.5) / 2
    expected_frac = (14715.0 + 16677.0) / 2
    assert math.isclose(pore, expected_pore, rel_tol=1e-9)
    assert math.isclose(frac, expected_frac, rel_tol=1e-9)


def test_interpolate_outside_range_raises():
    with pytest.raises(ValueError):
        interpolate_gradients_pa_m(SIMPLE_PROFILE, 5000.0)


def test_mud_weight_below_pore_pressure_is_critical():
    # Pore pressure density at 1500m = 11281.5 / 9.81 = 1150 kg/m3
    alert = evaluate_mud_weight_at_depth(1000.0, 1500.0, SIMPLE_PROFILE)
    assert alert["severity"] == "critical"
    assert "kick" in alert["message"].lower()


def test_mud_weight_above_fracture_gradient_is_critical():
    # Fracture density at 1500m = 16677.0 / 9.81 = 1700 kg/m3
    alert = evaluate_mud_weight_at_depth(1900.0, 1500.0, SIMPLE_PROFILE)
    assert alert["severity"] == "critical"
    assert "lost circulation" in alert["message"].lower()


def test_mud_weight_safely_within_window_is_ok():
    # Window at 1500m is 1150-1700 kg/m3; pick a comfortably central value
    alert = evaluate_mud_weight_at_depth(1400.0, 1500.0, SIMPLE_PROFILE)
    assert alert["severity"] == "ok"


def test_mud_weight_near_pore_pressure_boundary_warns():
    # 1150 kg/m3 is the pore-pressure boundary at 1500m; default trip margin is 30 kg/m3
    alert = evaluate_mud_weight_at_depth(1160.0, 1500.0, SIMPLE_PROFILE)
    assert alert["severity"] == "warning"


def test_nonpositive_density_rejected():
    with pytest.raises(ValueError):
        evaluate_mud_weight_at_depth(0.0, 1500.0, SIMPLE_PROFILE)


def test_evaluate_profile_marks_overall_critical_if_any_depth_fails():
    # 1050 kg/m3 is below pore pressure at 3000m (1300 kg/m3) though fine shallower
    report = evaluate_profile(1050.0, SIMPLE_PROFILE, check_depths_m=[0.0, 1500.0, 3000.0])
    assert report["overall_severity"] == "critical"
    assert report["is_safe"] is False


def test_evaluate_profile_all_safe():
    report = evaluate_profile(1400.0, SIMPLE_PROFILE, check_depths_m=[1500.0])
    assert report["overall_severity"] == "ok"
    assert report["is_safe"] is True


def test_evaluate_profile_defaults_to_profile_depths():
    report = evaluate_profile(1400.0, SIMPLE_PROFILE)
    assert len(report["alerts"]) == 3


def test_evaluate_profile_rejects_empty_check_depths():
    with pytest.raises(ValueError):
        evaluate_profile(1400.0, SIMPLE_PROFILE, check_depths_m=[])
