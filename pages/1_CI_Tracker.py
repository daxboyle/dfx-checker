import streamlit as st
import json
import os
import datetime

st.set_page_config(page_title="Continuous Improvement Tracker", page_icon="\U0001f4c8", layout="wide")
st.title("Continuous Improvement Tracker")

DATA_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY_FILE = os.path.join(DATA_DIR, "inspection_history.json")
CI_FILE = os.path.join(DATA_DIR, "ci_tracker.json")

PLATFORMS = ["Server Gen1", "Server Gen2", "Server Gen3", "Server Gen4", "Networking", "Storage", "Custom Silicon", "Other"]
VENDORS = ["Internal", "Vendor A", "Vendor B", "Vendor C", "Vendor D", "Other"]
CATEGORIES = ["Cable Management", "Thermal", "EMI/Shielding", "Mechanical/Structural", "Electrical", "Assembly Process", "Component Quality", "Fasteners", "Labeling", "Packaging", "Testing", "Other"]
SOURCES = ["Inspection Finding", "DFX Review", "Vendor Submission", "Customer Feedback", "Internal Audit", "SCAR", "Production Issue", "Other"]
STATUSES = ["Intake", "Assessment", "Approved", "In Progress", "Validation", "Closed", "Rejected"]


def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []


def load_ci():
    if os.path.exists(CI_FILE):
        with open(CI_FILE, "r") as f:
            return json.load(f)
    return {"cis": [], "lessons": []}


def save_ci(data):
    with open(CI_FILE, "w") as f:
        json.dump(data, f, indent=2)


def calc_priority_score(impact, effort):
    impact_map = {"Critical": 5, "High": 4, "Medium": 3, "Low": 2, "Minimal": 1}
    effort_map = {"Very High": 1, "High": 2, "Medium": 3, "Low": 4, "Minimal": 5}
    return impact_map.get(impact, 1) * effort_map.get(effort, 3)


def route_engineer_level(impact, effort):
    score = calc_priority_score(impact, effort)
    if score >= 20:
        return "L5-L6"
    elif score >= 12:
        return "L5"
    elif score >= 6:
        return "L4-L5"
    return "L4"


history = load_history()
ci_data = load_ci()

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Dashboard", "CI Intake", "CI Pipeline", "Impact Matrix", "Lessons Learned", "Trends"])

with tab1:
    st.subheader("Overview")
    cis = ci_data.get("cis", [])
    open_cis = [c for c in cis if c.get("status") not in ["Closed", "Rejected"]]
    closed_cis = [c for c in cis if c.get("status") == "Closed"]
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total CIs", len(cis))
    col2.metric("Open", len(open_cis))
    col3.metric("Closed", len(closed_cis))
    col4.metric("Inspections", len(history))
    if history:
        pass_rate = len([h for h in history if h.get("verdict") == "PASS"]) / len(history) * 100
        col5.metric("Pass Rate", str(round(pass_rate, 1)) + "%")
    if cis:
        st.subheader("Pipeline Summary")
        pipeline_cols = st.columns(len(STATUSES))
        for i, status in enumerate(STATUSES):
            count = len([c for c in cis if c.get("status") == status])
            pipeline_cols[i].metric(status, count)
        st.subheader("Recent CIs")
        for c in sorted(cis, key=lambda x: x.get("created", ""), reverse=True)[:5]:
            st.write("- **CI-" + str(c.get("id", "?")) + "** [" + c.get("status", "?") + "] " + c.get("title", "") + " | " + c.get("platform", "?") + " | " + c.get("vendor", "?"))

with tab2:
    st.subheader("Submit New Continuous Improvement")
    with st.form("ci_intake_form"):
        st.write("**Problem Description**")
        ci_title = st.text_input("CI Title:")
        ci_description = st.text_area("Detailed Description:", height=150)
        ci_category = st.selectbox("Category:", CATEGORIES)
        st.write("**Scope**")
        col_a, col_b = st.columns(2)
        with col_a:
            ci_platform = st.selectbox("Platform:", PLATFORMS)
            ci_generation = st.text_input("Generation/Revision:")
        with col_b:
            ci_vendor = st.selectbox("Vendor:", VENDORS)
            ci_source = st.selectbox("Source:", SOURCES)
        st.write("**Impact Assessment**")
        col_c, col_d = st.columns(2)
        with col_c:
            ci_impact = st.selectbox("Estimated Impact:", ["Critical", "High", "Medium", "Low", "Minimal"])
            ci_impact_areas = st.multiselect("Impact Areas:", ["FPY", "RTY", "Cycle Time", "Cost", "Safety", "Reliability", "Serviceability"])
        with col_d:
            ci_effort = st.selectbox("Estimated Effort:", ["Very High", "High", "Medium", "Low", "Minimal"])
            ci_cross_platform = st.checkbox("Applicable to other platforms?")
        ci_fpy = st.text_input("Estimated FPY/RTY impact (e.g. +2% FPY):")
        ci_cost = st.text_input("Estimated cost impact (e.g. -$5/unit):")
        st.write("**Submitter**")
        col_e, col_f = st.columns(2)
        with col_e:
            ci_submitter = st.text_input("Your name/alias:")
        with col_f:
            ci_role = st.selectbox("Role:", ["MFG Engineer", "Design Engineer", "Quality Engineer", "Vendor", "Supply Chain", "Other"])
        submitted = st.form_submit_button("Submit CI", type="primary")
        if submitted and ci_title:
            score = calc_priority_score(ci_impact, ci_effort)
            level = route_engineer_level(ci_impact, ci_effort)
            new_ci = {"id": len(ci_data.get("cis", [])) + 1, "title": ci_title, "description": ci_description,
                "category": ci_category, "platform": ci_platform, "generation": ci_generation,
                "vendor": ci_vendor, "source": ci_source, "impact": ci_impact, "effort": ci_effort,
                "impact_areas": ci_impact_areas, "cross_platform": ci_cross_platform,
                "fpy_impact": ci_fpy, "cost_impact": ci_cost, "submitter": ci_submitter,
                "submitter_role": ci_role, "priority_score": score, "recommended_level": level,
                "status": "Intake", "assigned_to": "", "created": datetime.datetime.now().isoformat(),
                "updated": datetime.datetime.now().isoformat(), "resolved": None, "outcome": "", "notes": []}
            if "cis" not in ci_data:
                ci_data["cis"] = []
            ci_data["cis"].append(new_ci)
            save_ci(ci_data)
            st.success("CI-" + str(new_ci["id"]) + " submitted! Priority: " + str(score) + " | Level: " + level)

with tab3:
    st.subheader("CI Pipeline")
    cis = ci_data.get("cis", [])
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        filt_status = st.selectbox("Status:", ["All"] + STATUSES, key="ps")
    with col_f2:
        filt_platform = st.selectbox("Platform:", ["All"] + PLATFORMS, key="pp")
    with col_f3:
        filt_vendor = st.selectbox("Vendor:", ["All"] + VENDORS, key="pv")
    filtered = cis
    if filt_status != "All":
        filtered = [c for c in filtered if c.get("status") == filt_status]
    if filt_platform != "All":
        filtered = [c for c in filtered if c.get("platform") == filt_platform]
    if filt_vendor != "All":
        filtered = [c for c in filtered if c.get("vendor") == filt_vendor]
    filtered = sorted(filtered, key=lambda x: x.get("priority_score", 0), reverse=True)
    st.write(str(len(filtered)) + " CIs shown")
    for ci in filtered:
        header = "CI-" + str(ci.get("id", "?")) + " [" + ci.get("status", "?") + "] " + ci.get("title", "")
        with st.expander(header):
            st.write("**Description:** " + ci.get("description", ""))
            col_d1, col_d2, col_d3 = st.columns(3)
            with col_d1:
                st.write("**Category:** " + ci.get("category", ""))
                st.write("**Platform:** " + ci.get("platform", ""))
                st.write("**Generation:** " + ci.get("generation", ""))
            with col_d2:
                st.write("**Vendor:** " + ci.get("vendor", ""))
                st.write("**Source:** " + ci.get("source", ""))
                st.write("**Submitter:** " + ci.get("submitter", ""))
            with col_d3:
                st.write("**Impact:** " + ci.get("impact", ""))
                st.write("**Effort:** " + ci.get("effort", ""))
                st.write("**Priority:** " + str(ci.get("priority_score", 0)))
                st.write("**Level:** " + ci.get("recommended_level", ""))
            new_status = st.selectbox("Status:", STATUSES, key="st_" + str(ci["id"]),
                index=STATUSES.index(ci.get("status", "Intake")) if ci.get("status") in STATUSES else 0)
            new_assignee = st.text_input("Assigned to:", value=ci.get("assigned_to", ""), key="as_" + str(ci["id"]))
            new_note = st.text_input("Add note:", key="nt_" + str(ci["id"]))
            outcome = st.text_area("Outcome:", value=ci.get("outcome", ""), key="oc_" + str(ci["id"]), height=68)
            if st.button("Update", key="up_" + str(ci["id"])):
                for c in ci_data["cis"]:
                    if c["id"] == ci["id"]:
                        c["status"] = new_status
                        c["assigned_to"] = new_assignee
                        c["outcome"] = outcome
                        c["updated"] = datetime.datetime.now().isoformat()
                        if new_status == "Closed":
                            c["resolved"] = datetime.datetime.now().isoformat()
                        if new_note:
                            c.setdefault("notes", []).append({"text": new_note, "date": datetime.datetime.now().isoformat()})
                save_ci(ci_data)
                st.success("Updated!")
                st.rerun()
            for n in ci.get("notes", []):
                st.write("- " + n.get("date", "")[:10] + ": " + n.get("text", ""))

with tab4:
    st.subheader("Impact vs Effort Matrix")
    cis = ci_data.get("cis", [])
    open_cis = [c for c in cis if c.get("status") not in ["Closed", "Rejected"]]
    if open_cis:
        import matplotlib.pyplot as plt
        impact_map = {"Critical": 5, "High": 4, "Medium": 3, "Low": 2, "Minimal": 1}
        effort_map = {"Very High": 5, "High": 4, "Medium": 3, "Low": 2, "Minimal": 1}
        fig, ax = plt.subplots(figsize=(10, 8))
        fig.patch.set_facecolor("#0e1117")
        ax.set_facecolor("#1a1a2e")
        ax.axhline(y=3, color="gray", linestyle="--", alpha=0.3)
        ax.axvline(x=3, color="gray", linestyle="--", alpha=0.3)
        ax.text(1.5, 4.5, "QUICK WINS", ha="center", va="center", color="#00ff41", fontsize=11, alpha=0.5)
        ax.text(4.5, 4.5, "MAJOR PROJECTS", ha="center", va="center", color="orange", fontsize=11, alpha=0.5)
        ax.text(1.5, 1.5, "FILL INS", ha="center", va="center", color="gray", fontsize=11, alpha=0.5)
        ax.text(4.5, 1.5, "RECONSIDER", ha="center", va="center", color="red", fontsize=11, alpha=0.5)
        for ci in open_cis:
            x = effort_map.get(ci.get("effort", "Medium"), 3)
            y = impact_map.get(ci.get("impact", "Medium"), 3)
            color = "#00ff41" if ci.get("priority_score", 0) >= 15 else "orange" if ci.get("priority_score", 0) >= 8 else "red"
            ax.scatter(x, y, c=color, s=200, zorder=5, edgecolors="white", linewidth=1)
            ax.annotate("CI-" + str(ci.get("id")), (x, y), color="white", fontsize=8, ha="center", va="bottom", xytext=(0, 10), textcoords="offset points")
        ax.set_xlabel("Effort", color="white", fontsize=12)
        ax.set_ylabel("Impact", color="white", fontsize=12)
        ax.set_xlim(0.5, 5.5)
        ax.set_ylim(0.5, 5.5)
        ax.set_xticks([1, 2, 3, 4, 5])
        ax.set_xticklabels(["Minimal", "Low", "Medium", "High", "Very High"], color="white")
        ax.set_yticks([1, 2, 3, 4, 5])
        ax.set_yticklabels(["Minimal", "Low", "Medium", "High", "Critical"], color="white")
        ax.tick_params(colors="white")
        st.pyplot(fig)
        st.subheader("Engineer Routing")
        for ci in sorted(open_cis, key=lambda x: x.get("priority_score", 0), reverse=True):
            st.write("- **CI-" + str(ci["id"]) + "** (Score: " + str(ci.get("priority_score", 0)) + ") -> **" + ci.get("recommended_level", "?") + "** | " + ci.get("title", ""))
    else:
        st.info("No open CIs. Submit CIs through the Intake tab.")

with tab5:
    st.subheader("Lessons Learned")
    with st.expander("Add Lesson", expanded=False):
        les_title = st.text_input("Title:", key="lt")
        les_detail = st.text_area("What happened and what we learned:", key="ld")
        les_cat = st.selectbox("Category:", CATEGORIES, key="lc")
        les_plat = st.selectbox("Platform:", PLATFORMS, key="lp")
        les_impact = st.selectbox("Impact:", ["High", "Medium", "Low"], key="li")
        les_cross = st.checkbox("Cross-platform?", key="lx")
        if st.button("Save Lesson"):
            if les_title:
                ci_data.setdefault("lessons", []).append({
                    "id": len(ci_data.get("lessons", [])) + 1, "title": les_title,
                    "detail": les_detail, "category": les_cat, "platform": les_plat,
                    "impact": les_impact, "cross_platform": les_cross,
                    "date": datetime.datetime.now().isoformat()})
                save_ci(ci_data)
                st.success("Saved!")
                st.rerun()
    search = st.text_input("Search lessons:", key="ls")
    lessons = ci_data.get("lessons", [])
    if search:
        lessons = [l for l in lessons if search.lower() in l.get("title", "").lower() or search.lower() in l.get("detail", "").lower()]
    for lesson in reversed(lessons):
        cross_tag = " | CROSS-PLATFORM" if lesson.get("cross_platform") else ""
        with st.expander("[" + lesson.get("category", "") + "] " + lesson.get("title", "") + cross_tag):
            st.write(lesson.get("detail", ""))
            st.write("**Impact:** " + lesson.get("impact", "") + " | **Platform:** " + lesson.get("platform", "") + " | **Date:** " + lesson.get("date", "")[:10])

with tab6:
    st.subheader("Trends")
    cis = ci_data.get("cis", [])
    if len(history) >= 2:
        import matplotlib.pyplot as plt
        scores = [h.get("score", 0) for h in history]
        defects = [h.get("defect_count", 0) for h in history]
        labels = [str(i+1) for i in range(len(history))]
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        fig.patch.set_facecolor("#0e1117")
        ax1.plot(labels, scores, "g-o", linewidth=2, markersize=8)
        ax1.axhline(y=80, color="orange", linestyle="--", label="Threshold")
        ax1.set_ylabel("Score %", color="white")
        ax1.set_title("Inspection Scores", color="white")
        ax1.set_facecolor("#1a1a2e")
        ax1.tick_params(colors="white")
        ax1.legend(facecolor="#1a1a2e", edgecolor="white", labelcolor="white")
        ax1.set_ylim(0, 105)
        colors_list = ["red" if d > 0 else "green" for d in defects]
        ax2.bar(labels, defects, color=colors_list)
        ax2.set_ylabel("Defects", color="white")
        ax2.set_xlabel("Inspection #", color="white")
        ax2.set_title("Defects Per Inspection", color="white")
        ax2.set_facecolor("#1a1a2e")
        ax2.tick_params(colors="white")
        plt.tight_layout()
        st.pyplot(fig)
    if cis:
        st.subheader("CI Metrics")
        cat_counts = {}
        for c in cis:
            cat = c.get("category", "Other")
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
        st.write("**By Category:**")
        for cat, count in sorted(cat_counts.items(), key=lambda x: x[1], reverse=True):
            st.write("- " + cat + ": " + str(count))
        vendor_counts = {}
        for c in cis:
            v = c.get("vendor", "Unknown")
            vendor_counts[v] = vendor_counts.get(v, 0) + 1
        st.write("**By Vendor:**")
        for v, count in sorted(vendor_counts.items(), key=lambda x: x[1], reverse=True):
            st.write("- " + v + ": " + str(count))
        closed = [c for c in cis if c.get("resolved")]
        if closed:
            cycle_times = []
            for c in closed:
                try:
                    ct = (datetime.datetime.fromisoformat(c["resolved"]) - datetime.datetime.fromisoformat(c["created"])).days
                    cycle_times.append(ct)
                except Exception:
                    pass
            if cycle_times:
                st.write("**Avg Cycle Time:** " + str(round(sum(cycle_times)/len(cycle_times), 1)) + " days")
    if not history and not cis:
        st.info("No data yet. Run inspections and submit CIs to see trends.")
