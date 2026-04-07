import streamlit as st
import json, os, base64, math, ezdxf
import matplotlib.pyplot as plt

st.set_page_config(page_title="Drawing & BOM Compare", page_icon="\U0001f4d0", layout="wide")
st.title("Drawing & BOM Compare")
DATA_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def clean_pdf(text):
    return ''.join(ch if ord(ch) < 128 else ' ' for ch in text)

tab1, tab2, tab3 = st.tabs(["Drawing Compare", "BOM Compare", "BOM Audit"])

with tab1:
    st.subheader("Compare Drawing Revisions")
    col_b, col_a = st.columns(2)
    with col_b:
        st.write("**Before (Original)**")
        files_before = st.file_uploader("Upload original(s)", type=["dxf","png","jpg","jpeg","pdf"], key="drw_b", accept_multiple_files=True)
    with col_a:
        st.write("**After (Revised)**")
        files_after = st.file_uploader("Upload revised(s)", type=["dxf","png","jpg","jpeg","pdf"], key="drw_a", accept_multiple_files=True)
    if files_before and files_after:
        if len(files_before) != len(files_after):
            st.warning("File count mismatch")
        else:
            for pair_idx in range(len(files_before)):
                fb = files_before[pair_idx]; fa = files_after[pair_idx]
                st.write("---")
                st.subheader("Pair " + str(pair_idx+1) + ": " + fb.name + " vs " + fa.name)
                ext_b = fb.name.split(".")[-1].lower(); ext_a = fa.name.split(".")[-1].lower()
                fb.seek(0); fa.seek(0)
                # Extract pages
                pages_b = []; pages_a = []
                if ext_b == "pdf":
                    import fitz, tempfile as tf
                    tmp = tf.NamedTemporaryFile(delete=False, suffix=".pdf"); tmp.write(fb.read()); tmp.close()
                    doc = fitz.open(tmp.name)
                    for pg in range(len(doc)): pages_b.append(doc[pg].get_pixmap(dpi=200).tobytes("png"))
                    doc.close(); os.unlink(tmp.name)
                else: pages_b.append(fb.read())
                if ext_a == "pdf":
                    import fitz, tempfile as tf
                    tmp = tf.NamedTemporaryFile(delete=False, suffix=".pdf"); tmp.write(fa.read()); tmp.close()
                    doc = fitz.open(tmp.name)
                    for pg in range(len(doc)): pages_a.append(doc[pg].get_pixmap(dpi=200).tobytes("png"))
                    doc.close(); os.unlink(tmp.name)
                else: pages_a.append(fa.read())
                st.write("Before: " + str(len(pages_b)) + " page(s) | After: " + str(len(pages_a)) + " page(s)")
                mx = max(len(pages_b), len(pages_a))
                for pi in range(mx):
                    if pi < len(pages_b) and pi < len(pages_a):
                        c1, c2 = st.columns(2)
                        with c1: st.image(pages_b[pi], caption="Before Pg " + str(pi+1), use_container_width=True)
                        with c2: st.image(pages_a[pi], caption="After Pg " + str(pi+1), use_container_width=True)
                if st.button("Analyze All Pages", key="az_" + str(pair_idx), type="primary"):
                    import boto3
                    from botocore.config import Config as BC
                    all_res = []; all_mk = []
                    prog = st.progress(0)
                    mn = min(len(pages_b), len(pages_a))
                    for pi in range(mn):
                        with st.spinner("Page " + str(pi+1) + "/" + str(mn) + "..."):
                            b1 = base64.b64encode(pages_b[pi]).decode()
                            b2 = base64.b64encode(pages_a[pi]).decode()
                            pr = "You are an expert manufacturing engineer comparing two drawing versions.\n"
                            pr += "Image 1=BEFORE, Image 2=AFTER. Be THOROUGH.\n\n"
                            pr += "## Changes Found\nEach: number, description, BEFORE->AFTER, location.\n\n"
                            pr += "## Manufacturing Impact\nFor EACH change: specific impact (tooling, fixtures, CNC, assembly, inspection).\n\n"
                            pr += "## Cost & Cycle Time\nPer change: $/unit, cycle time, one-time costs. Total for 1000 units.\n\n"
                            pr += "## ECN Requirements\nFormal ECN, work instructions, training, quality plan, supplier notification.\n\n"
                            pr += "## Summary\nTotal changes, combined impact, recommended actions."
                            cl = boto3.client("bedrock-runtime", region_name="us-west-2", config=BC(read_timeout=120))
                            bd = {"anthropic_version": "bedrock-2023-05-31", "max_tokens": 4000, "messages": [{"role": "user", "content": [{"type": "text", "text": "BEFORE:"}, {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b1}}, {"type": "text", "text": "AFTER:"}, {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b2}}, {"type": "text", "text": pr}]}]}
                            rsp = cl.invoke_model(modelId="us.anthropic.claude-sonnet-4-6", body=json.dumps(bd))
                            atxt = json.loads(rsp["body"].read())["content"][0]["text"]
                            all_res.append({"page": pi+1, "text": atxt})
                            # Markup
                            mp = "Locate EVERY change. Return ONLY JSON: {\"changes\": [{\"label\": \"desc\", \"x_pct\": 50, \"y_pct\": 30, \"type\": \"added/removed/modified\"}]}. Include ALL."
                            bd2 = {"anthropic_version": "bedrock-2023-05-31", "max_tokens": 2000, "messages": [{"role": "user", "content": [{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b2}}, {"type": "text", "text": "Changes: " + atxt + "\n\n" + mp}]}]}
                            rsp2 = cl.invoke_model(modelId="us.anthropic.claude-sonnet-4-6", body=json.dumps(bd2))
                            mt = json.loads(rsp2["body"].read())["content"][0]["text"]
                            mc = []
                            try:
                                jm = chr(96)*3+"json"; js = mt.find(jm)
                                if js >= 0:
                                    je = mt.find(chr(96)*3, js+len(jm))
                                    if je >= 0: mc = json.loads(mt[js+len(jm):je].strip()).get("changes",[])
                            except: pass
                            from PIL import Image as PI, ImageDraw as PD, ImageFont as PF
                            import io
                            img = PI.open(io.BytesIO(pages_a[pi])).convert('RGB')
                            if mc:
                                drw = PD.Draw(img); w, h = img.size
                                try: fnt = PF.truetype("/System/Library/Fonts/Helvetica.ttc", max(14, min(w,h)//40))
                                except: fnt = PF.load_default()
                                cm = {"added":(255,50,50),"removed":(255,170,0),"modified":(255,255,0)}
                                cr = max(25, min(w,h)//20)
                                for ci, ch in enumerate(mc):
                                    cx=int(ch.get("x_pct",50)/100*w); cy=int(ch.get("y_pct",50)/100*h)
                                    clr=cm.get(ch.get("type","modified"),(255,255,0))
                                    lb=str(ci+1)+": "+ch.get("label","")[:25]
                                    for k in range(20):
                                        a1=k*2*math.pi/20; a2=(k+1)*2*math.pi/20; ma=(a1+a2)/2
                                        bmp=cr+(8 if k%2==0 else -3)
                                        drw.line([(int(cx+cr*math.cos(a1)),int(cy+cr*math.sin(a1))),(int(cx+bmp*math.cos(ma)),int(cy+bmp*math.sin(ma))),(int(cx+cr*math.cos(a2)),int(cy+cr*math.sin(a2)))],fill=clr,width=3)
                                    bb=drw.textbbox((0,0),lb,font=fnt); tw=bb[2]-bb[0]; tht=bb[3]-bb[1]
                                    lx=max(5,min(cx-tw//2,w-tw-5)); ly=cy-cr-tht-10
                                    if ly<5: ly=cy+cr+5
                                    drw.rectangle([lx-3,ly-2,lx+tw+3,ly+tht+2],fill=(0,0,0))
                                    drw.text((lx,ly),lb,fill=clr,font=fnt)
                            all_mk.append(img)
                        prog.progress((pi+1)/mn)
                    for ri, r in enumerate(all_res):
                        st.write("---")
                        st.subheader("Page " + str(r["page"]))
                        if ri < len(all_mk):
                            st.image(all_mk[ri], caption="Markup Pg " + str(r["page"]), use_container_width=True)
                            st.markdown("Red=Added | Orange=Removed | Yellow=Modified")
                        st.markdown(r["text"])
                    # PDF
                    from fpdf import FPDF; import tempfile as rtf
                    rpdf = FPDF(); rpdf.add_page()
                    rpdf.set_font("Helvetica","B",20)
                    rpdf.cell(0,15,"Drawing Comparison Report",new_x="LMARGIN",new_y="NEXT",align="C")
                    rpdf.set_font("Helvetica","",12)
                    rpdf.cell(0,10,"Before: "+clean_pdf(fb.name),new_x="LMARGIN",new_y="NEXT")
                    rpdf.cell(0,10,"After: "+clean_pdf(fa.name),new_x="LMARGIN",new_y="NEXT")
                    for ri, r in enumerate(all_res):
                        rpdf.add_page()
                        rpdf.set_font("Helvetica","B",16)
                        rpdf.cell(0,12,"Page "+str(r["page"]),new_x="LMARGIN",new_y="NEXT")
                        if ri < len(all_mk):
                            mt2=rtf.mktemp(suffix=".png"); all_mk[ri].save(mt2)
                            rpdf.image(mt2,x=10,w=190); rpdf.ln(5); os.unlink(mt2)
                        rpdf.set_font("Helvetica","",10)
                        for rl in r["text"].split("\n"):
                            cl2=clean_pdf(rl.replace("#","").strip())
                            if cl2: rpdf.cell(0,6,cl2,new_x="LMARGIN",new_y="NEXT")
                    st.download_button("Download Full Report",bytes(rpdf.output()),"drawing_comparison.pdf","application/pdf",key="dl_"+str(pair_idx))

with tab2:
    st.subheader("Compare Bills of Materials")
    st.write("Upload before/after BOMs as CSV. Columns: Part Number, Description, Quantity, optionally Vendor, Unit Cost")
    c1, c2 = st.columns(2)
    with c1:
        st.write("**Before BOM**")
        bom_b = st.file_uploader("Original BOM", type=["csv"], key="bom_b")
    with c2:
        st.write("**After BOM**")
        bom_a = st.file_uploader("Revised BOM", type=["csv"], key="bom_a")
    if bom_b and bom_a:
        import csv, io
        bom_b.seek(0); bom_a.seek(0)
        rb = list(csv.DictReader(io.StringIO(bom_b.read().decode("utf-8"))))
        ra = list(csv.DictReader(io.StringIO(bom_a.read().decode("utf-8"))))
        pn = None
        for f in ["Part Number","PartNumber","part_number","PN","pn","Item"]:
            if f in (rb[0] if rb else {}): pn = f; break
        if not pn and rb: pn = list(rb[0].keys())[0]
        bd = {}
        for r in rb: bd[r.get(pn,'')] = r
        ad = {}
        for r in ra: ad[r.get(pn,'')] = r
        added = [p for p in ad if p not in bd]
        removed = [p for p in bd if p not in ad]
        modified = [p for p in ad if p in bd and str(ad[p]) != str(bd[p])]
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Before",len(rb)); c2.metric("After",len(ra))
        c3.metric("Added",len(added)); c4.metric("Removed",len(removed))
        if added:
            st.subheader("Added (" + str(len(added)) + ")")
            for p in added:
                st.write("+ **" + p + "** - " + ad[p].get("Description",ad[p].get("description","")))
        if removed:
            st.subheader("Removed (" + str(len(removed)) + ")")
            for p in removed:
                st.write("- **" + p + "** - " + bd[p].get("Description",bd[p].get("description","")))
        if modified:
            st.subheader("Modified (" + str(len(modified)) + ")")
            for p in modified:
                with st.expander("~ **" + p + "**"):
                    for key in ad[p]:
                        if str(ad[p].get(key,'')) != str(bd[p].get(key,'')):
                            st.write("  " + key + ": " + str(bd[p].get(key,"")) + " -> " + str(ad[p].get(key,"")))
        if not added and not removed and not modified:
            st.success("BOMs are identical!")
        # Cost impact
        cf = None
        for f in ["Unit Cost","UnitCost","unit_cost","Cost","cost"]:
            if f in (rb[0] if rb else {}): cf = f; break
        qf = None
        for f in ["Quantity","Qty","qty","QTY"]:
            if f in (rb[0] if rb else {}): qf = f; break
        if cf and qf:
            st.subheader("Cost Impact")
            try:
                cb = sum(float(r.get(cf,0))*float(r.get(qf,0)) for r in rb)
                ca = sum(float(r.get(cf,0))*float(r.get(qf,0)) for r in ra)
                d = ca - cb
                x1,x2,x3 = st.columns(3)
                x1.metric("Before","$"+str(round(cb,2)))
                x2.metric("After","$"+str(round(ca,2)))
                x3.metric("Delta","$"+str(round(d,2)),delta_color="inverse")
            except: st.write("Could not calculate - check CSV formatting")
        # PDF
        from fpdf import FPDF
        bpdf = FPDF(); bpdf.add_page()
        bpdf.set_font("Helvetica","B",20)
        bpdf.cell(0,15,"BOM Comparison Report",new_x="LMARGIN",new_y="NEXT",align="C")
        bpdf.set_font("Helvetica","",12)
        bpdf.cell(0,10,"Added: "+str(len(added))+" | Removed: "+str(len(removed))+" | Modified: "+str(len(modified)),new_x="LMARGIN",new_y="NEXT")
        bpdf.ln(5); bpdf.set_font("Helvetica","",10)
        if added:
            bpdf.set_font("Helvetica","B",14); bpdf.cell(0,10,"Added Parts",new_x="LMARGIN",new_y="NEXT")
            bpdf.set_font("Helvetica","",10)
            for p in added: bpdf.cell(0,7,"+ "+clean_pdf(p+" - "+ad[p].get("Description","")),new_x="LMARGIN",new_y="NEXT")
        if removed:
            bpdf.set_font("Helvetica","B",14); bpdf.cell(0,10,"Removed Parts",new_x="LMARGIN",new_y="NEXT")
            bpdf.set_font("Helvetica","",10)
            for p in removed: bpdf.cell(0,7,"- "+clean_pdf(p+" - "+bd[p].get("Description","")),new_x="LMARGIN",new_y="NEXT")
        if modified:
            bpdf.set_font("Helvetica","B",14); bpdf.cell(0,10,"Modified Parts",new_x="LMARGIN",new_y="NEXT")
            bpdf.set_font("Helvetica","",10)
            for p in modified:
                bpdf.cell(0,7,clean_pdf(p),new_x="LMARGIN",new_y="NEXT")
                for key in ad[p]:
                    if str(ad[p].get(key,'')) != str(bd[p].get(key,'')):
                        bpdf.cell(0,6,"  "+clean_pdf(key+": "+str(bd[p].get(key,""))+" -> "+str(ad[p].get(key,""))),new_x="LMARGIN",new_y="NEXT")
        st.download_button("Download BOM Report",bytes(bpdf.output()),"bom_comparison.pdf","application/pdf",key="dl_bom")

with tab3:
    st.subheader("BOM Audit & Compliance")
    st.write("Upload a vendor BOM to check against best practice rules.")
    BOM_RULES_FILE = os.path.join(DATA_DIR, "bom_rules.json")
    default_rules = [
        {"id": "BOM-001", "name": "Part Number Required", "check": "pn", "severity": "error", "description": "Every row must have a part number"},
        {"id": "BOM-002", "name": "Description Required", "check": "desc", "severity": "error", "description": "Every row must have a description"},
        {"id": "BOM-003", "name": "Quantity Required", "check": "qty", "severity": "error", "description": "Every row must have quantity > 0"},
        {"id": "BOM-004", "name": "Unit Cost Required", "check": "cost", "severity": "warning", "description": "Every row should have unit cost"},
        {"id": "BOM-005", "name": "Vendor Specified", "check": "vendor", "severity": "warning", "description": "Every row should specify vendor"},
        {"id": "BOM-006", "name": "No Duplicate PNs", "check": "dupes", "severity": "error", "description": "Each part number once only"},
        {"id": "BOM-007", "name": "Revision Level", "check": "rev", "severity": "warning", "description": "Parts should have revision level"},
        {"id": "BOM-008", "name": "Unit of Measure", "check": "uom", "severity": "warning", "description": "Each row should have UOM"},
    ]
    if os.path.exists(BOM_RULES_FILE):
        with open(BOM_RULES_FILE, "r") as rf: bom_rules = json.load(rf)
    else:
        bom_rules = default_rules
        with open(BOM_RULES_FILE, "w") as rf: json.dump(bom_rules, rf, indent=2)
    with st.expander("View/Edit BOM Rules"):
        for rule in bom_rules:
            st.write("**" + rule["id"] + "** [" + rule["severity"].upper() + "] " + rule["name"] + " - " + rule["description"])
        nr_name = st.text_input("New rule name:", key="br_n")
        nr_desc = st.text_input("Description:", key="br_d")
        nr_sev = st.selectbox("Severity:", ["error", "warning", "info"], key="br_s")
        if st.button("Add Rule", key="add_br"):
            if nr_name:
                bom_rules.append({"id": "BOM-" + str(len(bom_rules)+1).zfill(3), "name": nr_name, "check": "custom", "severity": nr_sev, "description": nr_desc})
                with open(BOM_RULES_FILE, "w") as rf: json.dump(bom_rules, rf, indent=2)
                st.success("Added!"); st.rerun()
    bom_file = st.file_uploader("Upload vendor BOM (CSV)", type=["csv"], key="bom_audit")
    if bom_file:
        import csv, io
        bom_file.seek(0)
        rows = list(csv.DictReader(io.StringIO(bom_file.read().decode("utf-8"))))
        if not rows: st.stop()
        cols = list(rows[0].keys())
        st.write(str(len(rows)) + " items, columns: " + ", ".join(cols))
        pn_col = next((c for c in cols if c.lower() in ["part number","partnumber","pn","item"]), None)
        desc_col = next((c for c in cols if c.lower() in ["description","desc","name"]), None)
        qty_col = next((c for c in cols if c.lower() in ["quantity","qty"]), None)
        cost_col = next((c for c in cols if c.lower() in ["unit cost","unitcost","cost","price"]), None)
        vendor_col = next((c for c in cols if c.lower() in ["vendor","supplier","manufacturer"]), None)
        rev_col = next((c for c in cols if c.lower() in ["revision","rev"]), None)
        uom_col = next((c for c in cols if c.lower() in ["uom","unit","unit of measure"]), None)
        errors = []; warnings = []; infos = []; passed = []
        if pn_col:
            miss = [i+1 for i, r in enumerate(rows) if not r.get(pn_col, '').strip()]
            if miss: errors.append("BOM-001: " + str(len(miss)) + " rows missing part number")
            else: passed.append("BOM-001: All part numbers present")
            pns = [r.get(pn_col, '') for r in rows if r.get(pn_col, '').strip()]
            dupes = set([p for p in pns if pns.count(p) > 1])
            if dupes: errors.append("BOM-006: Duplicates: " + ", ".join(list(dupes)[:5]))
            else: passed.append("BOM-006: No duplicates")
        else: errors.append("BOM-001: No Part Number column found")
        if desc_col:
            miss = [i+1 for i, r in enumerate(rows) if not r.get(desc_col, '').strip()]
            if miss: errors.append("BOM-002: " + str(len(miss)) + " rows missing description")
            else: passed.append("BOM-002: All descriptions present")
        else: errors.append("BOM-002: No Description column")
        if qty_col:
            bad = []
            for i, r in enumerate(rows):
                try:
                    if float(r.get(qty_col, 0)) <= 0: bad.append(i+1)
                except: bad.append(i+1)
            if bad: errors.append("BOM-003: " + str(len(bad)) + " rows invalid quantity")
            else: passed.append("BOM-003: All quantities valid")
        else: errors.append("BOM-003: No Quantity column")
        if cost_col: passed.append("BOM-004: Cost column present")
        else: warnings.append("BOM-004: No Unit Cost column")
        if vendor_col: passed.append("BOM-005: Vendor column present")
        else: warnings.append("BOM-005: No Vendor column")
        if rev_col: passed.append("BOM-007: Revision column present")
        else: warnings.append("BOM-007: No Revision column")
        if uom_col: passed.append("BOM-008: UOM column present")
        else: warnings.append("BOM-008: No UOM column")
        total = len(errors) + len(warnings) + len(infos) + len(passed)
        score = int(len(passed) / total * 100) if total > 0 else 0
        st.subheader("Audit Score: " + str(score) + "%")
        st.progress(score / 100)
        if errors:
            st.error(str(len(errors)) + " Error(s)")
            for e in errors: st.write("X " + e)
        if warnings:
            st.warning(str(len(warnings)) + " Warning(s)")
            for w in warnings: st.write("! " + w)
        if passed:
            with st.expander(str(len(passed)) + " Passed"):
                for p in passed: st.write("OK " + p)
        if st.button("Get AI Recommendations", type="primary", key="ai_bom"):
            import boto3
            from botocore.config import Config as BC
            with st.spinner("Analyzing BOM..."):
                bom_text = ', '.join(cols)
                for r in rows[:50]: bom_text += '\n' + ', '.join([str(r.get(c,'')) for c in cols])
                rules_text = '\n'.join(['- ' + r['id'] + ': ' + r['name'] + ' - ' + r['description'] for r in bom_rules])
                ar = "Errors: " + "; ".join(errors) + "\nWarnings: " + "; ".join(warnings)
                pr = "You are a manufacturing BOM compliance expert.\n\n"
                pr += "Vendor BOM (first 50 rows):\n" + bom_text + "\n\n"
                pr += "Rules:\n" + rules_text + "\n\n"
                pr += "Findings:\n" + ar + "\n\n"
                pr += "Provide:\n## Compliance Assessment\n## Specific Issues & Fixes\n## Missing Information\n## Recommendations (prioritized)\n## Risk if Released As-Is"
                cl = boto3.client("bedrock-runtime", region_name="us-west-2", config=BC(read_timeout=120))
                bd = {"anthropic_version": "bedrock-2023-05-31", "max_tokens": 4000, "messages": [{"role": "user", "content": [{"type": "text", "text": pr}]}]}
                rsp = cl.invoke_model(modelId="us.anthropic.claude-sonnet-4-6", body=json.dumps(bd))
                rec = json.loads(rsp["body"].read())["content"][0]["text"]
            st.subheader("AI Recommendations")
            st.markdown(rec)
