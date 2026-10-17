"""
SkillSync AI — Streamlit Dashboard
IBM Z Datathon 2026 | Event Code: SSF2026
Running on IBM LinuxONE Community Cloud (s390x)
"""
import os
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ─── Config ──────────────────────────────────────────────────────────────────

API_BASE = os.getenv("API_BASE", "http://localhost:8000")
HEADERS  = {"X-API-Key": os.getenv("MANAGER_API_KEY", "manager-secret-key-2026")}

IBM_BLUE  = "#0062FF"
IBM_RED   = "#DA1E28"
IBM_GREEN = "#198038"
IBM_ORANGE= "#FF832B"
IBM_GRAY  = "#697077"

SEVERITY_COLOR = {
    "critical": IBM_RED,
    "moderate": IBM_ORANGE,
    "low":      "#F1C21B",
    "ok":       IBM_GREEN,
}

st.set_page_config(
    page_title="SkillSync AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ──────────────────────────────────────────────────────────────

st.markdown("""
<style>
[data-testid="stSidebar"] { background: #161616; }
[data-testid="stSidebar"] * { color: #f4f4f4 !important; }
.kpi-card { background:#f4f4f4; border-left:4px solid #0062FF;
            padding:14px 18px; border-radius:4px; margin-bottom:10px; }
.kpi-card h2 { margin:0; font-size:2rem; color:#0062FF; }
.kpi-card p  { margin:0; font-size:0.85rem; color:#697077; }
.critical-badge { background:#DA1E28; color:white; padding:2px 8px;
                  border-radius:12px; font-size:0.78rem; font-weight:600; }
.moderate-badge { background:#FF832B; color:white; padding:2px 8px;
                  border-radius:12px; font-size:0.78rem; font-weight:600; }
.ok-badge       { background:#198038; color:white; padding:2px 8px;
                  border-radius:12px; font-size:0.78rem; font-weight:600; }
footer-note { font-size: 0.75rem; color: #697077; text-align: center; }
</style>
""", unsafe_allow_html=True)

# ─── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/5/51/IBM_logo.svg", width=80)
    st.markdown("## SkillSync AI")
    st.markdown("**IBM Z Datathon 2026**")
    st.markdown(f"Event Code: `SSF2026`")
    st.markdown("---")
    page = st.radio(
        "Navigation",
        [
            "🏠 Dashboard",
            "👥 Workforce Map",
            "🔍 Skill Gap Analysis",
            "📚 Learning Path",
            "⚙️  Allocation Engine",
            "⏱️  Deadline Simulation",
        ],
    )
    st.markdown("---")
    st.caption("Powered by IBM LinuxONE Community Cloud (s390x)")


# ─── Helper: API calls ────────────────────────────────────────────────────────

@st.cache_data(ttl=30)
def fetch_employees():
    try:
        r = requests.get(f"{API_BASE}/employees", headers=HEADERS, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return []


@st.cache_data(ttl=30)
def fetch_projects():
    try:
        r = requests.get(f"{API_BASE}/projects", headers=HEADERS, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return []


def fetch_gaps(project_id: int):
    r = requests.post(f"{API_BASE}/gaps/detect/{project_id}", headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json()


def fetch_learning_path(employee_id: int, skill: str, target: int, deadline: int):
    payload = {
        "employee_id": employee_id,
        "skill_name": skill,
        "target_proficiency": target,
        "project_deadline_days": deadline,
    }
    r = requests.post(f"{API_BASE}/learning-path", json=payload, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json()


def fetch_allocation():
    r = requests.post(f"{API_BASE}/allocate", headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def fetch_simulation(deadline_changes: dict):
    r = requests.post(
        f"{API_BASE}/simulate/deadline-change",
        json={"deadline_changes": {str(k): v for k, v in deadline_changes.items()}},
        headers=HEADERS,
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def footer():
    st.markdown("---")
    st.markdown(
        "<p style='text-align:center;font-size:0.75rem;color:#697077;'>"
        "⚡ Running on <b>IBM LinuxONE Community Cloud (s390x)</b> &nbsp;|&nbsp; "
        "Event Code: <b>SSF2026</b> &nbsp;|&nbsp; IBM Z Datathon 2026</p>",
        unsafe_allow_html=True,
    )


# ═════════════════════════════════════════════════════════════════════════════
# PAGE 1 — Dashboard
# ═════════════════════════════════════════════════════════════════════════════

if page == "🏠 Dashboard":
    st.title("⚡ SkillSync AI — Workforce Intelligence Dashboard")
    st.caption("Predict skill gaps · Generate learning paths · Optimize project allocation")

    employees = fetch_employees()
    projects  = fetch_projects()

    if not employees or not projects:
        st.warning("Start the backend API and seed the database first.")
        footer()
        st.stop()

    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class='kpi-card'>
            <h2>{len(employees)}</h2><p>Total Employees</p></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class='kpi-card'>
            <h2>{len(projects)}</h2><p>Active Projects</p></div>""", unsafe_allow_html=True)

    # Quick gap scan for KPIs
    total_critical = 0
    project_coverages = []
    for proj in projects:
        try:
            gap_data = fetch_gaps(proj["id"])
            total_critical += gap_data.get("critical_count", 0)
            project_coverages.append({
                "Project": proj["name"][:30],
                "Coverage %": gap_data.get("overall_coverage_pct", 0),
                "Priority": proj["priority"],
            })
        except Exception:
            project_coverages.append({
                "Project": proj["name"][:30],
                "Coverage %": 0,
                "Priority": proj["priority"],
            })

    with col3:
        st.markdown(f"""<div class='kpi-card'>
            <h2 style='color:#DA1E28'>{total_critical}</h2><p>Critical Skill Gaps</p></div>""",
            unsafe_allow_html=True)
    avg_cov = round(sum(p["Coverage %"] for p in project_coverages) / len(project_coverages), 1) if project_coverages else 0
    with col4:
        color = IBM_GREEN if avg_cov >= 70 else IBM_ORANGE if avg_cov >= 40 else IBM_RED
        st.markdown(f"""<div class='kpi-card'>
            <h2 style='color:{color}'>{avg_cov}%</h2><p>Avg Skill Coverage</p></div>""",
            unsafe_allow_html=True)

    st.markdown("### Project Skill Coverage")
    st.caption("Red bars indicate critical bottlenecks — insufficient qualified workforce available.")

    if project_coverages:
        df_cov = pd.DataFrame(project_coverages).sort_values("Coverage %")
        colors = [IBM_RED if c < 40 else IBM_ORANGE if c < 70 else IBM_GREEN
                  for c in df_cov["Coverage %"]]
        fig = go.Figure(go.Bar(
            x=df_cov["Coverage %"],
            y=df_cov["Project"],
            orientation="h",
            marker_color=colors,
            text=[f"{c}%" for c in df_cov["Coverage %"]],
            textposition="outside",
        ))
        fig.update_layout(
            xaxis_title="Skill Coverage (%)", xaxis_range=[0, 110],
            height=300, margin=dict(l=10, r=40, t=20, b=20),
            plot_bgcolor="white", paper_bgcolor="white",
        )
        fig.add_vline(x=70, line_dash="dash", line_color=IBM_GRAY, annotation_text="70% target")
        st.plotly_chart(fig, use_container_width=True)

    # Project table
    st.markdown("### Project Overview")
    priority_label = {1: "🔴 High", 2: "🟡 Medium", 3: "🟢 Low"}
    rows = []
    for p, cov in zip(projects, project_coverages):
        rows.append({
            "Project": p["name"],
            "Deadline (days)": p["deadline_days"],
            "Priority": priority_label.get(p["priority"], str(p["priority"])),
            "Coverage %": cov["Coverage %"],
            "Status": p["status"],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    footer()


# ═════════════════════════════════════════════════════════════════════════════
# PAGE 2 — Workforce Map
# ═════════════════════════════════════════════════════════════════════════════

elif page == "👥 Workforce Map":
    st.title("👥 Workforce Capability Map")
    st.caption("Employee skills heatmap — proficiency 1 (aware) → 5 (expert)")

    employees = fetch_employees()
    if not employees:
        st.warning("No employee data found.")
        footer()
        st.stop()

    # Build skill matrix
    all_skills = set()
    for e in employees:
        for s in e.get("skills", []):
            all_skills.add(s["name"])
    all_skills = sorted(all_skills)

    matrix = []
    emp_names = []
    overloaded = []
    for e in employees:
        emp_names.append(e["name"])
        skill_map = {s["name"]: s["proficiency"] for s in e.get("skills", [])}
        row = [skill_map.get(skill, 0) for skill in all_skills]
        matrix.append(row)
        spare = e["availability_hours_per_week"] - e["allocated_hours"]
        overloaded.append(spare <= 5)

    df_matrix = pd.DataFrame(matrix, index=emp_names, columns=all_skills)

    fig = px.imshow(
        df_matrix,
        color_continuous_scale=["#f4f4f4", "#d0e2ff", "#0062FF", "#002d9c"],
        zmin=0, zmax=5,
        aspect="auto",
        labels={"color": "Proficiency"},
    )
    fig.update_layout(
        height=550, margin=dict(l=10, r=10, t=30, b=10),
        coloraxis_colorbar=dict(
            tickvals=[0,1,2,3,4,5],
            ticktext=["–","Aware","Beginner","Competent","Proficient","Expert"],
        ),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Overloaded employees
    overloaded_emps = [e for e in employees if (e["availability_hours_per_week"] - e["allocated_hours"]) <= 5]
    if overloaded_emps:
        st.warning(f"⚠️ **{len(overloaded_emps)} employees are near full capacity** (≤5 spare hrs/week):")
        cols = st.columns(min(len(overloaded_emps), 4))
        for i, emp in enumerate(overloaded_emps):
            with cols[i % 4]:
                spare = emp["availability_hours_per_week"] - emp["allocated_hours"]
                st.metric(emp["name"], f"{spare} hrs spare", delta=f"{emp['department']}")

    st.markdown("### Employee Details")
    rows = []
    for e in employees:
        spare = e["availability_hours_per_week"] - e["allocated_hours"]
        top_skills = sorted(e.get("skills",[]), key=lambda s: s["proficiency"], reverse=True)[:3]
        rows.append({
            "Name": e["name"],
            "Department": e["department"],
            "Role": e["role"],
            "Spare hrs/wk": spare,
            "Status": "🔴 Overloaded" if spare <= 5 else "🟡 Near capacity" if spare <= 15 else "🟢 Available",
            "Top Skills": ", ".join(f"{s['name']} (L{s['proficiency']})" for s in top_skills),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    footer()


# ═════════════════════════════════════════════════════════════════════════════
# PAGE 3 — Skill Gap Analysis
# ═════════════════════════════════════════════════════════════════════════════

elif page == "🔍 Skill Gap Analysis":
    st.title("🔍 Skill Gap Analysis")
    st.caption("Select a project to detect critical skill bottlenecks before they delay delivery.")

    projects = fetch_projects()
    if not projects:
        footer()
        st.stop()

    proj_map = {p["name"]: p for p in projects}
    selected_name = st.selectbox("Select Project", list(proj_map.keys()))
    proj = proj_map[selected_name]

    col1, col2, col3 = st.columns(3)
    priority_label = {1: "🔴 High", 2: "🟡 Medium", 3: "🟢 Low"}
    col1.metric("Priority", priority_label.get(proj["priority"], "-"))
    col2.metric("Deadline", f"{proj['deadline_days']} days")
    col3.metric("Status", proj["status"].capitalize())

    if st.button("🔍 Detect Skill Gaps", type="primary"):
        with st.spinner("Analyzing workforce capability against project requirements..."):
            try:
                gap_data = fetch_gaps(proj["id"])
                st.session_state["gap_data"] = gap_data
            except Exception as e:
                st.error(f"Gap detection failed: {e}")
                st.stop()

    if "gap_data" in st.session_state:
        gap_data = st.session_state["gap_data"]
        gaps = gap_data.get("gaps", [])

        col1, col2, col3 = st.columns(3)
        col1.metric("Overall Coverage", f"{gap_data.get('overall_coverage_pct',0)}%")
        col2.metric("Critical Gaps", gap_data.get("critical_count", 0), delta_color="inverse")
        col3.metric("Moderate Gaps", gap_data.get("moderate_count", 0), delta_color="inverse")

        st.markdown("### Gap Details")
        for g in gaps:
            sev   = g["gap_severity"]
            color = SEVERITY_COLOR.get(sev, IBM_GRAY)
            badge = f"<span class='{sev}-badge'>{sev.upper()}</span>" if sev in ("critical","moderate") else f"<span class='ok-badge'>{sev.upper()}</span>"

            with st.expander(f"{badge} &nbsp; **{g['skill_name']}** — {g['available_headcount']}/{g['required_headcount']} available", expanded=(sev=="critical")):
                st.markdown(badge, unsafe_allow_html=True)
                st.progress(min(1.0, g["coverage_pct"] / 100))
                st.caption(f"Coverage: {g['coverage_pct']}%  |  Required proficiency: Level {g['required_proficiency']}")
                st.info(g["recommendation"])

                if g["qualified_employees"]:
                    st.markdown("**Qualified employees:**")
                    qdf = pd.DataFrame(g["qualified_employees"])[["name","proficiency","verified","spare_hours"]]
                    qdf.columns = ["Name","Proficiency","Verified","Spare hrs/wk"]
                    st.dataframe(qdf, use_container_width=True, hide_index=True)
                else:
                    st.warning("No employees currently qualified for this skill at the required level.")

    footer()


# ═════════════════════════════════════════════════════════════════════════════
# PAGE 4 — Learning Path Generator
# ═════════════════════════════════════════════════════════════════════════════

elif page == "📚 Learning Path":
    st.title("📚 Personalized Learning Path Generator")
    st.caption("Generate the minimum targeted learning plan to close a specific skill gap.")

    employees = fetch_employees()
    projects  = fetch_projects()

    if not employees or not projects:
        footer()
        st.stop()

    col1, col2 = st.columns(2)
    with col1:
        emp_map  = {e["name"]: e for e in employees}
        emp_name = st.selectbox("Select Employee", list(emp_map.keys()))
        emp      = emp_map[emp_name]

        # Show current skills
        if emp.get("skills"):
            skill_df = pd.DataFrame(emp["skills"])
            skill_df["Level Label"] = skill_df["proficiency"].map(
                {1:"Aware",2:"Beginner",3:"Competent",4:"Proficient",5:"Expert"}
            )
            st.caption("Current skill profile:")
            st.dataframe(skill_df[["name","proficiency","Level Label","verified"]].rename(
                columns={"name":"Skill","proficiency":"Level","verified":"Verified"}),
                use_container_width=True, hide_index=True, height=180)

    with col2:
        SKILL_LIST = sorted(set(
            s["name"] for e in employees for s in e.get("skills", [])
        ))
        skill_name = st.selectbox("Skill to develop", SKILL_LIST)
        target_lv  = st.slider("Target proficiency level", 2, 5, 4,
                               help="1=Aware, 2=Beginner, 3=Competent, 4=Proficient, 5=Expert")

        proj_map   = {p["name"]: p for p in projects}
        proj_sel   = st.selectbox("For project (sets deadline)", list(proj_map.keys()))
        deadline   = proj_map[proj_sel]["deadline_days"]
        st.caption(f"Project deadline: **{deadline} days**")

    if st.button("🎯 Generate Learning Path", type="primary"):
        with st.spinner("Building personalized learning path..."):
            try:
                path = fetch_learning_path(emp["id"], skill_name, target_lv, deadline)
                st.session_state["lp"] = path
            except Exception as e:
                st.error(f"Failed: {e}")
                st.stop()

    if "lp" in st.session_state:
        path = st.session_state["lp"]

        if not path.get("modules"):
            st.success(path.get("explanation", "Already at target level."))
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Modules", len(path["modules"]))
            col2.metric("Estimated Days", path["estimated_days"])
            feasible = path["feasible_in_days"] <= deadline
            col3.metric(
                "Feasibility",
                "✅ Feasible" if feasible else "⚠️ Tight",
                delta=f"{deadline - path['feasible_in_days']} days buffer" if feasible else "Over deadline",
                delta_color="normal" if feasible else "inverse",
            )

            st.info(path["explanation"])

            st.markdown("### Learning Modules")
            type_icon = {"video": "🎬", "lab": "🧪", "assessment": "✅", "reading": "📖"}
            for i, m in enumerate(path["modules"]):
                icon = type_icon.get(m["type"], "📌")
                with st.expander(f"{icon} Module {m['order']}: {m['title']} ({m['duration_hours']}h)"):
                    col1, col2 = st.columns(2)
                    col1.write(f"**Type:** {m['type'].capitalize()}")
                    col1.write(f"**Duration:** {m['duration_hours']} hours")
                    col2.write(f"**Prerequisite:** {m['prerequisite'] or 'None'}")

            # Timeline visual
            st.markdown("### Study Timeline")
            hours_per_day = 2
            cumulative_days = 0
            timeline_rows = []
            for m in path["modules"]:
                start = cumulative_days
                duration_days = m["duration_hours"] / hours_per_day
                cumulative_days += duration_days
                timeline_rows.append({
                    "Module": m["title"][:40],
                    "Start": start,
                    "End": cumulative_days,
                    "Type": m["type"],
                })
            df_t = pd.DataFrame(timeline_rows)
            color_map = {"video": IBM_BLUE, "lab": IBM_GREEN, "assessment": IBM_RED, "reading": IBM_ORANGE}
            fig = go.Figure()
            for _, row in df_t.iterrows():
                fig.add_trace(go.Bar(
                    x=[row["End"] - row["Start"]],
                    y=[row["Module"]],
                    orientation="h",
                    base=row["Start"],
                    marker_color=color_map.get(row["Type"], IBM_GRAY),
                    name=row["Type"],
                    showlegend=False,
                ))
            fig.add_vline(x=deadline, line_dash="dash", line_color=IBM_RED,
                          annotation_text=f"Deadline: {deadline}d")
            fig.update_layout(
                xaxis_title="Days", height=300,
                margin=dict(l=10, r=60, t=20, b=20),
                plot_bgcolor="white", paper_bgcolor="white",
            )
            st.plotly_chart(fig, use_container_width=True)
    footer()


# ═════════════════════════════════════════════════════════════════════════════
# PAGE 5 — Allocation Engine
# ═════════════════════════════════════════════════════════════════════════════

elif page == "⚙️  Allocation Engine":
    st.title("⚙️ Workforce Allocation Engine")
    st.caption("Optimal project staffing using constraint optimization — powered by Google OR-Tools on IBM LinuxONE.")

    st.info(
        "The optimizer maximizes skill coverage across all projects simultaneously, "
        "respecting each employee's workload capacity and project deadlines. "
        "Compare against the naive baseline (assign by availability only)."
    )

    if st.button("🚀 Run Optimal Allocation", type="primary"):
        with st.spinner("Running OR-Tools CP-SAT optimizer on LinuxONE..."):
            try:
                result = fetch_allocation()
                st.session_state["allocation"] = result
            except Exception as e:
                st.error(f"Allocation failed: {e}")
                st.stop()

    if "allocation" in st.session_state:
        result = st.session_state["allocation"]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Optimal Score", f"{result['overall_score']}%")
        col2.metric("Baseline Score", f"{result['baseline_score']}%")
        improvement = result["improvement_pct"]
        col3.metric("Improvement", f"+{improvement}%",
                    delta=f"{improvement}% better than random assignment",
                    delta_color="normal")
        col4.metric("Solver", result["solver_used"])

        st.markdown("### Project Coverage")
        cov_data = [
            {"Project ID": k, "Coverage %": v}
            for k, v in result["project_coverage"].items()
        ]
        if cov_data:
            projects = fetch_projects()
            proj_id_to_name = {str(p["id"]): p["name"][:35] for p in projects}
            df_cov = pd.DataFrame(cov_data)
            df_cov["Project"] = df_cov["Project ID"].map(proj_id_to_name).fillna(df_cov["Project ID"])
            colors = [IBM_GREEN if c >= 70 else IBM_ORANGE if c >= 40 else IBM_RED
                      for c in df_cov["Coverage %"]]
            fig = px.bar(df_cov, x="Project", y="Coverage %", color="Coverage %",
                         color_continuous_scale=["red","orange","green"],
                         range_y=[0,105], text="Coverage %")
            fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            fig.update_layout(height=320, showlegend=False,
                              plot_bgcolor="white", paper_bgcolor="white")
            fig.add_hline(y=70, line_dash="dash", line_color=IBM_GRAY,
                          annotation_text="70% coverage target")
            st.plotly_chart(fig, use_container_width=True)

        if result.get("unmet_gaps"):
            st.error(f"⚠️ Projects below 50% coverage: {', '.join(result['unmet_gaps'])}")

        st.markdown("### Assignment Details")
        if result["assignments"]:
            df = pd.DataFrame(result["assignments"])
            df["Skill Match"] = (df["skill_match_score"] * 100).round(1).astype(str) + "%"
            display_cols = ["employee_name","project_name","assigned_hours","Skill Match"]
            st.dataframe(
                df[display_cols].rename(columns={
                    "employee_name":"Employee",
                    "project_name":"Project",
                    "assigned_hours":"Hours/wk",
                }),
                use_container_width=True, hide_index=True,
            )

            with st.expander("View AI Rationale for each assignment"):
                for _, row in df.iterrows():
                    st.markdown(f"**{row['employee_name']} → {row['project_name']}**")
                    st.caption(row["rationale"])
                    st.markdown("---")
        else:
            st.warning("No assignments generated — check that employees have spare capacity.")
    footer()


# ═════════════════════════════════════════════════════════════════════════════
# PAGE 6 — Deadline Simulation (WOW MOMENT)
# ═════════════════════════════════════════════════════════════════════════════

elif page == "⏱️  Deadline Simulation":
    st.title("⏱️ Deadline Change Simulation")
    st.markdown("""
    <div style='background:#fff8e1;border-left:4px solid #FF832B;padding:12px 16px;border-radius:4px;margin-bottom:16px;'>
    <b>🌟 Key Demo Feature</b> — Change a project deadline and watch the allocation engine
    instantly recalculate optimal staffing. When deadlines tighten, upskilling becomes infeasible
    and the system flags it immediately.
    </div>
    """, unsafe_allow_html=True)

    projects = fetch_projects()
    if not projects:
        footer()
        st.stop()

    st.markdown("### Adjust Project Deadlines")
    st.caption("Move the sliders to simulate urgency changes. Then run to see the impact on allocations.")

    deadline_changes = {}
    cols = st.columns(min(len(projects), 3))
    for i, proj in enumerate(projects):
        with cols[i % 3]:
            new_dl = st.slider(
                f"**{proj['name'][:25]}**",
                min_value=3,
                max_value=60,
                value=proj["deadline_days"],
                key=f"dl_{proj['id']}",
                help=f"Original: {proj['deadline_days']} days",
            )
            if new_dl != proj["deadline_days"]:
                deadline_changes[proj["id"]] = new_dl
                delta = new_dl - proj["deadline_days"]
                if delta < 0:
                    st.caption(f"🔴 Shortened by {abs(delta)} days")
                else:
                    st.caption(f"🟢 Extended by {delta} days")

    run_col1, run_col2 = st.columns([1, 3])
    with run_col1:
        simulate = st.button("⚡ Recalculate Allocations", type="primary",
                             disabled=not deadline_changes)
    with run_col2:
        if not deadline_changes:
            st.caption("ℹ️ Move at least one slider to activate simulation.")

    if simulate:
        with st.spinner("Re-running optimizer with updated deadlines on IBM LinuxONE..."):
            try:
                baseline_r = fetch_allocation()
                sim_r      = fetch_simulation(deadline_changes)
                st.session_state["sim_baseline"] = baseline_r
                st.session_state["sim_result"]   = sim_r
                st.session_state["sim_changes"]  = deadline_changes
            except Exception as e:
                st.error(f"Simulation failed: {e}")
                st.stop()

    if "sim_result" in st.session_state:
        baseline_r = st.session_state["sim_baseline"]
        sim_r      = st.session_state["sim_result"]
        changes    = st.session_state["sim_changes"]

        # Show changed deadlines
        st.markdown("### Deadline Changes Applied")
        changed_projects = {p["id"]: p for p in projects if p["id"] in changes}
        for pid, new_dl in changes.items():
            proj = changed_projects.get(pid)
            if proj:
                orig = proj["deadline_days"]
                diff = new_dl - orig
                icon = "🔴" if diff < 0 else "🟢"
                st.markdown(f"{icon} **{proj['name']}**: {orig} days → **{new_dl} days** ({'+' if diff>0 else ''}{diff}d)")

        # Coverage comparison
        st.markdown("### Before vs After Coverage")
        proj_id_to_name = {str(p["id"]): p["name"][:30] for p in projects}
        compare_rows = []
        for pid_str in baseline_r["project_coverage"]:
            before = baseline_r["project_coverage"].get(pid_str, 0)
            after  = sim_r["project_coverage"].get(pid_str, 0)
            compare_rows.append({
                "Project": proj_id_to_name.get(pid_str, pid_str),
                "Before (%)": before,
                "After (%)": after,
                "Change": round(after - before, 1),
                "Deadline Changed": int(pid_str) in changes,
            })

        df_cmp = pd.DataFrame(compare_rows)
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Before", x=df_cmp["Project"], y=df_cmp["Before (%)"],
                             marker_color=IBM_BLUE, opacity=0.7))
        fig.add_trace(go.Bar(name="After",  x=df_cmp["Project"], y=df_cmp["After (%)"],
                             marker_color=IBM_RED, opacity=0.9))
        fig.update_layout(
            barmode="group", height=350,
            yaxis_range=[0, 115],
            plot_bgcolor="white", paper_bgcolor="white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        fig.add_hline(y=70, line_dash="dash", line_color=IBM_GRAY)
        st.plotly_chart(fig, use_container_width=True)

        # Impact callouts
        st.markdown("### Impact Analysis")
        degraded = [r for r in compare_rows if r["Change"] < -5 and r["Deadline Changed"]]
        improved = [r for r in compare_rows if r["Change"] > 5]

        if degraded:
            for r in degraded:
                st.error(
                    f"⚠️ **{r['Project']}** — Coverage dropped {abs(r['Change'])}% due to tighter deadline. "
                    f"Upskilling no longer feasible. Recommend: assign qualified employee immediately or escalate."
                )
        if improved:
            for r in improved:
                st.success(f"✅ **{r['Project']}** — Coverage improved {r['Change']}% with extended timeline.")
        if not degraded and not improved:
            st.info("Coverage remained stable across all projects with these deadline adjustments.")

        # Assignment diff table
        st.markdown("### Assignment Comparison")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Before (original deadlines)**")
            if baseline_r["assignments"]:
                df_b = pd.DataFrame(baseline_r["assignments"])[["employee_name","project_name","assigned_hours"]]
                df_b.columns = ["Employee","Project","hrs"]
                st.dataframe(df_b, use_container_width=True, hide_index=True, height=300)
        with col2:
            st.markdown("**After (updated deadlines)**")
            if sim_r["assignments"]:
                df_s = pd.DataFrame(sim_r["assignments"])[["employee_name","project_name","assigned_hours"]]
                df_s.columns = ["Employee","Project","hrs"]
                st.dataframe(df_s, use_container_width=True, hide_index=True, height=300)

    footer()
