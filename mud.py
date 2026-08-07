import math

GRAVITY = 9.81
KG_M3_TO_PPG = 0.008345404452


def hydrostatic_pressure_pa(density_kg_m3: float, tvd_m: float) -> float:
    if density_kg_m3 <= 0 or tvd_m <= 0:
        raise ValueError("Density and TVD must be greater than zero.")
    return density_kg_m3 * GRAVITY * tvd_m


def required_mud_density_kg_m3(formation_pressure_pa: float, tvd_m: float) -> float:
    if formation_pressure_pa < 0 or tvd_m <= 0:
        raise ValueError("Formation pressure must be non-negative and TVD must be positive.")
    return formation_pressure_pa / (GRAVITY * tvd_m)


def mud_weight_ppg(density_kg_m3: float) -> float:
    if density_kg_m3 <= 0:
        raise ValueError("Density must be greater than zero.")
    return density_kg_m3 * KG_M3_TO_PPG


def safe_mud_window(
    pore_pressure_gradient_pa_m: float,
    fracture_gradient_pa_m: float,
    tvd_m: float,
) -> tuple[float, float]:
    if pore_pressure_gradient_pa_m < 0 or fracture_gradient_pa_m < 0:
        raise ValueError("Pressure gradients cannot be negative.")
    if tvd_m <= 0:
        raise ValueError("TVD must be greater than zero.")
    if fracture_gradient_pa_m < pore_pressure_gradient_pa_m:
        raise ValueError("Fracture gradient must be greater than or equal to pore pressure gradient.")

    low = pore_pressure_gradient_pa_m / GRAVITY
    high = fracture_gradient_pa_m / GRAVITY
    return low, high


def bingham_shear_stress_pa(
    yield_point_pa: float,
    plastic_viscosity_pa_s: float,
    shear_rate_s_inv: float,
) -> float:
    if yield_point_pa < 0 or plastic_viscosity_pa_s < 0 or shear_rate_s_inv < 0:
        raise ValueError("YP, PV and shear rate cannot be negative.")
    return yield_point_pa + plastic_viscosity_pa_s * shear_rate_s_inv
