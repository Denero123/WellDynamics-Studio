GRAVITY = 9.81


def ecd_kg_m3(
    static_density_kg_m3: float,
    circulating_pressure_loss_pa: float,
    tvd_m: float,
) -> float:
    """
    ECD = static mud density + circulating pressure loss / (g * TVD)

    This function intentionally requires pressure loss as an input because
    the supplied PENG 258 PDF does not define a specific pressure-loss
    correlation for the hydraulics engine.
    """
    if static_density_kg_m3 <= 0:
        raise ValueError("Static density must be greater than zero.")
    if circulating_pressure_loss_pa < 0:
        raise ValueError("Circulating pressure loss cannot be negative.")
    if tvd_m <= 0:
        raise ValueError("TVD must be greater than zero.")

    return static_density_kg_m3 + circulating_pressure_loss_pa / (GRAVITY * tvd_m)
