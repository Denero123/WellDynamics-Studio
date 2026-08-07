"""
Annular hydraulics: Bingham-plastic rheology, flow-regime classification,
frictional pressure drop, and ECD calculated FROM that friction loss.

Design note (reads alongside src/engineering/hydraulics.py):
The existing `hydraulics.ecd_kg_m3()` intentionally requires the circulating
pressure loss as an input, because the PENG 258 PDF does not specify a
pressure-loss correlation. This module closes that gap by implementing a
standard oilfield Bingham-plastic annular friction model (Fanning friction
factor, Reynolds-number regime classification) so ECD can be calculated
from wellbore geometry and flow rate directly, without a user-supplied
pressure loss. Keep both: `hydraulics.ecd_kg_m3()` remains valid for anyone
who already has a measured/simulated pressure loss, while this module
supplies the calculation when only geometry and flow rate are known.
"""
import math

GRAVITY = 9.81
LAMINAR_RE_UPPER = 2100.0
TURBULENT_RE_LOWER = 2900.0


def annular_velocity_m_s(
    flow_rate_m3_s: float,
    hole_diameter_m: float,
    pipe_od_m: float,
) -> float:
    if flow_rate_m3_s <= 0:
        raise ValueError("Flow rate must be greater than zero.")
    if hole_diameter_m <= 0 or pipe_od_m <= 0:
        raise ValueError("Hole diameter and pipe OD must be greater than zero.")
    if pipe_od_m >= hole_diameter_m:
        raise ValueError("Pipe OD must be smaller than hole diameter.")

    annular_area_m2 = (math.pi / 4.0) * (hole_diameter_m**2 - pipe_od_m**2)
    return flow_rate_m3_s / annular_area_m2


def reynolds_number(
    density_kg_m3: float,
    velocity_m_s: float,
    hydraulic_diameter_m: float,
    plastic_viscosity_pa_s: float,
    yield_point_pa: float,
) -> float:
    if density_kg_m3 <= 0:
        raise ValueError("Density must be greater than zero.")
    if velocity_m_s <= 0:
        raise ValueError("Velocity must be greater than zero.")
    if hydraulic_diameter_m <= 0:
        raise ValueError("Hydraulic diameter must be greater than zero.")
    if plastic_viscosity_pa_s < 0 or yield_point_pa < 0:
        raise ValueError("PV and YP cannot be negative.")

    effective_viscosity_pa_s = plastic_viscosity_pa_s + (
        yield_point_pa * hydraulic_diameter_m
    ) / (6.0 * velocity_m_s)

    if effective_viscosity_pa_s <= 0:
        raise ValueError("Computed effective viscosity is non-physical (<= 0).")

    return (density_kg_m3 * velocity_m_s * hydraulic_diameter_m) / effective_viscosity_pa_s


def classify_flow_regime(reynolds_number_value: float) -> str:
    if reynolds_number_value <= 0:
        raise ValueError("Reynolds number must be greater than zero.")
    if reynolds_number_value < LAMINAR_RE_UPPER:
        return "laminar"
    if reynolds_number_value <= TURBULENT_RE_LOWER:
        return "transitional"
    return "turbulent"


def frictional_pressure_drop_pa(
    density_kg_m3: float,
    velocity_m_s: float,
    hydraulic_diameter_m: float,
    length_m: float,
    reynolds_number_value: float,
    flow_regime: str,
) -> float:
    if density_kg_m3 <= 0 or velocity_m_s <= 0:
        raise ValueError("Density and velocity must be greater than zero.")
    if hydraulic_diameter_m <= 0 or length_m <= 0:
        raise ValueError("Hydraulic diameter and length must be greater than zero.")
    if reynolds_number_value <= 0:
        raise ValueError("Reynolds number must be greater than zero.")
    if flow_regime not in ("laminar", "transitional", "turbulent"):
        raise ValueError(f"Unknown flow regime: {flow_regime!r}")

    if flow_regime == "laminar":
        fanning_friction_factor = 16.0 / reynolds_number_value
    elif flow_regime == "turbulent":
        fanning_friction_factor = 0.079 / reynolds_number_value**0.25
    else:  # transitional: linear blend between laminar and turbulent factors
        f_laminar = 16.0 / reynolds_number_value
        f_turbulent = 0.079 / reynolds_number_value**0.25
        blend = (reynolds_number_value - LAMINAR_RE_UPPER) / (
            TURBULENT_RE_LOWER - LAMINAR_RE_UPPER
        )
        fanning_friction_factor = f_laminar + blend * (f_turbulent - f_laminar)

    return (
        2.0 * fanning_friction_factor * density_kg_m3 * velocity_m_s**2 * length_m
    ) / hydraulic_diameter_m


def ecd_from_calculated_friction_kg_m3(
    static_density_kg_m3: float,
    friction_pressure_drop_pa: float,
    tvd_m: float,
) -> float:
    """
    ECD = static density + friction pressure drop / (g * TVD)

    Same relationship as hydraulics.ecd_kg_m3(), but named separately here
    to make clear the friction term is a calculated Bingham-plastic annular
    friction loss rather than a user-supplied value.
    """
    if static_density_kg_m3 <= 0:
        raise ValueError("Static density must be greater than zero.")
    if friction_pressure_drop_pa < 0:
        raise ValueError("Friction pressure drop cannot be negative.")
    if tvd_m <= 0:
        raise ValueError("TVD must be greater than zero.")

    return static_density_kg_m3 + friction_pressure_drop_pa / (GRAVITY * tvd_m)


def minimum_transport_velocity_m_s(yield_point_pa: float) -> float:
    """
    Conservative screening threshold for cuttings transport: higher YP fluids
    suspend cuttings at lower annular velocities. This is a simplified
    screening check, not a full slip-velocity (e.g. Moore) correlation --
    treat it as a stated modelling limitation in the technical report.
    """
    if yield_point_pa < 0:
        raise ValueError("Yield point cannot be negative.")

    baseline_m_s = 0.46
    yp_relief_m_s = min(yield_point_pa / 50.0, 0.20)
    return max(baseline_m_s - yp_relief_m_s, 0.15)


def analyze_annular_hydraulics(
    flow_rate_m3_s: float,
    hole_diameter_m: float,
    pipe_od_m: float,
    interval_length_m: float,
    tvd_m: float,
    static_density_kg_m3: float,
    plastic_viscosity_pa_s: float,
    yield_point_pa: float,
) -> dict[str, float | str | bool]:
    """
    Run the full velocity -> Reynolds -> regime -> friction -> ECD pipeline
    for one annular interval and check cuttings transport adequacy.

    Returns a dict (matching the style of cementing.fluid_sweep_volumes)
    rather than a bespoke class, so callers can unpack only what they need.
    """
    hydraulic_diameter_m = hole_diameter_m - pipe_od_m

    velocity = annular_velocity_m_s(flow_rate_m3_s, hole_diameter_m, pipe_od_m)
    reynolds = reynolds_number(
        static_density_kg_m3,
        velocity,
        hydraulic_diameter_m,
        plastic_viscosity_pa_s,
        yield_point_pa,
    )
    regime = classify_flow_regime(reynolds)
    friction_dp = frictional_pressure_drop_pa(
        static_density_kg_m3, velocity, hydraulic_diameter_m, interval_length_m, reynolds, regime
    )
    ecd = ecd_from_calculated_friction_kg_m3(static_density_kg_m3, friction_dp, tvd_m)

    min_velocity = minimum_transport_velocity_m_s(yield_point_pa)
    transport_ok = velocity >= min_velocity

    return {
        "annular_velocity_m_s": velocity,
        "reynolds_number": reynolds,
        "flow_regime": regime,
        "friction_pressure_drop_pa": friction_dp,
        "ecd_kg_m3": ecd,
        "cuttings_transport_ok": transport_ok,
        "cuttings_transport_margin_m_s": velocity - min_velocity,
    }
