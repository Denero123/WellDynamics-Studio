"""
Depth-indexed safe mud-weight window evaluation (PENG 258 Milestone 1:
"a functional backend that alerts users if a designed mud weight falls
outside the safe operational window").

`src/engineering/mud.safe_mud_window()` already computes the window at a
single TVD from single pore-pressure/fracture-gradient values. This module
extends that to a full depth-indexed pore-pressure/fracture-gradient
profile (as would be parsed from an uploaded formation-pressure file),
interpolating gradients at arbitrary depths and grading how close a
proposed mud weight sits to either boundary, not just whether it's inside
or outside.
"""
GRAVITY = 9.81


def validate_profile(profile: list[tuple[float, float, float]]) -> None:
    """
    profile: list of (depth_m, pore_pressure_gradient_pa_m, fracture_gradient_pa_m),
    sorted by increasing depth.
    """
    if len(profile) < 2:
        raise ValueError("Profile requires at least two depth points to interpolate.")

    depths = [point[0] for point in profile]
    if depths != sorted(depths):
        raise ValueError("Profile points must be sorted by increasing depth.")
    if len(set(depths)) != len(depths):
        raise ValueError("Profile contains duplicate depth entries.")

    for depth_m, pore_grad, frac_grad in profile:
        if depth_m < 0:
            raise ValueError("Depth cannot be negative.")
        if pore_grad <= 0 or frac_grad <= 0:
            raise ValueError("Pressure gradients must be greater than zero.")
        if pore_grad >= frac_grad:
            raise ValueError(
                f"At depth {depth_m}m, pore pressure gradient must be less than "
                f"fracture gradient."
            )


def interpolate_gradients_pa_m(
    profile: list[tuple[float, float, float]],
    depth_m: float,
) -> tuple[float, float]:
    """Linearly interpolate (pore_pressure_grad, fracture_grad) at depth_m, in Pa/m."""
    validate_profile(profile)

    first_depth, last_depth = profile[0][0], profile[-1][0]
    if depth_m < first_depth or depth_m > last_depth:
        raise ValueError(
            f"Depth {depth_m}m is outside the profile range ({first_depth}m-{last_depth}m)."
        )

    for (d0, pp0, fg0), (d1, pp1, fg1) in zip(profile, profile[1:]):
        if d0 <= depth_m <= d1:
            if d1 == d0:
                return pp0, fg0
            fraction = (depth_m - d0) / (d1 - d0)
            pore_grad = pp0 + fraction * (pp1 - pp0)
            frac_grad = fg0 + fraction * (fg1 - fg0)
            return pore_grad, frac_grad

    raise ValueError("Failed to interpolate profile at given depth.")  # pragma: no cover


def evaluate_mud_weight_at_depth(
    proposed_density_kg_m3: float,
    depth_m: float,
    profile: list[tuple[float, float, float]],
    trip_margin_kg_m3: float = 30.0,
    fracture_margin_kg_m3: float = 30.0,
) -> dict[str, float | str | bool]:
    """
    Evaluate a proposed mud density against the interpolated PP/FG window at
    one depth.

    Severity:
        "critical" -> outside [pore_pressure_density, fracture_density]
        "warning"  -> inside the window but within the safety margin of a boundary
        "ok"       -> safely inside the window

    Margins default to 30 kg/m3 (~0.25 ppg), a conservative trip margin;
    pass explicit values to match your lecturer's stated safety factor.
    """
    if proposed_density_kg_m3 <= 0:
        raise ValueError("Proposed mud density must be greater than zero.")

    pore_grad_pa_m, frac_grad_pa_m = interpolate_gradients_pa_m(profile, depth_m)
    pore_pressure_density_kg_m3 = pore_grad_pa_m / GRAVITY
    fracture_density_kg_m3 = frac_grad_pa_m / GRAVITY

    trip_margin = proposed_density_kg_m3 - pore_pressure_density_kg_m3
    fracture_margin = fracture_density_kg_m3 - proposed_density_kg_m3

    if proposed_density_kg_m3 < pore_pressure_density_kg_m3:
        severity = "critical"
        message = (
            f"Mud weight {proposed_density_kg_m3:,.1f} kg/m3 at {depth_m:,.0f}m is BELOW "
            f"pore pressure ({pore_pressure_density_kg_m3:,.1f} kg/m3). Kick risk."
        )
    elif proposed_density_kg_m3 > fracture_density_kg_m3:
        severity = "critical"
        message = (
            f"Mud weight {proposed_density_kg_m3:,.1f} kg/m3 at {depth_m:,.0f}m EXCEEDS "
            f"fracture gradient ({fracture_density_kg_m3:,.1f} kg/m3). Lost circulation risk."
        )
    elif trip_margin < trip_margin_kg_m3:
        severity = "warning"
        message = (
            f"Mud weight at {depth_m:,.0f}m is only {trip_margin:,.1f} kg/m3 above pore "
            f"pressure (recommended margin {trip_margin_kg_m3:,.1f} kg/m3). Narrow kick tolerance."
        )
    elif fracture_margin < fracture_margin_kg_m3:
        severity = "warning"
        message = (
            f"Mud weight at {depth_m:,.0f}m is only {fracture_margin:,.1f} kg/m3 below "
            f"fracture gradient (recommended margin {fracture_margin_kg_m3:,.1f} kg/m3). "
            f"Narrow lost-circulation tolerance."
        )
    else:
        severity = "ok"
        message = (
            f"Mud weight at {depth_m:,.0f}m is within the safe operational window "
            f"({pore_pressure_density_kg_m3:,.1f}-{fracture_density_kg_m3:,.1f} kg/m3)."
        )

    return {
        "depth_m": depth_m,
        "pore_pressure_density_kg_m3": pore_pressure_density_kg_m3,
        "fracture_density_kg_m3": fracture_density_kg_m3,
        "trip_margin_kg_m3": trip_margin,
        "fracture_margin_kg_m3": fracture_margin,
        "severity": severity,
        "message": message,
    }


def evaluate_profile(
    proposed_density_kg_m3: float,
    profile: list[tuple[float, float, float]],
    check_depths_m: list[float] | None = None,
    trip_margin_kg_m3: float = 30.0,
    fracture_margin_kg_m3: float = 30.0,
) -> dict[str, object]:
    """
    Evaluate one proposed mud density across multiple depths (defaults to
    every depth point in the profile). Returns per-depth alerts plus an
    overall verdict -- "critical" if any depth is outside the window,
    else "warning" if any depth is inside but within margin, else "ok".
    """
    if check_depths_m is not None and len(check_depths_m) == 0:
        raise ValueError("No depths supplied to evaluate.")
    depths = check_depths_m if check_depths_m is not None else [p[0] for p in profile]

    alerts = [
        evaluate_mud_weight_at_depth(
            proposed_density_kg_m3, depth, profile, trip_margin_kg_m3, fracture_margin_kg_m3
        )
        for depth in depths
    ]

    severities = [a["severity"] for a in alerts]
    if "critical" in severities:
        overall = "critical"
    elif "warning" in severities:
        overall = "warning"
    else:
        overall = "ok"

    return {
        "alerts": alerts,
        "overall_severity": overall,
        "is_safe": overall != "critical",
    }
