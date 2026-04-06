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

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(["Dashboard", "CI Intake", "CI Pipeline", "Impact Matrix", "Semantic Search", "Lessons Learned", "Trends", "Ticket Routing"])

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
        st.write("**Attachments**")
        ci_images = st.file_uploader("Upload photos or documents", type=["png", "jpg", "jpeg", "pdf"], accept_multiple_files=True, key="ci_imgs")
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
            if ci_images:
                img_dir = os.path.join(DATA_DIR, "ci_uploads", "CI-" + str(new_ci["id"]))
                os.makedirs(img_dir, exist_ok=True)
                saved_imgs = []
                for img in ci_images:
                    img_path = os.path.join(img_dir, img.name)
                    with open(img_path, "wb") as imgf:
                        imgf.write(img.read())
                    saved_imgs.append(img.name)
                new_ci["attachments"] = saved_imgs
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
            st.write("---")
            # Smart routing recommendation
            p_score = ci.get("priority_score", 0)
            ci_impact = ci.get("impact", "Medium")
            ci_effort = ci.get("effort", "Medium")
            if ci_impact in ["Critical", "High"] and ci_effort in ["Low", "Minimal"]:
                quadrant = "QUICK WIN"
                route_msg = "Quick win - vendor can likely implement. Cut a ticket to the vendor for corrective action."
                route_target = "Vendor"
            elif ci_impact in ["Critical", "High"] and ci_effort in ["High", "Very High"]:
                quadrant = "MAJOR PROJECT"
                route_msg = "Major project - likely needs design or engineering review. Cut a ticket to the design team."
                route_target = "Design Team"
            elif ci_impact in ["Low", "Minimal"] and ci_effort in ["Low", "Minimal"]:
                quadrant = "FILL IN"
                route_msg = "Fill-in work - low priority, assign to available L4/L5 engineer when bandwidth allows."
                route_target = "MFG Engineering"
            else:
                quadrant = "RECONSIDER"
                route_msg = "Reconsider - high effort, low impact. Discuss with team before committing resources."
                route_target = "Team Review"
            st.info("**" + quadrant + ":** " + route_msg)
            col_tk1, col_tk2, col_tk3 = st.columns(3)
            with col_tk1:
                if st.button("Generate Vendor Ticket", key="vt_" + str(ci["id"])):
                    vt = "Title: [CI-" + str(ci["id"]) + "] " + ci.get("title", "") + "\n\n"
                    vt += "Platform: " + ci.get("platform", "") + " " + ci.get("generation", "") + "\n"
                    vt += "Category: " + ci.get("category", "") + "\n"
                    vt += "Impact: " + ci.get("impact", "") + " | Effort: " + ci.get("effort", "") + "\n"
                    vt += "Priority Score: " + str(p_score) + " | Quadrant: " + quadrant + "\n\n"
                    vt += "Description:\n" + ci.get("description", "") + "\n\n"
                    vt += "Action Required: Please review and provide implementation plan with timeline."
                    st.text_area("Vendor ticket:", vt, height=200, key="vt_text_" + str(ci["id"]))
            with col_tk2:
                if st.button("Generate Design Ticket", key="dt_" + str(ci["id"])):
                    dt = "Title: [DESIGN REVIEW] CI-" + str(ci["id"]) + " - " + ci.get("title", "") + "\n\n"
                    dt += "Platform: " + ci.get("platform", "") + " " + ci.get("generation", "") + "\n"
                    dt += "Category: " + ci.get("category", "") + "\n"
                    dt += "Impact: " + ci.get("impact", "") + " | Effort: " + ci.get("effort", "") + "\n"
                    dt += "Quadrant: " + quadrant + "\n\n"
                    dt += "Description:\n" + ci.get("description", "") + "\n\n"
                    dt += "Request: Evaluate feasibility and design changes required. Provide LOE estimate."
                    st.text_area("Design ticket:", dt, height=200, key="dt_text_" + str(ci["id"]))
            with col_tk3:
                if st.button("Generate Email", key="em_" + str(ci["id"])):
                    em = "Subject: CI-" + str(ci["id"]) + " - " + ci.get("title", "") + " [" + quadrant + "]\n\n"
                    em += "Team,\n\nA new CI has been assessed and routed to " + route_target + ":\n\n"
                    em += "CI-" + str(ci["id"]) + ": " + ci.get("title", "") + "\n"
                    em += "Platform: " + ci.get("platform", "") + " " + ci.get("generation", "") + "\n"
                    em += "Impact: " + ci.get("impact", "") + " | Effort: " + ci.get("effort", "") + "\n"
                    em += "Quadrant: " + quadrant + "\n\n"
                    em += ci.get("description", "") + "\n\n"
                    em += "Recommended action: " + route_msg + "\n\nRegards"
                    st.text_area("Email:", em, height=200, key="em_text_" + str(ci["id"]))
            st.write("---")
            ROUTING_FILE = os.path.join(DATA_DIR, "ticket_routing.json")
            if os.path.exists(ROUTING_FILE):
                with open(ROUTING_FILE, "r") as rf:
                    routing = json.load(rf)
                cat_routing = routing.get(ci.get("category", "Other"), {"resolver_group": "mfg-engineering", "default_severity": 3})
                st.info("**Auto-route:** " + ci.get("category", "") + " -> **" + cat_routing["resolver_group"] + "** (Sev-" + str(cat_routing["default_severity"]) + ")")
                all_groups = sorted(set([v["resolver_group"] for v in routing.values()]))
                all_groups.append("Other (type below)")
                default_idx = all_groups.index(cat_routing["resolver_group"]) if cat_routing["resolver_group"] in all_groups else 0
                override_col1, override_col2 = st.columns([2, 2])
                with override_col1:
                    selected_group = st.selectbox("Route to:", all_groups, index=default_idx, key="route_" + str(ci["id"]))
                with override_col2:
                    if selected_group == "Other (type below)":
                        selected_group = st.text_input("Custom resolver group:", key="custom_rg_" + str(ci["id"]))
                    override_sev = st.selectbox("Severity:", [1, 2, 3, 4, 5], index=cat_routing["default_severity"] - 1, key="osev_" + str(ci["id"]))
                cat_routing["resolver_group"] = selected_group
                cat_routing["default_severity"] = override_sev
                if st.button("Create T.Corp Ticket (Preview)", key="tcorp_" + str(ci["id"])):
                    tcorp_text = "=== T.CORP TICKET PREVIEW ===\n\n"
                    tcorp_text += "Title: [CI-" + str(ci["id"]) + "] " + ci.get("title", "") + "\n"
                    tcorp_text += "Resolver Group: " + cat_routing["resolver_group"] + "\n"
                    tcorp_text += "Severity: " + str(cat_routing["default_severity"]) + "\n"
                    tcorp_text += "Category: " + ci.get("category", "") + "\n"
                    tcorp_text += "Platform: " + ci.get("platform", "") + " " + ci.get("generation", "") + "\n"
                    tcorp_text += "Vendor: " + ci.get("vendor", "") + "\n"
                    tcorp_text += "Impact: " + ci.get("impact", "") + " | Effort: " + ci.get("effort", "") + "\n"
                    tcorp_text += "Priority Score: " + str(ci.get("priority_score", 0)) + "\n\n"
                    tcorp_text += "Description:\n" + ci.get("description", "") + "\n\n"
                    tcorp_text += "Recommended Action: " + route_msg + "\n"
                    tcorp_text += "\n(Once Tickety API is onboarded, this will auto-create the ticket)"
                    st.text_area("T.Corp ticket preview:", tcorp_text, height=300, key="tcorp_text_" + str(ci["id"]))
                    st.write("Link: [Create manually](https://t.corp.amazon.com/create)")
            if ci.get("attachments"):
                st.write("**Attachments:**")
                img_dir = os.path.join(DATA_DIR, "ci_uploads", "CI-" + str(ci["id"]))
                if os.path.exists(img_dir):
                    img_cols = st.columns(min(len(ci["attachments"]), 4))
                    for idx, img_name in enumerate(ci["attachments"]):
                        img_path = os.path.join(img_dir, img_name)
                        if os.path.exists(img_path) and img_name.lower().endswith((".png", ".jpg", ".jpeg")):
                            with img_cols[idx % 4]:
                                st.image(img_path, caption=img_name, width=200)
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

with tab7:
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


with tab5:
    st.subheader("Semantic Search - Have We Seen This Before?")
    st.write("Search across all CIs, lessons learned, and inspection history using natural language.")

    search_query = st.text_area("Describe the issue or question:", height=100, placeholder="e.g. thermal issues with cable routing near fans on Gen3 servers")

    if st.button("Search", type="primary") and search_query:
        import boto3
        with st.spinner("Searching across all data..."):
            all_cis = ci_data.get("cis", [])
            all_lessons = ci_data.get("lessons", [])

            ci_summaries = []
            for c in all_cis:
                summary = "CI-" + str(c.get("id", "")) + ": " + c.get("title", "") + " | "
                summary += "Category: " + c.get("category", "") + " | "
                summary += "Platform: " + c.get("platform", "") + " " + c.get("generation", "") + " | "
                summary += "Vendor: " + c.get("vendor", "") + " | "
                summary += "Status: " + c.get("status", "") + " | "
                summary += "Impact: " + c.get("impact", "") + " | "
                summary += "Description: " + c.get("description", "")[:200] + " | "
                summary += "Outcome: " + c.get("outcome", "")
                ci_summaries.append(summary)

            lesson_summaries = []
            for l in all_lessons:
                summary = "Lesson-" + str(l.get("id", "")) + ": " + l.get("title", "") + " | "
                summary += "Category: " + l.get("category", "") + " | "
                summary += "Platform: " + l.get("platform", "") + " | "
                summary += "Detail: " + l.get("detail", "")[:200]
                lesson_summaries.append(summary)

            inspection_summaries = []
            for h in history:
                summary = "Inspection: " + h.get("reference", "") + " vs " + h.get("production_file", "") + " | "
                summary += "Verdict: " + h.get("verdict", "") + " | "
                summary += "Score: " + str(h.get("score", 0)) + "% | "
                summary += "Defects: " + str(h.get("defect_count", 0))
                inspection_summaries.append(summary)

            all_data = "CONTINUOUS IMPROVEMENT RECORDS:\n"
            if ci_summaries:
                all_data += "\n".join(ci_summaries) + "\n\n"
            all_data += "LESSONS LEARNED:\n"
            if lesson_summaries:
                all_data += "\n".join(lesson_summaries) + "\n\n"
            all_data += "INSPECTION HISTORY:\n"
            if inspection_summaries:
                all_data += "\n".join(inspection_summaries)

            prompt = "You are a manufacturing knowledge search assistant.\n\n"
            prompt += "A user is searching for: " + search_query + "\n\n"
            prompt += "Here is all available data from our CI system:\n\n" + all_data + "\n\n"
            prompt += "INSTRUCTIONS:\n"
            prompt += "- Find ALL records that are relevant to the search query\n"
            prompt += "- Rank results by relevance\n"
            prompt += "- For each match, explain WHY it is relevant\n"
            prompt += "- Identify patterns across matches (e.g. same vendor, same platform, recurring issue)\n"
            prompt += "- Suggest cross-platform applicability if relevant\n"
            prompt += "- If nothing matches, say so clearly\n\n"
            prompt += "Format:\n## Matching Records\n(list each with relevance explanation)\n\n"
            prompt += "## Patterns Identified\n(recurring themes across matches)\n\n"
            prompt += "## Cross-Platform Applicability\n(could this apply to other platforms?)\n\n"
            prompt += "## Recommendation\n(what should the user do based on past data?)"

            client = boto3.client("bedrock-runtime", region_name="us-west-2")
            body_data = {"anthropic_version": "bedrock-2023-05-31", "max_tokens": 4000,
                "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}]}
            response = client.invoke_model(modelId="anthropic.claude-3-haiku-20240307-v1:0", body=json.dumps(body_data))
            result = json.loads(response["body"].read())
            answer = result["content"][0]["text"]

        st.markdown(answer)

    if not ci_data.get("cis") and not ci_data.get("lessons") and not history:
        st.info("No data to search yet. Submit CIs, lessons, and run inspections to build the knowledge base.")

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

with tab8:
    st.subheader("Ticket Routing Configuration")
    st.write("Configure which resolver group receives tickets for each CI category.")
    ROUTING_FILE = os.path.join(DATA_DIR, "ticket_routing.json")
    if os.path.exists(ROUTING_FILE):
        with open(ROUTING_FILE, "r") as rf:
            routing = json.load(rf)
    else:
        routing = {}
    st.subheader("Current Routing")
    updated = False
    for cat in ["Cable Management", "Thermal", "EMI/Shielding", "Mechanical/Structural", "Electrical", "Assembly Process", "Component Quality", "Fasteners", "Labeling", "Packaging", "Testing", "Other"]:
        col_r1, col_r2, col_r3 = st.columns([2, 3, 1])
        with col_r1:
            st.write("**" + cat + "**")
        with col_r2:
            current = routing.get(cat, {}).get("resolver_group", "mfg-engineering")
            new_rg = st.text_input("Resolver group:", value=current, key="rg_" + cat)
            if new_rg != current:
                routing.setdefault(cat, {})["resolver_group"] = new_rg
                updated = True
        with col_r3:
            current_sev = routing.get(cat, {}).get("default_severity", 3)
            new_sev = st.selectbox("Sev:", [1, 2, 3, 4, 5], index=[1,2,3,4,5].index(current_sev), key="sev_" + cat)
            if new_sev != current_sev:
                routing.setdefault(cat, {})["default_severity"] = new_sev
                updated = True
    if updated:
        with open(ROUTING_FILE, "w") as rf:
            json.dump(routing, rf, indent=2)
        st.success("Routing updated!")
        st.rerun()
