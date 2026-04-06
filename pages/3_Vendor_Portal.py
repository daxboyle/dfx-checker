import streamlit as st
import json
import os
import datetime

st.set_page_config(page_title="Vendor Portal", page_icon="\U0001f4e6", layout="wide")
st.title("Vendor CI Submission Portal")
st.write("Submit continuous improvement opportunities, quality issues, or process suggestions.")

DATA_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CI_FILE = os.path.join(DATA_DIR, "ci_tracker.json")

def load_ci():
    if os.path.exists(CI_FILE):
        with open(CI_FILE, "r") as f:
            return json.load(f)
    return {"cis": [], "lessons": []}

def save_ci(data):
    with open(CI_FILE, "w") as f:
        json.dump(data, f, indent=2)

CATEGORIES = ["Cable Management", "Thermal", "EMI/Shielding", "Mechanical/Structural", "Electrical", "Assembly Process", "Component Quality", "Fasteners", "Labeling", "Packaging", "Testing", "Other"]
PLATFORMS = ["Server Gen1", "Server Gen2", "Server Gen3", "Server Gen4", "Networking", "Storage", "Custom Silicon", "Other"]

tab1, tab2 = st.tabs(["Submit CI", "My Submissions"])

with tab1:
    st.subheader("Submit a Continuous Improvement")
    with st.form("vendor_ci_form"):
        st.write("**Your Information**")
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            vendor_name = st.text_input("Company name:")
            contact_name = st.text_input("Your name:")
        with col_v2:
            contact_email = st.text_input("Email:")
            contact_phone = st.text_input("Phone (optional):")

        st.write("**Issue Details**")
        ci_title = st.text_input("Title (brief description of the issue or improvement):")
        ci_description = st.text_area("Detailed description:", height=200, placeholder="Describe the issue, when it occurs, how often, and any suggested fix...")
        ci_category = st.selectbox("Category:", CATEGORIES)

        col_v3, col_v4 = st.columns(2)
        with col_v3:
            ci_platform = st.selectbox("Affected platform:", PLATFORMS)
            ci_generation = st.text_input("Generation/Revision (if known):")
        with col_v4:
            ci_severity = st.selectbox("How critical is this?", ["Critical - stops production", "High - workaround exists but impacts quality", "Medium - improvement opportunity", "Low - nice to have"])
            ci_frequency = st.selectbox("How often does this occur?", ["Every unit", "Frequently (>25%)", "Sometimes (5-25%)", "Rarely (<5%)", "One-time occurrence"])

        st.write("**Additional Context**")
        ci_root_cause = st.text_area("Suspected root cause (if known):", height=100)
        ci_suggested_fix = st.text_area("Suggested fix or improvement:", height=100)
        ci_affects_other = st.checkbox("This may affect other platforms or products")
        st.write("**Attach Photos**")
        uploaded_images = st.file_uploader("Upload photos of the issue (optional)", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="vendor_imgs")

        submitted = st.form_submit_button("Submit CI", type="primary")

        if submitted and ci_title and vendor_name:
            ci_data = load_ci()
            severity_map = {"Critical - stops production": "Critical", "High - workaround exists but impacts quality": "High", "Medium - improvement opportunity": "Medium", "Low - nice to have": "Low"}
            impact = severity_map.get(ci_severity, "Medium")
            effort_map = {"Critical - stops production": "High", "High - workaround exists but impacts quality": "Medium", "Medium - improvement opportunity": "Low", "Low - nice to have": "Minimal"}
            effort = effort_map.get(ci_severity, "Medium")
            impact_val = {"Critical": 5, "High": 4, "Medium": 3, "Low": 2, "Minimal": 1}
            effort_val = {"Very High": 1, "High": 2, "Medium": 3, "Low": 4, "Minimal": 5}
            score = impact_val.get(impact, 3) * effort_val.get(effort, 3)

            new_ci = {
                "id": len(ci_data.get("cis", [])) + 1,
                "title": ci_title,
                "description": ci_description + "\n\nRoot Cause: " + ci_root_cause + "\n\nSuggested Fix: " + ci_suggested_fix + "\n\nFrequency: " + ci_frequency,
                "category": ci_category,
                "platform": ci_platform,
                "generation": ci_generation,
                "vendor": vendor_name,
                "source": "Vendor Submission",
                "impact": impact,
                "effort": effort,
                "impact_areas": [],
                "cross_platform": ci_affects_other,
                "fpy_impact": "",
                "cost_impact": "",
                "submitter": contact_name + " (" + contact_email + ")",
                "submitter_role": "Vendor",
                "priority_score": score,
                "recommended_level": "L5" if score >= 12 else "L4-L5" if score >= 6 else "L4",
                "status": "Intake",
                "assigned_to": "",
                "created": datetime.datetime.now().isoformat(),
                "updated": datetime.datetime.now().isoformat(),
                "resolved": None,
                "outcome": "",
                "notes": [],
            }
            if uploaded_images:
                img_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ci_uploads", "CI-" + str(new_ci["id"]))
                os.makedirs(img_dir, exist_ok=True)
                saved_imgs = []
                for img in uploaded_images:
                    img_path = os.path.join(img_dir, img.name)
                    with open(img_path, "wb") as imgf:
                        imgf.write(img.read())
                    saved_imgs.append(img.name)
                new_ci["attachments"] = saved_imgs
            ci_data.setdefault("cis", []).append(new_ci)
            save_ci(ci_data)
            st.success("Thank you! Your CI has been submitted as CI-" + str(new_ci["id"]) + ". You will be contacted at " + contact_email + " with updates.")
            st.balloons()

with tab2:
    st.subheader("Track Your Submissions")
    vendor_search = st.text_input("Enter your company name to find your submissions:")
    if vendor_search:
        ci_data = load_ci()
        vendor_cis = [c for c in ci_data.get("cis", []) if vendor_search.lower() in c.get("vendor", "").lower()]
        if vendor_cis:
            st.write("Found " + str(len(vendor_cis)) + " submission(s):")
            for c in sorted(vendor_cis, key=lambda x: x.get('created', ''), reverse=True):
                status_color = "green" if c.get("status") == "Closed" else "orange" if c.get("status") in ["In Progress", "Validation"] else "blue"
                with st.expander("CI-" + str(c.get("id", "?")) + " [" + c.get("status", "?") + "] " + c.get("title", "")):
                    st.write("**Status:** " + c.get("status", "Unknown"))
                    st.write("**Category:** " + c.get("category", ""))
                    st.write("**Platform:** " + c.get("platform", ""))
                    st.write("**Submitted:** " + c.get("created", "")[:10])
                    if c.get("assigned_to"):
                        st.write("**Assigned to:** " + c.get("assigned_to", ""))
                    if c.get("outcome"):
                        st.write("**Outcome:** " + c.get("outcome", ""))
                    for n in c.get("notes", []):
                        st.write("- " + n.get("date", "")[:10] + ": " + n.get("text", ""))
        else:
            st.info("No submissions found for '" + vendor_search + "'. Check the company name spelling.")
