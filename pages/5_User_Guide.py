import streamlit as st

st.set_page_config(page_title="User Guide", page_icon="\U0001f4d6", layout="wide")
st.title("DFX Platform User Guide")
st.write("Step-by-step tutorials for every feature. Follow along to learn the platform.")

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["Getting Started", "DFX Checker", "Inspection", "CI Tracker", "DFM Agent", "Drawing Compare", "BOM Tools"])

with tab1:
    st.header("Getting Started")
    st.subheader("1. Installation")
    st.markdown("""
**First time setup:**
1. Open Terminal on your Mac
2. Run: `git clone https://github.com/daxboyle/dfx-checker.git`
3. Run: `cd dfx-checker`
4. Run: `./setup.sh`

**Daily startup:**
1. Open Terminal
2. Run: `cd dfx-checker && ./start.sh`
3. Browser opens automatically at localhost:8501

**AWS Credentials (needed for AI features):**
1. Go to [isengard.amazon.com](https://isengard.amazon.com)
2. Find account **286507431165**
3. Click **Temporary Credentials** > **bash/zsh**
4. Paste the export commands in your terminal
5. Credentials expire after a few hours - repeat when needed

**What works WITHOUT AWS credentials:**
- DXF drawing analysis
- CI Tracker (intake, pipeline, impact matrix)
- Custom rules and profiles
- BOM comparison
- PDF reports

**What NEEDS AWS credentials:**
- Image/photo analysis
- Vision inspection (GO/NO-GO)
- Semantic search
- DFM Agent analysis
- Drawing comparison AI analysis
- BOM Audit AI recommendations
    """)

with tab2:
    st.header("DFX Design Checker")
    st.subheader("Tutorial 1: Check a DXF Drawing")
    st.markdown("""
1. On the main page, select a **Manufacturing Process** from the sidebar (e.g., CNC Machining)
2. Select **DXF Drawing** as file type
3. Upload a .dxf file
4. The app automatically:
   - Counts all geometry (lines, circles, arcs)
   - Checks each feature against the process rules
   - Shows a color-coded markup (red=fail, orange=warning, green=pass)
   - Calculates a design score
5. Click **Download PDF Report** to save results

**Try it:** Use the test file `test_drawing.dxf` in the project folder
    """)
    st.subheader("Tutorial 2: Check an Image or Photo")
    st.markdown("""
1. Select a process (e.g., **Server/Hardware Assembly**)
2. Select **Image** as file type (or it auto-selects for Server mode)
3. Upload a photo (PNG, JPG)
4. AI analyzes the image against all rules
5. Results show with color-coded circles on the image marking findings
6. Download the PDF report

**Try it:** Take a photo of any hardware/server and upload it
    """)
    st.subheader("Tutorial 3: Custom Rules")
    st.markdown("""
1. In the sidebar, find **Custom Rules**
2. Click **Add Custom Rule** expander
3. Enter: name (e.g., Min screw torque), value (5), unit (in-lbs), type (minimum)
4. Click **Add Rule**
5. Your rule now appears in the sidebar and is checked in every AI analysis

**Bulk import:** Click **Bulk Import Rules (CSV)** to upload many rules at once.
Download the sample CSV first to see the format.

**Save profiles:** After setting rules, use **Rule Profiles** in the sidebar to save
as a named profile (e.g., Vendor A - CNC). Load it anytime.
    """)
    st.subheader("Tutorial 4: PDF and STEP Files")
    st.markdown("""
**PDF Drawings:**
1. Select **PDF Drawing** as file type
2. Upload a PDF
3. For multi-page PDFs, select which page to analyze
4. Click **Analyze this page with AI**

**STEP Files (3D CAD):**
1. Select **STEP File (3D)** as file type
2. Upload a .step or .stp file
3. App extracts volume, faces, edges, holes
4. Checks against process rules automatically

*Note: STEP analysis only works locally, not on the cloud version*
    """)

with tab3:
    st.header("Vision Inspection")
    st.subheader("Tutorial 5: GO/NO-GO Inspection")
    st.markdown("""
1. Select **Server/Hardware Assembly** as process
2. Select **Inspection Mode**
3. **Save a reference image:**
   - Select Upload new reference
   - Name it (e.g., Server-Gen3-Rev2)
   - Upload the approved/golden image
   - It saves permanently for reuse
4. **Upload production image** to inspect
5. Set the **Pass/Fail threshold** (default 80%)
6. Click **Run Inspection**
7. Results show:
   - Big green **GO** or red **NO-GO** banner
   - Defect list with severity (critical/major/minor)
   - Full inspection report
8. On FAIL: vendor email and SIM ticket text auto-generated
9. Check **Log to CI Tracker** to record the result
10. Download the inspection report PDF

**Try it:** Upload any two different images - set threshold to 99% to force a FAIL
    """)
    st.subheader("Tutorial 6: Compare Two Images")
    st.markdown("""
1. Select **Server/Hardware Assembly** > **Compare Two Images**
2. Upload Image A (reference) and Image B (current)
3. AI compares both and reports:
   - Differences found
   - Which image is better per rule
   - Scores for both
   - Recommendations
4. Download comparison report
    """)

with tab4:
    st.header("CI Tracker")
    st.subheader("Tutorial 7: Submit a CI")
    st.markdown("""
1. Go to **CI Tracker** page (sidebar)
2. Click **CI Intake** tab
3. Fill in the form:
   - Title and description of the issue
   - Category (Cable Management, Thermal, etc.)
   - Platform and generation
   - Vendor
   - Impact and effort estimates
   - FPY/cost impact if known
   - Upload photos if available
4. Click **Submit CI**
5. System auto-calculates priority score and recommends engineer level
    """)
    st.subheader("Tutorial 8: Manage the CI Pipeline")
    st.markdown("""
1. Go to **CI Pipeline** tab
2. Filter by status, platform, or vendor
3. Expand any CI to see full details
4. Update status: Intake > Assessment > Approved > In Progress > Validation > Closed
5. Assign to an engineer
6. Add notes for tracking
7. See the **smart routing recommendation** (Quick Win, Major Project, etc.)
8. Use ticket buttons to generate vendor/design/email tickets
9. Override the resolver group if the auto-suggestion is wrong
    """)
    st.subheader("Tutorial 9: Impact Matrix")
    st.markdown("""
1. Go to **Impact Matrix** tab
2. See all open CIs plotted on Impact vs Effort chart
3. Quadrants:
   - **Quick Wins** (top-left): High impact, low effort - do these first
   - **Major Projects** (top-right): High impact, high effort - plan carefully
   - **Fill Ins** (bottom-left): Low impact, low effort - when bandwidth allows
   - **Reconsider** (bottom-right): Low impact, high effort - discuss before committing
4. Engineer routing table shows recommended assignment level
    """)
    st.subheader("Tutorial 10: Semantic Search")
    st.markdown("""
1. Go to **Semantic Search** tab
2. Type a natural language question, e.g.:
   - "thermal issues with cable routing near fans"
   - "Vendor A quality problems on Gen3"
   - "have we seen this EMI gasket issue before?"
3. AI searches all CIs, lessons learned, and inspection history
4. Returns matching records, patterns, cross-platform applicability, and recommendations

*Requires AWS credentials*
    """)
    st.subheader("Tutorial 11: Ticket Routing")
    st.markdown("""
1. Go to **Ticket Routing** tab
2. Configure which resolver group handles each CI category
3. Set default severity per category
4. Add SIM folder UUIDs when ready for auto-ticket creation
5. These settings are used by the smart routing in the Pipeline tab
    """)

with tab5:
    st.header("DFM Optimizer Agent")
    st.subheader("Tutorial 12: Auto-Analyze CIs")
    st.markdown("""
1. Go to **DFM Agent** page (sidebar)
2. Click **Auto-Analyze CIs** tab
3. Click **Analyze All Unanalyzed CIs**
4. Agent processes each CI and provides:
   - Validated impact/effort (may differ from submitter estimate)
   - Similar CIs in the system
   - Cross-platform applicability
   - FPY and cost impact estimates
   - Recommended priority and next action
   - Risk and success factors

*Requires AWS credentials and at least 1 CI submitted*
    """)
    st.subheader("Tutorial 13: Pattern Recognition")
    st.markdown("""
1. Go to **Pattern Recognition** tab
2. Click **Run Pattern Analysis**
3. Agent scans all CIs for:
   - Recurring issues
   - Vendor-specific patterns
   - Platform-specific patterns
   - Category clusters
   - Systemic root causes

*Best with 5+ CIs for meaningful patterns*
    """)
    st.subheader("Tutorial 14: Cross-Platform Intelligence")
    st.markdown("""
1. Go to **Cross-Platform Intel** tab
2. Click **Run Cross-Platform Analysis**
3. Agent identifies:
   - Solutions from one platform applicable to others
   - Unreported issues likely on other platforms
   - Vendor fixes to apply everywhere
   - Generational improvements to carry forward

*Best with CIs across multiple platforms*
    """)

with tab6:
    st.header("Drawing & BOM Compare")
    st.subheader("Tutorial 15: Compare Drawing Revisions")
    st.markdown("""
1. Go to **Drawing & BOM Compare** page (sidebar)
2. Click **Drawing Compare** tab
3. Upload **Before** file(s) on the left
4. Upload **After** file(s) on the right
5. Supports: DXF, PNG, JPG, PDF (multi-page)
6. For multi-page PDFs, all pages are extracted and shown
7. Click **Analyze All Pages**
8. For each page, AI provides:
   - All changes found with before/after values
   - **Manufacturing impact** per change (tooling, fixtures, CNC, assembly)
   - **Cost and cycle time estimates** per change and total for 1000 units
   - **ECN requirements** (formal ECN, work instructions, training)
   - Revision cloud markup on the After drawing
9. Click **Download Full Report** for a PDF with all pages and markup

**Multi-file support:** Upload multiple files on each side (e.g., pages 1-5).
Files are matched 1-to-1 (file 1 vs file 1, etc.)

**Try it:** Upload two versions of any drawing or document
    """)

with tab7:
    st.header("BOM Tools")
    st.subheader("Tutorial 16: Compare Two BOMs")
    st.markdown("""
1. Go to **Drawing & BOM Compare** > **BOM Compare** tab
2. Upload Before BOM (CSV) and After BOM (CSV)
3. CSV should have columns: Part Number, Description, Quantity
4. Optional columns: Vendor, Unit Cost, Revision
5. App shows:
   - Added parts (new in After)
   - Removed parts (missing from After)
   - Modified parts (changed values)
   - Cost impact if Unit Cost and Quantity columns exist
6. Download BOM comparison report
    """)
    st.subheader("Tutorial 17: BOM Audit")
    st.markdown("""
1. Go to **Drawing & BOM Compare** > **BOM Audit** tab
2. Review the built-in rules (or add custom rules)
3. Upload a vendor BOM (CSV)
4. App automatically checks:
   - Part numbers present and unique
   - Descriptions present
   - Quantities valid
   - Unit cost, vendor, revision, UOM columns
5. Shows audit score with errors/warnings/passed
6. Click **Get AI Recommendations** for:
   - Compliance assessment
   - Specific fix instructions per issue
   - Missing information for production-ready BOM
   - Risk assessment if released as-is

**Try it:** Create a simple CSV with columns: Part Number, Description, Quantity
Leave some fields blank to see the audit catch them.
    """)
    st.subheader("Sample BOM CSV Format")
    st.code("Part Number,Description,Quantity,Vendor,Unit Cost\nPN-001,M3 Screw,24,FastenerCo,0.05\nPN-002,PCB Main Board,1,BoardMfg,45.00\nPN-003,Heat Sink,2,,12.50\nPN-004,,1,CableCo,3.25", language="csv")
    st.write("Note: Row 3 is missing Vendor, Row 4 is missing Description - the audit will catch these.")
