import streamlit as st
import ezdxf
import tempfile
import os
import math
import base64
import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


def clean_pdf(text):
   out = []
   for ch in text:
       if ord(ch) < 128:
           out.append(ch)
       else:
           out.append(" ")
   return "".join(out)


PROFILES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profiles.json")


def load_profiles():
   if os.path.exists(PROFILES_FILE):
       with open(PROFILES_FILE, "r") as f:
           return json.load(f)
   return {}


def save_profiles(profiles):
   with open(PROFILES_FILE, "w") as f:
       json.dump(profiles, f, indent=2)


st.title("DFX Design Checker")

st.sidebar.header("Configuration")
process = st.sidebar.selectbox("Manufacturing Process", [
   "CNC Machining",
   "Injection Molding",
   "Sheet Metal",
   "3D Printing (FDM)",
   "Server/Hardware Assembly",
])

RULES = {
   "CNC Machining": {
       "min_hole_radius": 0.5,
       "min_arc_radius": 0.5,
       "min_line_length": 0.5,
       "min_hole_spacing": 3.0,
       "min_wall_thickness": 0.8,
   },
   "Injection Molding": {
       "min_hole_radius": 0.4,
       "min_arc_radius": 0.25,
       "min_line_length": 0.3,
       "min_hole_spacing": 2.0,
       "min_wall_thickness": 0.8,
   },
   "Sheet Metal": {
       "min_hole_radius": 0.5,
       "min_arc_radius": 1.0,
       "min_line_length": 0.5,
       "min_hole_spacing": 4.0,
       "min_wall_thickness": 0.5,
   },
   "3D Printing (FDM)": {
       "min_hole_radius": 0.5,
       "min_arc_radius": 0.5,
       "min_line_length": 0.3,
       "min_hole_spacing": 2.0,
       "min_wall_thickness": 0.4,
   },
   "Server/Hardware Assembly": {
       "cable_routing": "Cables must follow designated channels, no crossing hot zones or fans",
       "cable_bend_radius": "Cable bend radius must not be too tight (min 4x cable diameter)",
       "emi_gaskets": "EMI gaskets must be present at all panel seams and joints",
       "grounding": "Grounding straps must be connected and visible",
       "shielding": "No gaps in shielding enclosure, conductive gaskets not damaged",
       "airflow": "Airflow path must not be obstructed by cables or components",
       "fan_placement": "Fans properly seated and oriented in correct direction",
       "thermal": "Hot components must have heatsinks, adequate spacing between heat sources",
       "connector_access": "All connectors and ports must be accessible for service",
       "fasteners": "All screws and fasteners present and correct type",
       "labeling": "Components and cables properly labeled",
       "tool_clearance": "Adequate clearance for tools during service and maintenance",
   },
}

rules = RULES[process]

st.sidebar.header("Active Rules")
if process == "Server/Hardware Assembly":
   for name, desc in rules.items():
       st.sidebar.write("**" + name + ":** " + desc)
else:
   st.sidebar.write("**Min hole radius:** " + str(rules["min_hole_radius"]) + "mm")
   st.sidebar.write("**Min arc radius:** " + str(rules["min_arc_radius"]) + "mm")
   st.sidebar.write("**Min line length:** " + str(rules["min_line_length"]) + "mm")
   st.sidebar.write("**Min hole spacing:** " + str(rules["min_hole_spacing"]) + "mm")
   st.sidebar.write("**Min wall thickness:** " + str(rules["min_wall_thickness"]) + "mm")

if process != "Server/Hardware Assembly":
   st.sidebar.header("Custom Overrides")
   rules["min_hole_radius"] = st.sidebar.number_input(
       "Override min hole radius (mm)", value=rules["min_hole_radius"], step=0.1
   )
   rules["min_wall_thickness"] = st.sidebar.number_input(
       "Override min wall thickness (mm)", value=rules["min_wall_thickness"], step=0.1
   )

# --- RULE PROFILES ---
if process != "Server/Hardware Assembly":
   st.sidebar.header("Rule Profiles")
   profiles = load_profiles()
   process_profiles = {k: v for k, v in profiles.items() if v.get("process") == process}

   profile_names = ["(Default)"] + list(process_profiles.keys())
   selected_profile = st.sidebar.selectbox("Load a saved profile:", profile_names)

   if selected_profile != "(Default)" and selected_profile in profiles:
       prof = profiles[selected_profile]
       for key in prof:
           if key != "process" and key in rules:
               rules[key] = prof[key]
       st.sidebar.success("Loaded: " + selected_profile)

   with st.sidebar.expander("Save Current Rules as Profile"):
       new_profile_name = st.text_input("Profile name (e.g. Vendor A - CNC):")
       if st.button("Save Profile"):
           if new_profile_name:
               profiles[new_profile_name] = dict(rules)
               profiles[new_profile_name]["process"] = process
               save_profiles(profiles)
               st.success("Saved: " + new_profile_name)
               st.rerun()
           else:
               st.warning("Enter a profile name first")

   if selected_profile != "(Default)":
       if st.sidebar.button("Delete: " + selected_profile):
           del profiles[selected_profile]
           save_profiles(profiles)
           st.sidebar.success("Deleted!")
           st.rerun()

st.write("Upload a file to check against **" + process + "** rules.")

if process == "Server/Hardware Assembly":
   upload_type = "Image"
   analysis_mode = st.radio("Analysis mode:", ["Single Image", "Compare Two Images"], horizontal=True)
   if analysis_mode == "Compare Two Images":
       col_a, col_b = st.columns(2)
       with col_a:
           st.write("**Image A (Reference/Baseline)**")
           uploaded_file_a = st.file_uploader("Upload Image A", type=["png", "jpg", "jpeg", "webp", "gif"], key="img_a")
       with col_b:
           st.write("**Image B (Current/Production)**")
           uploaded_file_b = st.file_uploader("Upload Image B", type=["png", "jpg", "jpeg", "webp", "gif"], key="img_b")
   else:
       uploaded_file_a = None
       uploaded_file_b = None
   uploaded_file = None if analysis_mode == "Compare Two Images" else st.file_uploader("Choose an image of the server/hardware", type=["png", "jpg", "jpeg", "webp", "gif"])
else:
   upload_type = st.radio("File type:", ["DXF Drawing", "STEP File (3D)", "PDF Drawing", "Image"], horizontal=True)
   if upload_type == "DXF Drawing":
       uploaded_file = st.file_uploader("Choose a .dxf file", type=["dxf"])
   elif upload_type == "STEP File (3D)":
       uploaded_file = st.file_uploader("Choose a .step or .stp file", type=["step", "stp"])
   elif upload_type == "PDF Drawing":
       uploaded_file = st.file_uploader("Choose a .pdf file", type=["pdf"])
   else:
       uploaded_file = st.file_uploader("Choose an image", type=["png", "jpg", "jpeg", "webp", "gif"])
if process == "Server/Hardware Assembly" and analysis_mode == "Compare Two Images" and uploaded_file_a is not None and uploaded_file_b is not None:
   import boto3
   from PIL import Image as PILImage

   col_show_a, col_show_b = st.columns(2)
   with col_show_a:
       st.image(uploaded_file_a, caption="Image A (Reference)", use_container_width=True)
   with col_show_b:
       st.image(uploaded_file_b, caption="Image B (Current)", use_container_width=True)

   uploaded_file_a.seek(0)
   uploaded_file_b.seek(0)

   with st.spinner("Comparing images with AI..."):
       img_a_bytes = uploaded_file_a.read()
       img_b_bytes = uploaded_file_b.read()
       img_a_b64 = base64.b64encode(img_a_bytes).decode()
       img_b_b64 = base64.b64encode(img_b_bytes).decode()

       ext_a = uploaded_file_a.name.split(".")[-1].lower()
       ext_b = uploaded_file_b.name.split(".")[-1].lower()
       media_types = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp", "gif": "image/gif"}
       media_a = media_types.get(ext_a, "image/png")
       media_b = media_types.get(ext_b, "image/png")

       rules_text = "\n".join(["- " + k + ": " + str(v) for k, v in rules.items()])

       compare_prompt = "You are a strict, detail-oriented hardware design engineer performing a formal comparison inspection.\n\n"
       compare_prompt += "CRITICAL RULES FOR COMPARISON:\n"
       compare_prompt += "- If the two images appear identical or nearly identical, explicitly state that and do not fabricate differences\n"
       compare_prompt += "- Only report differences you can clearly see - do not speculate\n"
       compare_prompt += "- Minor lighting or angle differences between photos are NOT design differences - ignore them\n"
       compare_prompt += "- Focus on structural, component, and assembly differences only\n"
       compare_prompt += "- Score both images independently using: (PASS count) / (PASS + FAIL + WARN count) * 100\n\n"
       compare_prompt += "\nImage A is the REFERENCE/BASELINE (the standard to compare against).\n"
       compare_prompt += "Image B is the CURRENT/PRODUCTION unit being inspected.\n\n"
       compare_prompt += "Check both against these rules:\n" + rules_text + "\n\n"
       compare_prompt += "Provide your analysis in this format:\n\n"
       compare_prompt += "## Overview\n(What you see in each image)\n\n"
       compare_prompt += "## Differences Found\n(List every difference between A and B, with location descriptions)\n\n"
       compare_prompt += "## Rule Comparison\n(For each rule, which image is better and why)\n\n"
       compare_prompt += "## Issues in Image B Not Present in Image A\n(Defects, missing components, misalignments)\n\n"
       compare_prompt += "## Score\n- Image A score: X%\n- Image B score: X%\n\n"
       compare_prompt += "## Recommendations\n(What needs to be fixed in Image B to match Image A)"

       client = boto3.client("bedrock-runtime", region_name="us-west-2")
       body_data = {
           "anthropic_version": "bedrock-2023-05-31",
           "max_tokens": 4000,
           "messages": [{
               "role": "user",
               "content": [
                   {"type": "text", "text": "Image A (Reference):"},
                   {"type": "image", "source": {"type": "base64", "media_type": media_a, "data": img_a_b64}},
                   {"type": "text", "text": "Image B (Current/Production):"},
                   {"type": "image", "source": {"type": "base64", "media_type": media_b, "data": img_b_b64}},
                   {"type": "text", "text": compare_prompt}
               ]
           }]
       }
       response = client.invoke_model(modelId="anthropic.claude-3-haiku-20240307-v1:0", body=json.dumps(body_data))
       result = json.loads(response["body"].read())
       comparison = result["content"][0]["text"]

   st.subheader("Comparison Results")
   st.markdown(comparison)

   st.subheader("Export Report")
   from fpdf import FPDF
   pdf = FPDF()
   pdf.add_page()
   pdf.set_font("Helvetica", "B", 20)
   pdf.cell(0, 15, "DFX Comparison Report", new_x="LMARGIN", new_y="NEXT", align="C")
   pdf.set_font("Helvetica", "", 12)
   pdf.cell(0, 10, "Image A: " + clean_pdf(uploaded_file_a.name), new_x="LMARGIN", new_y="NEXT")
   pdf.cell(0, 10, "Image B: " + clean_pdf(uploaded_file_b.name), new_x="LMARGIN", new_y="NEXT")
   pdf.ln(5)
   pdf.set_font("Helvetica", "", 10)
   for pdfline in comparison.split("\n"):
       cleaned = clean_pdf(pdfline.replace("#", "").strip())
       if cleaned:
           pdf.cell(0, 6, cleaned, new_x="LMARGIN", new_y="NEXT")
   pdf_bytes = pdf.output()
   st.download_button(label="Download Comparison Report", data=bytes(pdf_bytes), file_name="dfx_comparison_report.pdf", mime="application/pdf")

elif uploaded_file is not None or (process != "Server/Hardware Assembly" and uploaded_file is not None):
   pass

if uploaded_file is not None:

   if upload_type == "Image":
       import boto3
       from PIL import Image, ImageDraw, ImageFont

       st.image(uploaded_file, caption="Uploaded image", use_container_width=True)
       uploaded_file.seek(0)
       img_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
       img_tmp.write(uploaded_file.read())
       img_tmp_path = img_tmp.name
       img_tmp.close()
       uploaded_file.seek(0)

       with st.spinner("Analyzing image with AI..."):
           image_bytes = uploaded_file.read()
           image_b64 = base64.b64encode(image_bytes).decode()
           ext = uploaded_file.name.split(".")[-1].lower()
           media_types = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp", "gif": "image/gif"}
           media_type = media_types.get(ext, "image/png")
           rules_text = "\n".join(["- " + k + ": " + str(v) for k, v in rules.items()])
           prompt_intro = "a server or hardware assembly" if process == "Server/Hardware Assembly" else "an engineering drawing"
           prompt = "You are a strict, detail-oriented hardware design engineer performing a formal inspection.\n\n"
           prompt += "CRITICAL RULES FOR CONSISTENT SCORING:\n"
           prompt += "- Only mark FAIL if you can clearly see a violation in the image\n"
           prompt += "- Only mark WARN if something looks suspicious but you cannot confirm\n"
           prompt += "- Mark PASS only if you can positively confirm the rule is met\n"
           prompt += "- Mark N/A if the rule cannot be assessed from this image\n"
           prompt += "- Do NOT guess or assume - if you cannot see it clearly, mark N/A\n"
           prompt += "- Be conservative: when in doubt, mark WARN not PASS\n"
           prompt += "- Score = (PASS count) / (PASS + FAIL + WARN count) * 100. Exclude N/A from score.\n\n"
           prompt += "You are reviewing " + prompt_intro + ".\n\n"
           prompt += "Check against these rules:\n" + rules_text + "\n\n"
           prompt += "For each finding, estimate where in the image the issue is located using percentage coordinates (0,0 is top-left, 100,100 is bottom-right).\n\n"
           prompt += "Return a JSON block wrapped in triple-backtick json fence with structure: "
           prompt += '{\"findings\": [{\"label\": \"desc\", \"status\": \"FAIL/WARN/PASS/N/A\", \"x_pct\": 50, \"y_pct\": 30, \"detail\": \"explanation\"}], \"score\": 82, \"overview\": \"description\"}\n\n'
           prompt += "After the JSON, provide a human-readable report with: Overview, Errors, Warnings, Passed, Not Assessable, Design Score, Recommendations"
           client = boto3.client("bedrock-runtime", region_name="us-west-2")
           body_data = {"anthropic_version": "bedrock-2023-05-31", "max_tokens": 4000, "messages": [{"role": "user", "content": [{"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_b64}}, {"type": "text", "text": prompt}]}]}
           response = client.invoke_model(modelId="anthropic.claude-3-haiku-20240307-v1:0", body=json.dumps(body_data))
           result = json.loads(response["body"].read())
           analysis = result["content"][0]["text"]

       findings = []
       try:
           jm = "```json"
           js = analysis.find(jm)
           if js >= 0:
               je = analysis.find("```", js + len(jm))
               if je >= 0:
                   findings = json.loads(analysis[js + len(jm):je].strip()).get("findings", [])
       except Exception:
           pass

       if findings:
           img = Image.open(img_tmp_path).convert("RGB")
           draw = ImageDraw.Draw(img)
           w, h = img.size
           font_size = max(14, min(w, h) // 40)
           try:
               font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
           except Exception:
               font = ImageFont.load_default()
           colors_map = {"FAIL": (255, 50, 50), "WARN": (255, 180, 0), "PASS": (50, 200, 50)}
           radius = max(20, min(w, h) // 25)
           for finding in findings:
               if finding.get("status") == "N/A":
                   continue
               fx = int(finding.get("x_pct", 50) / 100 * w)
               fy = int(finding.get("y_pct", 50) / 100 * h)
               fcolor = colors_map.get(finding.get("status"), (150, 150, 150))
               flabel = finding.get("label", "")[:30]
               for offset in range(3):
                   draw.ellipse([fx-radius-offset, fy-radius-offset, fx+radius+offset, fy+radius+offset], outline=fcolor)
               bbox = draw.textbbox((0, 0), flabel, font=font)
               tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
               lx = max(5, min(fx - tw // 2, w - tw - 5))
               ly = fy - radius - th - 8
               if ly < 5:
                   ly = fy + radius + 5
               draw.rectangle([lx-3, ly-2, lx+tw+3, ly+th+2], fill=(0, 0, 0))
               draw.text((lx, ly), flabel, fill=fcolor, font=font)
           st.subheader("Marked-Up Image")
           st.image(img, caption="AI findings marked on image", use_container_width=True)
           markup_img_path = tempfile.mktemp(suffix=".png")
           img.save(markup_img_path)
       else:
           markup_img_path = img_tmp_path

       st.subheader("AI Analysis - " + process)
       display_text = analysis
       try:
           jm = "```json"
           js = analysis.find(jm)
           if js >= 0:
               je = analysis.find("```", js + len(jm))
               if je >= 0:
                   display_text = analysis[je + 3:].strip()
       except Exception:
           pass
       if display_text:
           st.markdown(display_text)

       st.subheader("Export Report")
       from fpdf import FPDF
       pdf = FPDF()
       pdf.add_page()
       pdf.set_font("Helvetica", "B", 20)
       pdf.cell(0, 15, "DFX Design Check Report", new_x="LMARGIN", new_y="NEXT", align="C")
       pdf.set_font("Helvetica", "", 12)
       pdf.cell(0, 10, clean_pdf("Process: " + process), new_x="LMARGIN", new_y="NEXT")
       pdf.cell(0, 10, clean_pdf("File: " + uploaded_file.name), new_x="LMARGIN", new_y="NEXT")
       pdf.ln(5)
       pdf.image(markup_img_path, x=10, w=190)
       pdf.ln(5)
       pdf.set_font("Helvetica", "", 10)
       for pdfline in display_text.split("\n"):
           cleaned = clean_pdf(pdfline.replace("#", "").strip())
           if cleaned:
               pdf.cell(0, 6, cleaned, new_x="LMARGIN", new_y="NEXT")
       pdf_bytes = pdf.output()
       if markup_img_path != img_tmp_path:
           os.unlink(markup_img_path)
       os.unlink(img_tmp_path)
       st.download_button(label="Download PDF Report", data=bytes(pdf_bytes), file_name="dfx_report.pdf", mime="application/pdf")

   else:
       with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp:
           tmp.write(uploaded_file.read())
           tmp_path = tmp.name

       doc = ezdxf.readfile(tmp_path)
       msp = doc.modelspace()
       circles = list(msp.query("CIRCLE"))
       lines = list(msp.query("LINE"))
       arcs = list(msp.query("ARC"))

       st.subheader("Drawing Summary")
       col1, col2, col3 = st.columns(3)
       col1.metric("Lines", len(lines))
       col2.metric("Circles/Holes", len(circles))
       col3.metric("Arcs", len(arcs))

       errors = []
       warnings = []
       passed = []
       markups = []

       for i, circle in enumerate(circles):
           r = circle.dxf.radius
           cx, cy = circle.dxf.center.x, circle.dxf.center.y
           loc = "at (" + str(round(cx,1)) + ", " + str(round(cy,1)) + ")"
           if r < rules["min_hole_radius"]:
               errors.append("Hole #" + str(i+1) + " " + loc + ": radius " + str(round(r,2)) + "mm < min " + str(rules["min_hole_radius"]) + "mm")
               markups.append({"type": "circle", "x": cx, "y": cy, "r": r, "color": "red", "label": "H" + str(i+1) + ": too small"})
           else:
               passed.append("Hole #" + str(i+1) + " " + loc + ": radius " + str(round(r,2)) + "mm - OK")
               markups.append({"type": "circle", "x": cx, "y": cy, "r": r, "color": "green", "label": ""})

       for i in range(len(circles)):
           for j in range(i + 1, len(circles)):
               c1 = circles[i].dxf.center
               c2 = circles[j].dxf.center
               dist = math.sqrt((c2.x - c1.x) ** 2 + (c2.y - c1.y) ** 2)
               edge_dist = dist - circles[i].dxf.radius - circles[j].dxf.radius
               if edge_dist < rules["min_hole_spacing"]:
                   errors.append("Holes #" + str(i+1) + " & #" + str(j+1) + ": spacing " + str(round(edge_dist,2)) + "mm < min " + str(rules["min_hole_spacing"]) + "mm")
                   markups.append({"type": "line_between", "x1": c1.x, "y1": c1.y, "x2": c2.x, "y2": c2.y, "color": "red", "label": str(round(edge_dist,1)) + "mm"})
               else:
                   passed.append("Holes #" + str(i+1) + " & #" + str(j+1) + ": spacing " + str(round(edge_dist,2)) + "mm - OK")

       for i, arc in enumerate(arcs):
           r = arc.dxf.radius
           cx, cy = arc.dxf.center.x, arc.dxf.center.y
           loc = "at (" + str(round(cx,1)) + ", " + str(round(cy,1)) + ")"
           if r < rules["min_arc_radius"]:
               errors.append("Arc #" + str(i+1) + " " + loc + ": radius " + str(round(r,2)) + "mm < min " + str(rules["min_arc_radius"]) + "mm")
               markups.append({"type": "point", "x": cx, "y": cy, "color": "red", "label": "Arc: " + str(round(r,2)) + "mm"})
           else:
               passed.append("Arc #" + str(i+1) + " " + loc + ": radius " + str(round(r,2)) + "mm - OK")
               markups.append({"type": "point", "x": cx, "y": cy, "color": "green", "label": ""})

       for i, line in enumerate(lines):
           s, e = line.dxf.start, line.dxf.end
           length = math.sqrt((e.x - s.x) ** 2 + (e.y - s.y) ** 2)
           if length < rules["min_line_length"]:
               mid_x, mid_y = (s.x + e.x) / 2, (s.y + e.y) / 2
               warnings.append("Line #" + str(i+1) + " at (" + str(round(mid_x,1)) + ", " + str(round(mid_y,1)) + "): length " + str(round(length,2)) + "mm - possible sliver")
               markups.append({"type": "point", "x": mid_x, "y": mid_y, "color": "orange", "label": "Sliver"})

       horizontal = []
       vertical = []
       for line in lines:
           s, e = line.dxf.start, line.dxf.end
           dx, dy = abs(e.x - s.x), abs(e.y - s.y)
           if dy < 0.01 and dx > 1.0:
               horizontal.append(line)
           elif dx < 0.01 and dy > 1.0:
               vertical.append(line)

       for i in range(len(horizontal)):
           for j in range(i + 1, len(horizontal)):
               y1 = horizontal[i].dxf.start.y
               y2 = horizontal[j].dxf.start.y
               gap = abs(y2 - y1)
               if 0 < gap < rules["min_wall_thickness"]:
                   mid_x = (horizontal[i].dxf.start.x + horizontal[i].dxf.end.x) / 2
                   mid_y = (y1 + y2) / 2
                   errors.append("Thin wall at (" + str(round(mid_x,1)) + ", " + str(round(mid_y,1)) + "): " + str(round(gap,2)) + "mm < min " + str(rules["min_wall_thickness"]) + "mm")
                   markups.append({"type": "rect", "x": horizontal[i].dxf.start.x, "y": min(y1, y2), "w": abs(horizontal[i].dxf.end.x - horizontal[i].dxf.start.x), "h": gap, "color": "red", "label": "Wall: " + str(round(gap,2)) + "mm"})

       for i in range(len(vertical)):
           for j in range(i + 1, len(vertical)):
               x1 = vertical[i].dxf.start.x
               x2 = vertical[j].dxf.start.x
               gap = abs(x2 - x1)
               if 0 < gap < rules["min_wall_thickness"]:
                   mid_y = (vertical[i].dxf.start.y + vertical[i].dxf.end.y) / 2
                   mid_x = (x1 + x2) / 2
                   errors.append("Thin wall at (" + str(round(mid_x,1)) + ", " + str(round(mid_y,1)) + "): " + str(round(gap,2)) + "mm < min " + str(rules["min_wall_thickness"]) + "mm")
                   markups.append({"type": "rect", "x": min(x1, x2), "y": vertical[i].dxf.start.y, "w": gap, "h": abs(vertical[i].dxf.end.y - vertical[i].dxf.start.y), "color": "red", "label": "Wall: " + str(round(gap,2)) + "mm"})

       st.subheader("Drawing Markup")
       fig, ax = plt.subplots(1, 1, figsize=(12, 8))
       ax.set_aspect("equal")
       ax.set_facecolor("#1a1a2e")
       fig.patch.set_facecolor("#1a1a2e")

       for line in lines:
           s, e = line.dxf.start, line.dxf.end
           ax.plot([s.x, e.x], [s.y, e.y], color="#555555", linewidth=0.8)
       for circle in circles:
           c = plt.Circle((circle.dxf.center.x, circle.dxf.center.y), circle.dxf.radius, fill=False, color="#555555", linewidth=0.8)
           ax.add_patch(c)
       for arc in arcs:
           a = mpatches.Arc((arc.dxf.center.x, arc.dxf.center.y), arc.dxf.radius * 2, arc.dxf.radius * 2, angle=0, theta1=arc.dxf.start_angle, theta2=arc.dxf.end_angle, color="#555555", linewidth=0.8)
           ax.add_patch(a)

       for m in markups:
           if m["type"] == "circle":
               highlight = plt.Circle((m["x"], m["y"]), m["r"] + 1, fill=False, color=m["color"], linewidth=2.5, linestyle="--")
               ax.add_patch(highlight)
               if m["label"]:
                   ax.annotate(m["label"], (m["x"], m["y"]), color=m["color"], fontsize=8, fontweight="bold", ha="center", xytext=(0, m["r"] + 3), textcoords="offset points")
           elif m["type"] == "line_between":
               ax.plot([m["x1"], m["x2"]], [m["y1"], m["y2"]], color=m["color"], linewidth=2, linestyle="--")
               mid_x = (m["x1"] + m["x2"]) / 2
               mid_y = (m["y1"] + m["y2"]) / 2
               ax.annotate(m["label"], (mid_x, mid_y), color=m["color"], fontsize=8, fontweight="bold", ha="center", xytext=(0, 8), textcoords="offset points")
           elif m["type"] == "point":
               ax.plot(m["x"], m["y"], "x", color=m["color"], markersize=12, markeredgewidth=2.5)
               if m["label"]:
                   ax.annotate(m["label"], (m["x"], m["y"]), color=m["color"], fontsize=8, fontweight="bold", xytext=(5, 5), textcoords="offset points")
           elif m["type"] == "rect":
               rect = plt.Rectangle((m["x"], m["y"]), m["w"], m["h"], fill=True, facecolor=m["color"], alpha=0.3, edgecolor=m["color"], linewidth=2)
               ax.add_patch(rect)
               if m["label"]:
                   ax.annotate(m["label"], (m["x"] + m["w"]/2, m["y"] + m["h"]/2), color="white", fontsize=8, fontweight="bold", ha="center")

       legend_elements = [
           plt.Line2D([0], [0], color="red", linewidth=2, linestyle="--", label="Error"),
           plt.Line2D([0], [0], color="orange", linewidth=2, linestyle="--", label="Warning"),
           plt.Line2D([0], [0], color="green", linewidth=2, linestyle="--", label="Passed"),
           plt.Line2D([0], [0], color="#555555", linewidth=1, label="Drawing"),
       ]
       ax.legend(handles=legend_elements, loc="upper right", facecolor="#1a1a2e", edgecolor="white", labelcolor="white")
       ax.tick_params(colors="white")
       ax.set_xlabel("X (mm)", color="white")
       ax.set_ylabel("Y (mm)", color="white")
       ax.autoscale()
       ax.margins(0.15)
       st.pyplot(fig)

       st.subheader("Results - " + process)
       if errors:
           st.error("Found " + str(len(errors)) + " error(s)")
           for e in errors:
               st.write("X " + e)
       if warnings:
           st.warning("Found " + str(len(warnings)) + " warning(s)")
           for w in warnings:
               st.write("! " + w)
       if passed:
           with st.expander(str(len(passed)) + " check(s) passed", expanded=False):
               for p in passed:
                   st.write("OK: " + p)
       if not errors and not warnings:
           st.balloons()
           st.success("All checks passed!")

       total = len(errors) + len(warnings) + len(passed)
       score = 0
       if total > 0:
           score = int((len(passed) / total) * 100)
           st.subheader("Design Score: " + str(score) + "%")
           st.progress(score / 100)

       st.subheader("Export Report")
       markup_path = tempfile.mktemp(suffix=".png")
       fig.savefig(markup_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())

       from fpdf import FPDF
       pdf = FPDF()
       pdf.add_page()
       pdf.set_font("Helvetica", "B", 20)
       pdf.cell(0, 15, "DFX Design Check Report", new_x="LMARGIN", new_y="NEXT", align="C")
       pdf.set_font("Helvetica", "", 12)
       pdf.cell(0, 10, clean_pdf("Process: " + process), new_x="LMARGIN", new_y="NEXT")
       pdf.cell(0, 10, clean_pdf("File: " + uploaded_file.name), new_x="LMARGIN", new_y="NEXT")
       pdf.cell(0, 10, "Score: " + str(score) + "%", new_x="LMARGIN", new_y="NEXT")
       pdf.cell(0, 10, "Errors: " + str(len(errors)) + " | Warnings: " + str(len(warnings)) + " | Passed: " + str(len(passed)), new_x="LMARGIN", new_y="NEXT")
       pdf.ln(5)
       pdf.image(markup_path, x=10, w=190)
       pdf.ln(5)
       if errors:
           pdf.set_font("Helvetica", "B", 14)
           pdf.set_text_color(200, 0, 0)
           pdf.cell(0, 10, "Errors (" + str(len(errors)) + ")", new_x="LMARGIN", new_y="NEXT")
           pdf.set_font("Helvetica", "", 10)
           for e in errors:
               pdf.cell(0, 7, clean_pdf(e), new_x="LMARGIN", new_y="NEXT")
       if warnings:
           pdf.set_font("Helvetica", "B", 14)
           pdf.set_text_color(200, 150, 0)
           pdf.cell(0, 10, "Warnings (" + str(len(warnings)) + ")", new_x="LMARGIN", new_y="NEXT")
           pdf.set_font("Helvetica", "", 10)
           for w in warnings:
               pdf.cell(0, 7, clean_pdf(w), new_x="LMARGIN", new_y="NEXT")
       if passed:
           pdf.set_font("Helvetica", "B", 14)
           pdf.set_text_color(0, 150, 0)
           pdf.cell(0, 10, "Passed (" + str(len(passed)) + ")", new_x="LMARGIN", new_y="NEXT")
           pdf.set_font("Helvetica", "", 10)
           for p in passed:
               pdf.cell(0, 7, clean_pdf(p), new_x="LMARGIN", new_y="NEXT")
       pdf_bytes = pdf.output()
       os.unlink(markup_path)
       st.download_button(label="Download PDF Report", data=bytes(pdf_bytes), file_name="dfx_report.pdf", mime="application/pdf")
       os.unlink(tmp_path)
