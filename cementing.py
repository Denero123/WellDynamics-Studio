import math


def annular_volume_m3(
    hole_diameter_m: float,
    casing_od_m: float,
    length_m: float,
) -> float:
    if hole_diameter_m <= 0 or casing_od_m <= 0 or length_m <= 0:
        raise ValueError("Diameters and length must be greater than zero.")
    if hole_diameter_m <= casing_od_m:
        raise ValueError("Hole diameter must be greater than casing OD.")

    return (math.pi / 4.0) * (
        hole_diameter_m**2 - casing_od_m**2
    ) * length_m


def cement_volume_with_excess_m3(
    base_annular_volume_m3: float,
    excess_fraction: float,
) -> float:
    if base_annular_volume_m3 < 0:
        raise ValueError("Base annular volume cannot be negative.")
    if excess_fraction < 0:
        raise ValueError("Excess fraction cannot be negative.")

    return base_annular_volume_m3 * (1.0 + excess_fraction)


def fluid_sweep_volumes(
    annular_volume_m3_value: float,
    spacer_fraction: float,
    flush_fraction: float,
    displacement_fraction: float,
) -> dict[str, float]:
    values = {
        "spacer_volume": spacer_fraction,
        "flush_volume": flush_fraction,
        "displacement_volume": displacement_fraction,
    }

    if annular_volume_m3_value <= 0:
        raise ValueError("Annular volume must be greater than zero.")
    if any(value < 0 for value in values.values()):
        raise ValueError("Sweep fractions cannot be negative.")

    return {
        name: annular_volume_m3_value * fraction
        for name, fraction in values.items()
    }
