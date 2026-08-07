import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import hashlib
import time
import datetime
import math
from io import BytesIO

# ReportLab Imports for PDF Generation
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & PETROLEUM INDUSTRIAL THEMING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Intelligent Drill & Cement Suite Pro",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    /* Dark Petroleum Theme with Industrial Industrial Accents */
    .stApp {
        background-color: #080B10;
        color: #E2E8F0;
    }

    /* Hero Welcome Banner with Offshore Rig Background */
    .hero-container {
        text-align: center;
        padding: 60px 20px;
        background: linear-gradient(180deg, rgba(8, 11, 16, 0.75) 0%, rgba(8, 11, 16, 0.95) 100%),
                    url('https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=1600&q=80');
        background-size: cover;
        background-position: center;
        border: 1px solid #1E293B;
        border-radius: 16px;
        margin-bottom: 25px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.8);
    }
    .hero-title {
        font-size: 3rem;
        font-weight: 900;
        background: linear-gradient(90deg, #F59E0B, #38BDF8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
        letter-spacing: -0.5px;
    }
    .hero-subtitle {
        font-size: 1.15rem;
        color: #CBD5E1;
        max-width: 750px;
        margin: 0 auto 20px auto;
        text-shadow: 0 2px 4px rgba(0,0,0,0.8);
    }

    /* Feature Badge Cards with Background Highlights */
    .feature-card {
        background: linear-gradient(180deg, rgba(17, 24, 39, 0.85) 0%, rgba(15, 23, 42, 0.95) 100%),
                    url('https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&w=600&q=80');
        background-size: cover;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 22px;
        text-align: left;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
    }
    .feature-card:hover {
        border-color: #F59E0B;
    }

    .stMetric {
        background-color: #0F172A;
        padding: 14px;
        border-radius: 8px;
        border: 1px solid #1E293B;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# 2. SESSION STATE & USER DATABASE INITIALIZATION
# -----------------------------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

if "user_credentials" not in st.session_state:
    st.session_state.user_credentials = {
        "admin@drill.com": hash_password("password123"),
        "engineer@drill.com": hash_password("drill2026"),
        "worker1@drill.com": hash_password("worker123"),
    }

if "audit_logs" not in st.session_state:
    st.session_state.audit_logs = [{
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "event": "System Initialized",
        "user": "SYSTEM"
    }]

def log_event(event: str, user: str = "GUEST"):
    st.session_state.audit_logs.append({
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "event": event,
        "user": user
    })

# -----------------------------------------------------------------------------
# 3. AUTHENTICATION & WORKER REGISTRATION PORTAL
# -----------------------------------------------------------------------------
def render_login_portal():
    st.markdown(
        """
        <div class="hero-container">
            <div class="hero-title">Automate anything, anywhere in drilling.</div>
            <div class="hero-subtitle">
                Worker Access Portal: Real-time predictive telemetry, hydraulics optimization, and 3D cementing analytics.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_login, tab_register = st.tabs(["🔒 Worker Login", "➕ Register New Worker"])

    with tab_login:
        col1, col2, col3 = st.columns([1, 1.2, 1])
        with col2:
            st.subheader("Worker Sign In")
            with st.form("login_form", clear_on_submit=False):
                email = st.text_input("Worker Email Address", value="worker1@drill.com").strip().lower()
                password = st.text_input("Password", type="password", value="worker123")
                submit_btn = st.form_submit_button("Launch Intelligent Suite", use_container_width=True, type="primary")

                if submit_btn:
                    if not email or not password:
                        st.error("Please enter both email and password.")
                    elif email in st.session_state.user_credentials:
                        stored_hash = st.session_state.user_credentials[email]
                        if stored_hash == hash_password(password):
                            st.session_state.authenticated = True
                            st.session_state.current_user = email
                            log_event(f"Worker '{email}' logged in", user=email)
                            st.success("Access Granted!")
                            time.sleep(0.3)
                            st.rerun()
                        else:
                            st.error("Invalid password.")
                    else:
                        st.error("Worker email not found. Please register first.")

    with tab_register:
        col1, col2, col3 = st.columns([1, 1.2, 1])
        with col2:
            st.subheader("Add Worker Account")
            with st.form("register_form", clear_on_submit=True):
                new_email = st.text_input("New Worker Email").strip().lower()
                new_pass = st.text_input("New Worker Password", type="password")
                confirm_pass = st.text_input("Confirm Password", type="password")
                reg_btn = st.form_submit_button("Register Worker", use_container_width=True)

                if reg_btn:
                    if not new_email or not new_pass:
                        st.error("Please fill in all fields.")
                    elif "@" not in new_email or "." not in new_email:
                        st.error("Invalid email address format.")
                    elif new_pass != confirm_pass:
                        st.error("Passwords do not match.")
                    elif new_email in st.session_state.user_credentials:
                        st.error("Worker email already registered.")
                    else:
                        st.session_state.user_credentials[new_email] = hash_password(new_pass)
                        log_event(f"Registered new worker '{new_email}'", user="ADMIN")
                        st.success(f"Worker '{new_email}' registered successfully!")

    st.divider()

    # Petroleum Visual Feature Grid
    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        st.markdown('<div class="feature-card">📊 <b>Hydraulics Engine</b><br><small>Dynamic ECD monitoring & transport efficiency.</small></div>', unsafe_allow_html=True)
    with fc2:
        st.markdown('<div class="feature-card">🧱 <b>Cementing Matrix</b><br><small>Volumetric annulus modeling with washouts.</small></div>', unsafe_allow_html=True)
    with fc3:
        st.markdown('<div class="feature-card">🌐 <b>3D Telemetry</b><br><small>Spatial trajectories for casings and cements.</small></div>', unsafe_allow_html=True)
    with fc4:
        st.markdown('<div class="feature-card">🛡️ <b>Audit & Compliance</b><br><small>Automated PDF generation and logging.</small></div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 4. MAIN DASHBOARD APPLICATION
# -----------------------------------------------------------------------------
if not st.session_state.authenticated:
    render_login_portal()
else:
    # Header Banner with Active Rig Visual
    st.markdown(
        """
        <div style="padding:15px; border-radius:10px; background: linear-gradient(90deg, rgba(15,23,42,0.9) 0%, rgba(30,41,59,0.8) 100%), url('https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=1200&q=80'); background-size:cover;">
            <h2 style="margin:0; color:#F59E0B;">🏗️ Offshore Drilling Rig Operations Hub</h2>
            <p style="margin:0; color:#94A3B8;">Intelligent Mud & Cement Design Suite (PyMudCement-Optima)</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    top_col1, top_col2 = st.columns([4, 1])
    with top_col1:
        st.caption(f"Active Worker Session: **{st.session_state.current_user}**")
    with top_col2:
        if st.button("Log Out", use_container_width=True):
            log_event("Worker logged out", user=st.session_state.current_user)
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.rerun()

    st.divider()

    # SIDEBAR CONTROL PANEL
    st.sidebar.markdown("## ⚙️ Global Wellbore Parameters")
    with st.sidebar.form(key="global_inputs_form"):
        well_profile = st.selectbox("Well Profile", options=["Vertical Well", "S-Type Directional", "Horizontal / ERD"], index=1)
        target_tvd = st.number_input("Target TVD (ft)", min_value=1000.0, max_value=35000.0, value=10000.0, step=500.0)
        hole_dia = st.number_input("Open Hole Diameter [in]", value=12.25, step=0.125)
        casing_od = st.number_input("Casing Outer Diameter [in]", value=9.625, step=0.125)
        casing_id = st.number_input("Casing Inner Diameter [in]", value=8.835, step=0.125)
        washout_pct = st.slider("Washout Factor (%)", 0, 50, 15)
        toc_depth = st.number_input("Top of Cement (TOC) Depth [ft]", value=3000.0, step=250.0)

        pore_pressure_grad = st.number_input("Pore Pressure Grad (psi/ft)", min_value=0.001, max_value=2.000, value=0.465, step=0.01)
        fracture_grad = st.number_input("Fracture Grad (psi/ft)", min_value=0.001, max_value=3.000, value=0.750, step=0.01)
        bottomhole_temp = st.number_input("Bottomhole Temp (°F)", min_value=60.0, max_value=450.0, value=240.0, step=5.0)

        run_btn = st.form_submit_button("🚀 Update 3D Models & Analytics", type="primary", use_container_width=True)

    # WORKER MANAGEMENT SECTION IN SIDEBAR
    st.sidebar.divider()
    st.sidebar.markdown("## 👥 Worker Account Management")
    with st.sidebar.expander("Registered Workers"):
        for u in st.session_state.user_credentials.keys():
            st.text(f"• {u}")

    # Dynamic State Binding
    st.session_state.well_profile = well_profile
    st.session_state.target_tvd = target_tvd
    st.session_state.hole_dia = hole_dia
    st.session_state.casing_od = casing_od
    st.session_state.casing_id = casing_id
    st.session_state.washout_pct = washout_pct
    st.session_state.toc_depth = toc_depth
    st.session_state.pore_pressure_grad = pore_pressure_grad
    st.session_state.fracture_grad = fracture_grad
    st.session_state.bottomhole_temp = bottomhole_temp

    # MAIN APPLICATION TABS
    tab_telemetry, tab_casing_3d, tab_hydraulics, tab_cementing, tab_audit = st.tabs([
        "🌐 3D Wellbore Telemetry",
        "🧱 3D Casing & Cementing Model",
        "📊 Dynamic Hydraulics Engine",
        "📐 Volumetric Cementing Matrix",
        "🛡️ Operations Audit & PDF Export"
    ])

    # -------------------------------------------------------------------------
    # TAB 1: REAL 3D WELLBORE TELEMETRY
    # -------------------------------------------------------------------------
    with tab_telemetry:
        st.subheader(f"3D Wellbore Trajectory & Directional Telemetry ({well_profile})")

        tvd_val = st.session_state.target_tvd
        md_steps = 150
        md = np.linspace(0, tvd_val * 1.25 if well_profile != "Vertical Well" else tvd_val, md_steps)

        if well_profile == "Vertical Well":
            inc = np.zeros(md_steps)
            azm = np.zeros(md_steps)
            tvd_arr = md
            north = np.zeros(md_steps)
            east = np.zeros(md_steps)
        elif well_profile == "S-Type Directional":
            inc = np.sin(np.pi * md / tvd_val) * 45.0
            azm = np.full(md_steps, 60.0)
            tvd_arr = np.cumsum(np.cos(np.radians(inc)) * (md[1] - md[0]))
            disp = np.cumsum(np.sin(np.radians(inc)) * (md[1] - md[0]))
            north = disp * np.cos(np.radians(60.0))
            east = disp * np.sin(np.radians(60.0))
        else:
            inc = np.where(md < tvd_val * 0.6, (md / (tvd_val * 0.6)) * 90.0, 90.0)
            azm = np.full(md_steps, 120.0)
            tvd_arr = np.cumsum(np.cos(np.radians(inc)) * (md[1] - md[0]))
            disp = np.cumsum(np.sin(np.radians(inc)) * (md[1] - md[0]))
            north = disp * np.cos(np.radians(120.0))
            east = disp * np.sin(np.radians(120.0))

        fig_3d = go.Figure(data=[go.Scatter3d(
            x=east, y=north, z=-tvd_arr,
            mode="lines+markers",
            marker=dict(size=3, color=md, colorscale="Turbo", showscale=True, colorbar=dict(title="MD (ft)")),
            line=dict(color="#38BDF8", width=6),
            name="Wellbore Path"
        )])

        fig_3d.update_layout(
            scene=dict(
                xaxis_title="East / West Displacement (ft)",
                yaxis_title="North / South Displacement (ft)",
                zaxis_title="True Vertical Depth (ft)",
                aspectmode="manual",
                aspectratio=dict(x=1, y=1, z=1.5)
            ),
            template="plotly_dark",
            height=550,
            margin=dict(l=0, r=0, b=0, t=30)
        )
        st.plotly_chart(fig_3d, use_container_width=True)

        st.markdown("##### 📍 Live Survey & Directional Telemetry Table")
        df_survey = pd.DataFrame({
            "Measured Depth (ft)": np.round(md[::15], 1),
            "TVD (ft)": np.round(tvd_arr[::15], 1),
            "Inclination (°)": np.round(inc[::15], 2),
            "Azimuth (°)": np.round(azm[::15], 2),
            "North Displacement (ft)": np.round(north[::15], 1),
            "East Displacement (ft)": np.round(east[::15], 1)
        })
        st.dataframe(df_survey, use_container_width=True)

    # -------------------------------------------------------------------------
    # TAB 2: REAL 3D CASING & CEMENTING ANNULUS VISUALIZER
    # -------------------------------------------------------------------------
    with tab_casing_3d:
        st.subheader("Interactive 3D Wellbore Geometry, Casing & Cement Visualizer")

        tvd = st.session_state.target_tvd
        toc = st.session_state.toc_depth
        r_hole = (st.session_state.hole_dia * math.sqrt(1 + st.session_state.washout_pct/100.0)) / 2.0
        r_cas_od = st.session_state.casing_od / 2.0
        r_cas_id = st.session_state.casing_id / 2.0

        def make_cylinder(r, z_top, z_bottom, n_points=30):
            theta = np.linspace(0, 2*np.pi, n_points)
            z_grid = np.linspace(z_top, z_bottom, 2)
            theta_grid, z_grid = np.meshgrid(theta, z_grid)
            x_grid = r * np.cos(theta_grid)
            y_grid = r * np.sin(theta_grid)
            return x_grid, y_grid, z_grid

        x_h, y_h, z_h = make_cylinder(r_hole, 0, -tvd)
        x_c_od, y_c_od, z_c_od = make_cylinder(r_cas_od, 0, -tvd)
        x_cem, y_cem, z_cem = make_cylinder(r_hole * 0.98, -toc, -tvd)

        fig_geo = go.Figure()
        fig_geo.add_trace(go.Surface(x=x_h, y=y_h, z=z_h, opacity=0.15, colorscale=[[0, '#94A3B8'], [1, '#94A3B8']], showscale=False, name="Open Hole Wall"))
        fig_geo.add_trace(go.Surface(x=x_cem, y=y_cem, z=z_cem, opacity=0.6, colorscale=[[0, '#F59E0B'], [1, '#F59E0B']], showscale=False, name="Cement Column"))
        fig_geo.add_trace(go.Surface(x=x_c_od, y=y_c_od, z=z_c_od, opacity=0.9, colorscale=[[0, '#38BDF8'], [1, '#38BDF8']], showscale=False, name="Casing String"))

        fig_geo.update_layout(
            scene=dict(
                xaxis_title="X (in)",
                yaxis_title="Y (in)",
                zaxis_title="TVD (ft)",
                aspectmode="manual",
                aspectratio=dict(x=1, y=1, z=3)
            ),
            template="plotly_dark",
            height=550,
            margin=dict(l=0, r=0, b=0, t=30)
        )

        g1, g2 = st.columns([2.5, 1])
        with g1:
            st.plotly_chart(fig_geo, use_container_width=True)
        with g2:
            st.markdown("##### 📐 Section Metrics")
            st.metric("Effective Hole Radius", f"{r_hole:.2f} in")
            st.metric("Casing Outer Radius", f"{r_cas_od:.2f} in")
            st.metric("Cement Column Height", f"{max(0.0, tvd - toc):,.0f} ft")
            st.info("🟧 **Orange Surface:** Cement Column\n\n🟦 **Blue Surface:** Steel Casing\n\n⬜ **Outer Grey:** Borehole Wall")

    # -------------------------------------------------------------------------
    # TAB 3: DYNAMIC HYDRAULICS ENGINE
    # -------------------------------------------------------------------------
    with tab_hydraulics:
        st.subheader("Dynamic Hydraulics & Hole Cleaning Engine")

        c1, c2 = st.columns(2)
        with c1:
            mw = st.slider("Mud Weight (ppg)", 8.0, 20.0, 10.2, 0.1)
            pv = st.slider("Plastic Viscosity (cP)", 5, 50, 20, 1)
            yp = st.slider("Yield Point (lb/100ft²)", 5, 40, 15, 1)
        with c2:
            annular_dp = st.slider("Annular Pressure Drop (psi)", 50, 500, 150, 10)
            gpm = st.slider("Flow Rate (GPM)", 200, 1000, 500, 25)

        tvd = st.session_state.target_tvd
        ecd = mw + (annular_dp / (0.052 * tvd)) if tvd > 0 else mw
        eff = min(max((gpm / 600.0) * 45.0 + (yp / (pv if pv > 0 else 1)) * 30.0 + (mw / 10.0) * 20.0, 35.0), 98.5)

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("PLASTIC VISCOSITY", f"{pv:.1f} cP")
        k2.metric("YIELD POINT", f"{yp:.1f} lb/100ft²")
        k3.metric("ANNULAR DP (LOSS)", f"{annular_dp:.1f} psi")
        k4.metric("DYNAMIC ECD", f"{ecd:.2f} ppg")

        st.markdown(f"**Hole Cleaning / Cuttings Transport Efficiency: {eff:.1f}%**")
        st.progress(eff / 100.0)

        # Matplotlib Graph
        st.markdown("### Interactive Wellbore Pressure Profile")
        depths = np.linspace(0, tvd, 100)
        pore_p = st.session_state.pore_pressure_grad * depths
        frac_p = st.session_state.fracture_grad * depths
        mud_p = (mw * 0.052) * depths

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(pore_p, depths, label="Pore Pressure", color="blue")
        ax.plot(frac_p, depths, label="Fracture Gradient", color="red")
        ax.plot(mud_p, depths, label="Recommended Mud Weight", color="brown", linestyle="--")
        ax.fill_betweenx(depths, pore_p, frac_p, color='gray', alpha=0.2, label="Safe Drilling Window")

        ax.invert_yaxis()
        ax.set_xlabel("Pressure (psi)")
        ax.set_ylabel("Depth (ft)")
        ax.legend(loc="lower left")
        st.pyplot(fig)

    # -------------------------------------------------------------------------
    # TAB 4: VOLUMETRIC CEMENTING MATRIX
    # -------------------------------------------------------------------------
    with tab_cementing:
        st.subheader("Volumetric Cementing & Additive Matrix")

        cc1, cc2 = st.columns(2)
        with cc1:
            st.markdown("##### 📏 Input Parameters")
            h_dia = st.session_state.hole_dia
            c_od = st.session_state.casing_od
            c_id = st.session_state.casing_id
            w_pct = st.session_state.washout_pct
            shoe = st.session_state.target_tvd
            toc = st.session_state.toc_depth

            slurry_den = st.number_input("Slurry Density [ppg]", value=15.80, step=0.1)
            slurry_yield = st.number_input("Slurry Yield [cu.ft/sk]", value=1.18, step=0.01)

        cement_h = max(0.0, shoe - toc)
        eff_h_dia = math.sqrt((h_dia**2) * (1.0 + w_pct / 100.0))
        annular_cap = (eff_h_dia**2 - c_od**2) / 1029.4
        annular_vol_bbl = annular_cap * cement_h
        sacks_req = (annular_vol_bbl * 5.61458) / slurry_yield if slurry_yield > 0 else 0
        disp_vol_bbl = ((c_id**2) / 1029.4) * shoe

        with cc2:
            st.markdown("##### 📊 Primary Cementing Deliverables")
            st.metric("Annular Cement Vol (w/ Washouts)", f"{annular_vol_bbl:,.1f} bbl")
            st.metric("Total Cement Sacks Required", f"{int(sacks_req):,} sks")
            st.metric("Displacement Volume Required", f"{disp_vol_bbl:,.1f} bbl")

            st.divider()
            st.markdown("##### 🧬 Additive Selection Matrix")
            bht = st.session_state.bottomhole_temp
            st.info(f"**Matched Additives for BHT {bht:.1f}°F:**\n"
                    f"* Lignosulfonate Retarder (0.4% BWOC)\n"
                    f"* Silica Flour (35% BWOC - Prevents Strength Retrogression)")

    # -------------------------------------------------------------------------
    # TAB 5: OPERATIONS AUDIT & PDF JOB SHEET EXPORT
    # -------------------------------------------------------------------------
    with tab_audit:
        st.subheader("Operations Audit & PDF Job Sheet Export")

        ac1, ac2 = st.columns(2)
        with ac1:
            st.markdown("##### 📄 Export Milestone Deliverable")

            def generate_pdf():
                log_event("Generated PDF Job Sheet", user=st.session_state.current_user)
                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
                story = []
                styles = getSampleStyleSheet()

                title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#0284c7'), spaceAfter=12)
                story.append(Paragraph("DIGITAL DRILLING & CEMENTING JOB SHEET REPORT", title_style))
                story.append(Paragraph(f"<b>Generated:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC | <b>Worker:</b> {st.session_state.current_user}", styles['Normal']))
                story.append(Spacer(1, 12))

                data = [
                    ["Parameter Description", "Calculated Deliverable Value"],
                    ["Target True Vertical Depth (TVD)", f"{st.session_state.target_tvd:,.0f} ft"],
                    ["Dynamic ECD", f"{ecd:.2f} ppg"],
                    ["Cuttings Transport Efficiency", f"{eff:.1f} %"],
                    ["Annular Cement Volume (w/ Washout)", f"{annular_vol_bbl:,.1f} bbl"],
                    ["Total Cement Sacks Required", f"{int(sacks_req):,} sks"]
                ]
                t_calc = Table(data, colWidths=[250, 200])
                t_calc.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f172a')),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
                    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')])
                ]))
                story.append(Paragraph("<b>1. Key Engineering Deliverables</b>", styles['Heading2']))
                story.append(Spacer(1, 6))
                story.append(t_calc)
                story.append(Spacer(1, 14))

                audit_data = [["Timestamp", "Event Description", "Worker"]]
                for entry in st.session_state.audit_logs:
                    audit_data.append([entry['timestamp'], entry['event'], entry['user']])

                t_audit = Table(audit_data, colWidths=[120, 230, 100])
                t_audit.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#334155')),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94a3b8')),
                    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f1f5f9')])
                ]))
                story.append(Paragraph("<b>2. Operations Audit Trail</b>", styles['Heading2']))
                story.append(Spacer(1, 6))
                story.append(t_audit)

                doc.build(story)
                buffer.seek(0)
                return buffer.getvalue()

            pdf_data = generate_pdf()
            st.download_button(
                label="⬇ DOWNLOAD DIGITAL CEMENTING JOB SHEET (PDF)",
                data=pdf_data,
                file_name="Digital_Cementing_Job_Sheet.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )

        with ac2:
            st.markdown("##### 📜 Real-Time Audit Logs Stream")
            df_audit = pd.DataFrame(st.session_state.audit_logs)
            st.dataframe(df_audit.iloc[::-1], use_container_width=True, height=300)
