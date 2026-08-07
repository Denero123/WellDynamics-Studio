import sys
from pathlib import Path

# Force Python to see the root repository directory
sys.path.append(str(Path(__file__).resolve().parent))

import streamlit as st

from src.engineering.mud import (
    hydrostatic_pressure_pa,
    required_mud_density_kg_m3,
    mud_weight_ppg,
    safe_mud_window,
    bingham_shear_stress_pa,
)
from src.engineering.cementing import (
    annular_volume_m3,
    cement_volume_with_excess_m3,
    fluid_sweep_volumes,
)
from src.engineering.hydraulics import ecd_kg_m3
from src.engineering.rheology import analyze_annular_hydraulics
from src.engineering.mud_weight_window import validate_profile, evaluate_profile
from src.core.validation import validate_positive, validate_fraction
from src.core.logging_config import configure_logging

configure_logging()

st.set_page_config(
    page_title="PyMudCement-Optima",
    page_icon="🛢️",
    layout="wide",
)

st.title("PyMudCement-Optima")
st.caption("PENG 258 • Drilling Fluids, Hydraulics & Cementing Engineering")

with st.sidebar:
    st.header("Navigation")
    page = st.radio(
        "Module",
        [
            "Dashboard",
            "Mud & Pressure",
            "Rheology",
            "Cement Volumes",
            "Hydraulics & ECD",
            "Annular Hydraulics (Physics-Based ECD)",
            "MW Window (Depth Profile)",
        ],
    )
    st.divider()
    st.caption("Engineering calculations are based on the PENG 258 project specification.")

if page == "Dashboard":
    st.subheader("Engineering dashboard")
    c1, c2, c3 = st.columns(3)
    c1.metric("Core modules", "6")
    c2.metric("Primary models", "5+")
    c3.metric("Validation", "Input-driven")

    st.info(
        "Use the modules on the left to calculate mud pressure balance, "
        "Bingham-plastic rheology, annular cement volumes, physics-based "
        "annular hydraulics/ECD, and depth-profile mud-weight window alerts."
    )

    st.markdown("""
### Project scope
- Mud density required to balance formation pressure
- Safe mud-weight window using pore-pressure and fracture-gradient inputs (single depth)
- Safe mud-weight window evaluated across a full depth-indexed PP/FG profile
- PV/YP rheology using the Bingham-plastic model
- Annular cement volume with open-hole excess
- Slurry, spacer, flush and displacement sweep volumes
- ECD from user-supplied circulating pressure loss
- ECD calculated directly from geometry and flow rate via a Bingham-plastic
  annular friction model (Reynolds number, flow-regime classification,
  frictional pressure drop), plus a cuttings-transport screening check

### Engineering modelling notes
The supplied PENG 258 PDF specifies the required capabilities and core equations
but does not mandate a single pressure-loss correlation. This suite offers both
options: `Hydraulics & ECD` accepts a user-supplied circulating pressure loss,
while `Annular Hydraulics (Physics-Based ECD)` calculates that loss internally
using a standard Bingham-plastic annular friction model. The cuttings-transport
check in the latter is a conservative screening heuristic, not a full
slip-velocity correlation -- documented as a stated limitation.
""")

elif page == "Mud & Pressure":
    st.subheader("Mud & Pressure Balance")
    st.write("Calculate hydrostatic pressure and the mud density required to balance formation pressure.")

    col1, col2 = st.columns(2)
    with col1:
        depth = st.number_input("True vertical depth (m)", min_value=0.001, value=2500.0)
        density = st.number_input("Mud density (kg/m³)", min_value=0.001, value=1200.0)
        formation_pressure = st.number_input("Formation pressure (Pa)", min_value=0.0, value=29_430_000.0)

    with col2:
        pore_gradient = st.number_input("Pore pressure gradient (Pa/m)", min_value=0.0, value=11772.0)
        fracture_gradient = st.number_input("Fracture gradient (Pa/m)", min_value=0.0, value=16000.0)

    if st.button("Calculate pressure balance", type="primary"):
        try:
            validate_positive(depth, "TVD")
            validate_positive(density, "Mud density")
            if formation_pressure < 0:
                raise ValueError("Formation pressure cannot be negative.")

            hydro = hydrostatic_pressure_pa(density, depth)
            required_density = required_mud_density_kg_m3(formation_pressure, depth)
            current_ppg = mud_weight_ppg(density)
            required_ppg = mud_weight_ppg(required_density)

            low_density, high_density = safe_mud_window(
                pore_gradient, fracture_gradient, depth
            )

            st.metric("Hydrostatic pressure", f"{hydro:,.0f} Pa")
            st.metric("Current mud weight", f"{current_ppg:.2f} ppg")
            st.metric("Required mud weight", f"{required_ppg:.2f} ppg")

            if low_density <= required_density <= high_density:
                st.success("Required mud density is inside the calculated operational window.")
            else:
                st.warning("Required mud density falls outside the calculated operational window.")

            st.write(
                f"Safe density window: **{low_density:,.1f}–{high_density:,.1f} kg/m³**"
            )
        except ValueError as exc:
            st.error(str(exc))

elif page == "Rheology":
    st.subheader("Bingham-Plastic Rheology")
    st.write("Calculate shear stress from Yield Point, Plastic Viscosity and shear rate.")

    col1, col2 = st.columns(2)
    with col1:
        yp = st.number_input("Yield Point, YP (Pa)", min_value=0.0, value=10.0)
        pv = st.number_input("Plastic Viscosity, PV (Pa·s)", min_value=0.0, value=0.03)
    with col2:
        shear_rate = st.number_input("Shear rate (s⁻¹)", min_value=0.0, value=100.0)

    if st.button("Calculate shear stress", type="primary"):
        try:
            tau = bingham_shear_stress_pa(yp, pv, shear_rate)
            st.metric("Shear stress", f"{tau:,.3f} Pa")
        except ValueError as exc:
            st.error(str(exc))

elif page == "Cement Volumes":
    st.subheader("Cementing Volumetrics")
    st.write("Calculate annular volume and apply an open-hole excess/washout factor.")

    col1, col2 = st.columns(2)
    with col1:
        hole_diameter = st.number_input("Open-hole diameter (m)", min_value=0.0001, value=0.2159)
        casing_od = st.number_input("Casing outer diameter (m)", min_value=0.0001, value=0.1397)
    with col2:
        interval_length = st.number_input("Cemented interval length (m)", min_value=0.0001, value=1000.0)
        excess = st.number_input("Open-hole excess (%)", min_value=0.0, max_value=500.0, value=15.0)

    if st.button("Calculate cement volume", type="primary"):
        try:
            validate_positive(hole_diameter, "Hole diameter")
            validate_positive(casing_od, "Casing OD")
            validate_positive(interval_length, "Interval length")
            validate_fraction(excess / 100.0, "Excess")

            if hole_diameter <= casing_od:
                raise ValueError("Open-hole diameter must be greater than casing OD.")

            base = annular_volume_m3(hole_diameter, casing_od, interval_length)
            design = cement_volume_with_excess_m3(base, excess / 100.0)

            st.metric("Base annular volume", f"{base:,.3f} m³")
            st.metric("Design cement volume", f"{design:,.3f} m³")
        except ValueError as exc:
            st.error(str(exc))

    st.divider()
    st.subheader("Fluid sweep volumes")
    annular = st.number_input("Reference annular volume (m³)", min_value=0.0001, value=20.0, key="sweep_ann")
    spacer_pct = st.number_input("Spacer (% of annular volume)", min_value=0.0, value=20.0, key="spacer_pct")
    flush_pct = st.number_input("Flush (% of annular volume)", min_value=0.0, value=10.0, key="flush_pct")
    displacement_pct = st.number_input("Displacement (% of annular volume)", min_value=0.0, value=100.0, key="disp_pct")

    if st.button("Calculate sweep volumes"):
        try:
            sweeps = fluid_sweep_volumes(
                annular,
                spacer_pct / 100,
                flush_pct / 100,
                displacement_pct / 100,
            )
            for name, value in sweeps.items():
                st.metric(name.replace("_", " ").title(), f"{value:,.3f} m³")
        except ValueError as exc:
            st.error(str(exc))

elif page == "Hydraulics & ECD":
    st.subheader("Hydraulics & Equivalent Circulating Density")
    st.warning(
        "The project PDF requires dynamic pressure-drop modelling but does not provide "
        "a pressure-loss correlation. This module therefore accepts calculated/supplied "
        "circulating pressure loss rather than silently inventing a correlation."
    )

    density = st.number_input("Static mud density (kg/m³)", min_value=0.001, value=1200.0)
    pressure_loss = st.number_input("Circulating pressure loss (Pa)", min_value=0.0, value=2_000_000.0)
    tvd = st.number_input("TVD (m)", min_value=0.001, value=2500.0)

    if st.button("Calculate ECD", type="primary"):
        try:
            ecd = ecd_kg_m3(density, pressure_loss, tvd)
            st.metric("ECD", f"{ecd:,.2f} kg/m³")
        except ValueError as exc:
            st.error(str(exc))

elif page == "Annular Hydraulics (Physics-Based ECD)":
    st.subheader("Annular Hydraulics & Physics-Based ECD")
    st.write(
        "Calculates annular velocity, Reynolds number, flow regime, frictional "
        "pressure drop and ECD directly from wellbore geometry and flow rate "
        "using a Bingham-plastic annular friction model -- no manually supplied "
        "pressure loss required."
    )

    col1, col2 = st.columns(2)
    with col1:
        flow_rate_lpm = st.number_input("Flow rate (L/min)", min_value=1.0, value=1500.0)
        hole_diameter_mm = st.number_input("Hole diameter (mm)", min_value=1.0, value=216.0)
        pipe_od_mm = st.number_input("Pipe OD (mm)", min_value=1.0, value=127.0)
    with col2:
        interval_length = st.number_input(
            "Interval length (m)", min_value=1.0, value=1200.0, key="rheo_length"
        )
        tvd_rheo = st.number_input("TVD at base of interval (m)", min_value=1.0, value=1200.0, key="rheo_tvd")
        density_rheo = st.number_input("Static mud density (kg/m³)", min_value=1.0, value=1200.0, key="rheo_density")

    col3, col4 = st.columns(2)
    with col3:
        pv_rheo = st.number_input("Plastic viscosity, PV (Pa·s)", min_value=0.0, value=0.025, key="rheo_pv")
    with col4:
        yp_rheo = st.number_input("Yield point, YP (Pa)", min_value=0.0, value=12.0, key="rheo_yp")

    if st.button("Calculate hydraulics & ECD", type="primary"):
        try:
            flow_rate_m3_s = flow_rate_lpm / 60_000.0
            result = analyze_annular_hydraulics(
                flow_rate_m3_s=flow_rate_m3_s,
                hole_diameter_m=hole_diameter_mm / 1000.0,
                pipe_od_m=pipe_od_mm / 1000.0,
                interval_length_m=interval_length,
                tvd_m=tvd_rheo,
                static_density_kg_m3=density_rheo,
                plastic_viscosity_pa_s=pv_rheo,
                yield_point_pa=yp_rheo,
            )

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Flow regime", str(result["flow_regime"]).title())
            m2.metric("Annular velocity", f"{result['annular_velocity_m_s']:.3f} m/s")
            m3.metric("Reynolds number", f"{result['reynolds_number']:,.0f}")
            m4.metric("ECD", f"{result['ecd_kg_m3']:,.1f} kg/m³")

            st.metric("Friction pressure drop", f"{result['friction_pressure_drop_pa']:,.0f} Pa")

            if result["cuttings_transport_ok"]:
                st.success(
                    f"Cuttings transport OK -- velocity margin "
                    f"{result['cuttings_transport_margin_m_s']:.3f} m/s above the minimum."
                )
            else:
                st.warning(
                    f"Cuttings transport may be inadequate -- velocity is "
                    f"{abs(result['cuttings_transport_margin_m_s']):.3f} m/s below the "
                    f"recommended minimum. Consider raising flow rate or fluid YP."
                )
        except ValueError as exc:
            st.error(str(exc))

    st.caption(
        "Limitation: the minimum-transport-velocity check is a conservative screening "
        "heuristic, not a full slip-velocity (e.g. Moore) correlation. State this as a "
        "modelling limitation in the technical report."
    )

elif page == "MW Window (Depth Profile)":
    st.subheader("Safe Mud-Weight Window -- Depth Profile")
    st.write(
        "Milestone 1: alerts if a designed mud weight falls outside the safe "
        "operational window, evaluated across a full depth-indexed pore-pressure "
        "/ fracture-gradient profile rather than a single depth."
    )

    st.caption(
        "Enter profile points as depth (m), pore pressure gradient (kPa/m), "
        "fracture gradient (kPa/m), one per line, e.g. `0,10.0,15.0`."
    )
    default_profile_text = "0,10.0,15.0\n1500,11.5,16.5\n3000,13.0,18.5"
    profile_text = st.text_area("PP/FG profile", value=default_profile_text, height=120)

    proposed_density = st.number_input(
        "Proposed mud density (kg/m³)", min_value=1.0, value=1250.0, key="mw_profile_density"
    )
    col1, col2 = st.columns(2)
    with col1:
        trip_margin = st.number_input("Min trip margin above PP (kg/m³)", min_value=0.0, value=30.0)
    with col2:
        frac_margin = st.number_input("Min margin below FG (kg/m³)", min_value=0.0, value=30.0)

    if st.button("Evaluate mud weight window", type="primary"):
        try:
            profile: list[tuple[float, float, float]] = []
            for line_num, line in enumerate(profile_text.strip().splitlines(), start=1):
                parts = [p.strip() for p in line.split(",")]
                if len(parts) != 3:
                    raise ValueError(f"Line {line_num} must have 3 comma-separated values.")
                depth_m, pore_kpa_m, frac_kpa_m = (float(p) for p in parts)
                profile.append((depth_m, pore_kpa_m * 1000.0, frac_kpa_m * 1000.0))

            validate_profile(profile)
            report = evaluate_profile(
                proposed_density_kg_m3=proposed_density,
                profile=profile,
                trip_margin_kg_m3=trip_margin,
                fracture_margin_kg_m3=frac_margin,
            )

            severity_display = {"ok": "🟢 OK", "warning": "🟡 WARNING", "critical": "🔴 CRITICAL"}
            st.markdown(f"### Overall status: {severity_display[report['overall_severity']]}")

            if not report["is_safe"]:
                st.error(
                    "This mud weight design falls outside the safe operational window "
                    "at one or more depths."
                )

            for alert in report["alerts"]:
                icon = severity_display[alert["severity"]]
                with st.expander(f"{icon} {alert['depth_m']:,.0f} m"):
                    st.write(alert["message"])
                    c1, c2 = st.columns(2)
                    c1.metric("Pore pressure density", f"{alert['pore_pressure_density_kg_m3']:,.1f} kg/m³")
                    c2.metric("Fracture density", f"{alert['fracture_density_kg_m3']:,.1f} kg/m³")

        except ValueError as exc:
            st.error(str(exc))
