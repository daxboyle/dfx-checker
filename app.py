import streamlit as st
import ezdxf
import tempfile
import os
import math
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

st.title("DFX Design Checker")

# --- SIDEBAR: PROCESS SELECTION ---
st.sidebar.header("Configuration")
process = st.sidebar.selectbox("Manufacturing Process", [
   "CNC Machining",
   "Injection Molding",
   "Sheet Metal",
   "3D Printing (FDM)",
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
}

rules = RULES[process]

st.sidebar.header("Active Rules")
st.sidebar.write(f"**Min hole radius:** {rules['min_hole_radius']}mm")
st.sidebar.write(f"**Min arc radius:** {rules['min_arc_radius']}mm")
st.sidebar.write(f"**Min line length:** {rules['min_line_length']}mm")
st.sidebar.write(f"**Min hole spacing:** {rules['min_hole_spacing']}mm")
st.sidebar.write(f"**Min wall thickness:** {rules['min_wall_thickness']}mm")

st.sidebar.header("Custom Overrides")
rules["min_hole_radius"] = st.sidebar.number_input(
   "Override min hole radius (mm)", value=rules["min_hole_radius"], step=0.1
)
rules["min_wall_thickness"] = st.sidebar.number_input(
   "Override min wall thickness (mm)", value=rules["min_wall_thickness"], step=0.1
)

# --- FILE UPLOAD ---
st.write(f"Upload a .dxf file to check against **{process}** rules.")
uploaded_file = st.file_uploader("Choose a .dxf file", type=["dxf"])

if uploaded_file is not None:
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
   # Store markup annotations: (x, y, color, label)
   markups = []

   # --- RULE: Hole Size ---
   for i, circle in enumerate(circles):
       r = circle.dxf.radius
       cx, cy = circle.dxf.center.x, circle.dxf.center.y
       loc = f"at ({cx:.1f}, {cy:.1f})"
       if r < rules["min_hole_radius"]:
           errors.append(
               f"❌ **Hole #{i+1}** {loc}: radius {r:.2f}mm < min {rules['min_hole_radius']}mm"
           )
           markups.append({"type": "circle", "x": cx, "y": cy, "r": r, "color": "red", "label": f"H{i+1}: too small"})
       else:
           passed.append(f"✅ **Hole #{i+1}** {loc}: radius {r:.2f}mm — OK")
           markups.append({"type": "circle", "x": cx, "y": cy, "r": r, "color": "green", "label": ""})

   # --- RULE: Hole Spacing ---
   for i in range(len(circles)):
       for j in range(i + 1, len(circles)):
           c1 = circles[i].dxf.center
           c2 = circles[j].dxf.center
           dist = math.sqrt((c2.x - c1.x) ** 2 + (c2.y - c1.y) ** 2)
           edge_dist = dist - circles[i].dxf.radius - circles[j].dxf.radius
           mid_x = (c1.x + c2.x) / 2
           mid_y = (c1.y + c2.y) / 2
           if edge_dist < rules["min_hole_spacing"]:
               errors.append(
                   f"❌ **Holes #{i+1} & #{j+1}**: edge spacing {edge_dist:.2f}mm "
                   f"< min {rules['min_hole_spacing']}mm"
               )
               markups.append({"type": "line_between", "x1": c1.x, "y1": c1.y,
                               "x2": c2.x, "y2": c2.y, "color": "red",
                               "label": f"{edge_dist:.1f}mm"})
           else:
               passed.append(
                   f"✅ **Holes #{i+1} & #{j+1}**: edge spacing {edge_dist:.2f}mm — OK"
               )

   # --- RULE: Arc Radius ---
   for i, arc in enumerate(arcs):
       r = arc.dxf.radius
       cx, cy = arc.dxf.center.x, arc.dxf.center.y
       loc = f"at ({cx:.1f}, {cy:.1f})"
       if r < rules["min_arc_radius"]:
           errors.append(
               f"❌ **Arc #{i+1}** {loc}: radius {r:.2f}mm < min {rules['min_arc_radius']}mm"
           )
           markups.append({"type": "point", "x": cx, "y": cy, "color": "red", "label": f"Arc: {r:.2f}mm"})
       else:
           passed.append(f"✅ **Arc #{i+1}** {loc}: radius {r:.2f}mm — OK")
           markups.append({"type": "point", "x": cx, "y": cy, "color": "green", "label": ""})

   # --- RULE: Short Lines ---
   for i, line in enumerate(lines):
       s, e = line.dxf.start, line.dxf.end
       length = math.sqrt((e.x - s.x) ** 2 + (e.y - s.y) ** 2)
       if length < rules["min_line_length"]:
           mid_x, mid_y = (s.x + e.x) / 2, (s.y + e.y) / 2
           warnings.append(
               f"⚠️ **Line #{i+1}** at ({mid_x:.1f}, {mid_y:.1f}): "
               f"length {length:.2f}mm — possible sliver"
           )
           markups.append({"type": "point", "x": mid_x, "y": mid_y, "color": "orange", "label": f"Sliver"})

   # --- RULE: Wall Thickness ---
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
               errors.append(
                   f"❌ **Thin wall** at ({mid_x:.1f}, {mid_y:.1f}): "
                   f"{gap:.2f}mm < min {rules['min_wall_thickness']}mm"
               )
               markups.append({"type": "rect", "x": horizontal[i].dxf.start.x,
                               "y": min(y1, y2), "w": abs(horizontal[i].dxf.end.x - horizontal[i].dxf.start.x),
                               "h": gap, "color": "red", "label": f"Wall: {gap:.2f}mm"})

   for i in range(len(vertical)):
       for j in range(i + 1, len(vertical)):
           x1 = vertical[i].dxf.start.x
           x2 = vertical[j].dxf.start.x
           gap = abs(x2 - x1)
           if 0 < gap < rules["min_wall_thickness"]:
               mid_y = (vertical[i].dxf.start.y + vertical[i].dxf.end.y) / 2
               mid_x = (x1 + x2) / 2
               errors.append(
                   f"❌ **Thin wall** at ({mid_x:.1f}, {mid_y:.1f}): "
                   f"{gap:.2f}mm < min {rules['min_wall_thickness']}mm"
               )
               markups.append({"type": "rect", "x": min(x1, x2), "y": vertical[i].dxf.start.y,
                               "w": gap, "h": abs(vertical[i].dxf.end.y - vertical[i].dxf.start.y),
                               "color": "red", "label": f"Wall: {gap:.2f}mm"})

   # --- VISUAL MARKUP ---
   st.subheader("Drawing Markup")
   fig, ax = plt.subplots(1, 1, figsize=(12, 8))
   ax.set_aspect('equal')
   ax.set_facecolor('#1a1a2e')
   fig.patch.set_facecolor('#1a1a2e')

   # Draw all geometry in gray first
   for line in lines:
       s, e = line.dxf.start, line.dxf.end
       ax.plot([s.x, e.x], [s.y, e.y], color='#555555', linewidth=0.8)
   for circle in circles:
       c = plt.Circle((circle.dxf.center.x, circle.dxf.center.y),
                       circle.dxf.radius, fill=False, color='#555555', linewidth=0.8)
       ax.add_patch(c)
   for arc in arcs:
       a = mpatches.Arc((arc.dxf.center.x, arc.dxf.center.y),
                        arc.dxf.radius * 2, arc.dxf.radius * 2,
                        angle=0, theta1=arc.dxf.start_angle, theta2=arc.dxf.end_angle,
                        color='#555555', linewidth=0.8)
       ax.add_patch(a)

   # Draw markups on top
   for m in markups:
       if m["type"] == "circle":
           highlight = plt.Circle((m["x"], m["y"]), m["r"] + 1,
                                  fill=False, color=m["color"], linewidth=2.5, linestyle='--')
           ax.add_patch(highlight)
           if m["label"]:
               ax.annotate(m["label"], (m["x"], m["y"]), color=m["color"],
                          fontsize=8, fontweight='bold', ha='center',
                          xytext=(0, m["r"] + 3), textcoords='offset points')
       elif m["type"] == "line_between":
           ax.plot([m["x1"], m["x2"]], [m["y1"], m["y2"]],
                   color=m["color"], linewidth=2, linestyle='--')
           mid_x = (m["x1"] + m["x2"]) / 2
           mid_y = (m["y1"] + m["y2"]) / 2
           ax.annotate(m["label"], (mid_x, mid_y), color=m["color"],
                      fontsize=8, fontweight='bold', ha='center',
                      xytext=(0, 8), textcoords='offset points')
       elif m["type"] == "point":
           ax.plot(m["x"], m["y"], 'x', color=m["color"], markersize=12, markeredgewidth=2.5)
           if m["label"]:
               ax.annotate(m["label"], (m["x"], m["y"]), color=m["color"],
                          fontsize=8, fontweight='bold',
                          xytext=(5, 5), textcoords='offset points')
       elif m["type"] == "rect":
           rect = plt.Rectangle((m["x"], m["y"]), m["w"], m["h"],
                                 fill=True, facecolor=m["color"], alpha=0.3,
                                 edgecolor=m["color"], linewidth=2)
           ax.add_patch(rect)
           if m["label"]:
               ax.annotate(m["label"], (m["x"] + m["w"]/2, m["y"] + m["h"]/2),
                          color='white', fontsize=8, fontweight='bold', ha='center')

   # Legend
   legend_elements = [
       plt.Line2D([0], [0], color='red', linewidth=2, linestyle='--', label='Error'),
       plt.Line2D([0], [0], color='orange', linewidth=2, linestyle='--', label='Warning'),
       plt.Line2D([0], [0], color='green', linewidth=2, linestyle='--', label='Passed'),
       plt.Line2D([0], [0], color='#555555', linewidth=1, label='Drawing'),
   ]
   ax.legend(handles=legend_elements, loc='upper right', facecolor='#1a1a2e',
             edgecolor='white', labelcolor='white')

   ax.tick_params(colors='white')
   ax.set_xlabel('X (mm)', color='white')
   ax.set_ylabel('Y (mm)', color='white')
   ax.autoscale()
   ax.margins(0.15)

   st.pyplot(fig)

   # --- TEXT RESULTS ---
   st.subheader(f"Results — {process}")

   if errors:
       st.error(f"🚫 {len(errors)} Error(s)")
       for e in errors:
           st.write(e)
   if warnings:
       st.warning(f"⚠️ {len(warnings)} Warning(s)")
       for w in warnings:
           st.write(w)
   if passed:
       with st.expander(f"✅ {len(passed)} Passed", expanded=False):
           for p in passed:
               st.write(p)

   if not errors and not warnings:
       st.balloons()
       st.success("🎉 All checks passed!")

   total = len(errors) + len(warnings) + len(passed)
   if total > 0:
       score = int((len(passed) / total) * 100)
       st.subheader(f"Design Score: {score}%")
       st.progress(score / 100)

   os.unlink(tmp_path)
