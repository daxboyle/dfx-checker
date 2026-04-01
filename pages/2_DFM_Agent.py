import streamlit as st
import json
import os
import datetime

st.set_page_config(page_title="DFM Optimizer Agent", page_icon="\U0001f916", layout="wide")
st.title("DFM Optimizer Agent")
st.write("Automated CI analysis, pattern recognition, and cross-platform recommendations.")

DATA_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CI_FILE = os.path.join(DATA_DIR, "ci_tracker.json")
AGENT_FILE = os.path.join(DATA_DIR, "agent_analysis.json")


def load_ci():
    if os.path.exists(CI_FILE):
        with open(CI_FILE, "r") as f:
            return json.load(f)
    return {"cis": [], "lessons": []}


def load_agent_data():
    if os.path.exists(AGENT_FILE):
        with open(AGENT_FILE, "r") as f:
            return json.load(f)
    return {"analyses": [], "patterns": [], "recommendations": []}


def save_agent_data(data):
    with open(AGENT_FILE, "w") as f:
        json.dump(data, f, indent=2)


ci_data = load_ci()
agent_data = load_agent_data()
cis = ci_data.get("cis", [])

tab1, tab2, tab3, tab4 = st.tabs(["Auto-Analyze CIs", "Pattern Recognition", "Cross-Platform Intel", "Agent History"])

with tab1:
    st.subheader("Automated CI Analysis")
    st.write("Select CIs to run through the DFM Optimizer Agent for automated impact assessment.")

    unanalyzed = [c for c in cis if "CI-" + str(c.get("id")) not in [a.get("ci_id") for a in agent_data.get("analyses", [])]]
    analyzed = [c for c in cis if "CI-" + str(c.get("id")) in [a.get("ci_id") for a in agent_data.get("analyses", [])]]

    col_m1, col_m2 = st.columns(2)
    col_m1.metric("Unanalyzed CIs", len(unanalyzed))
    col_m2.metric("Analyzed CIs", len(analyzed))

    if unanalyzed and st.button("Analyze All Unanalyzed CIs", type="primary"):
        import boto3
        client = boto3.client("bedrock-runtime", region_name="us-west-2")
        progress = st.progress(0)
        for idx, ci in enumerate(unanalyzed):
            with st.spinner("Analyzing CI-" + str(ci["id"]) + "..."):
                all_cis_text = ""
                for c in cis:
                    all_cis_text += "CI-" + str(c.get("id")) + ": " + c.get("title", "") + " | "
                    all_cis_text += "Category: " + c.get("category", "") + " | "
                    all_cis_text += "Platform: " + c.get("platform", "") + " " + c.get("generation", "") + " | "
                    all_cis_text += "Vendor: " + c.get("vendor", "") + " | "
                    all_cis_text += "Impact: " + c.get("impact", "") + " | "
                    all_cis_text += "Description: " + c.get("description", "")[:200] + "\n"

                prompt = "You are a Manufacturing DFM Optimizer Agent.\n\n"
                prompt += "Analyze this CI submission and provide automated assessment:\n\n"
                prompt += "CI-" + str(ci["id"]) + ":\n"
                prompt += "Title: " + ci.get("title", "") + "\n"
                prompt += "Description: " + ci.get("description", "") + "\n"
                prompt += "Category: " + ci.get("category", "") + "\n"
                prompt += "Platform: " + ci.get("platform", "") + " " + ci.get("generation", "") + "\n"
                prompt += "Vendor: " + ci.get("vendor", "") + "\n"
                prompt += "Submitter Impact Estimate: " + ci.get("impact", "") + "\n"
                prompt += "Submitter Effort Estimate: " + ci.get("effort", "") + "\n"
                prompt += "FPY Impact: " + ci.get("fpy_impact", "") + "\n"
                prompt += "Cost Impact: " + ci.get("cost_impact", "") + "\n\n"
                prompt += "ALL OTHER CIs IN SYSTEM (for context):\n" + all_cis_text + "\n\n"
                prompt += "Provide your analysis as JSON in triple-backtick json fence:\n"
                prompt += '{"validated_impact": "Critical/High/Medium/Low", "validated_effort": "Very High/High/Medium/Low", '
                prompt += '"impact_reasoning": "why this impact level", "effort_reasoning": "why this effort level", '
                prompt += '"similar_cis": ["CI-X", "CI-Y"], "similarity_explanation": "how they relate", '
                prompt += '"cross_platform_applicable": true/false, "applicable_platforms": ["list"], '
                prompt += '"estimated_fpy_impact": "+X%", "estimated_cost_impact": "$X/unit", '
                prompt += '"recommended_priority": 1-25, "recommended_action": "what to do next", '
                prompt += '"risk_factors": ["list of risks"], "success_factors": ["list of success factors"]}\n\n'
                prompt += "After JSON, provide a brief narrative summary."

                body_data = {"anthropic_version": "bedrock-2023-05-31", "max_tokens": 3000,
                    "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}]}
                response = client.invoke_model(modelId="anthropic.claude-3-haiku-20240307-v1:0", body=json.dumps(body_data))
                result = json.loads(response["body"].read())
                analysis_text = result["content"][0]["text"]

                parsed = {}
                try:
                    jm = chr(96)*3 + "json"
                    js = analysis_text.find(jm)
                    if js >= 0:
                        je = analysis_text.find(chr(96)*3, js + len(jm))
                        if je >= 0:
                            parsed = json.loads(analysis_text[js + len(jm):je].strip())
                except Exception:
                    pass

                narrative = analysis_text
                try:
                    jm = chr(96)*3 + "json"
                    js = analysis_text.find(jm)
                    if js >= 0:
                        je = analysis_text.find(chr(96)*3, js + len(jm))
                        if je >= 0:
                            narrative = analysis_text[je + 3:].strip()
                except Exception:
                    pass

                agent_data.setdefault("analyses", []).append({
                    "ci_id": "CI-" + str(ci["id"]),
                    "timestamp": datetime.datetime.now().isoformat(),
                    "parsed": parsed,
                    "narrative": narrative,
                })
                save_agent_data(agent_data)

            progress.progress((idx + 1) / len(unanalyzed))
        st.success("Analyzed " + str(len(unanalyzed)) + " CIs!")
        st.rerun()

    # Show analyses
    st.subheader("Analysis Results")
    for analysis in reversed(agent_data.get("analyses", [])):
        ci_id = analysis.get("ci_id", "?")
        parsed = analysis.get("parsed", {})
        with st.expander(ci_id + " - Validated Impact: " + parsed.get("validated_impact", "?") + " | Priority: " + str(parsed.get("recommended_priority", "?"))):
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                st.write("**Validated Impact:** " + parsed.get("validated_impact", "N/A"))
                st.write("**Reasoning:** " + parsed.get("impact_reasoning", "N/A"))
                st.write("**Est. FPY Impact:** " + parsed.get("estimated_fpy_impact", "N/A"))
                st.write("**Est. Cost Impact:** " + parsed.get("estimated_cost_impact", "N/A"))
            with col_a2:
                st.write("**Validated Effort:** " + parsed.get("validated_effort", "N/A"))
                st.write("**Reasoning:** " + parsed.get("effort_reasoning", "N/A"))
                st.write("**Recommended Priority:** " + str(parsed.get("recommended_priority", "N/A")))
                st.write("**Cross-Platform:** " + str(parsed.get("cross_platform_applicable", "N/A")))
            if parsed.get("similar_cis"):
                st.write("**Similar CIs:** " + ", ".join(parsed.get("similar_cis", [])))
                st.write("**Similarity:** " + parsed.get("similarity_explanation", ""))
            if parsed.get("applicable_platforms"):
                st.write("**Applicable Platforms:** " + ", ".join(parsed.get("applicable_platforms", [])))
            st.write("**Recommended Action:** " + parsed.get("recommended_action", "N/A"))
            if parsed.get("risk_factors"):
                st.write("**Risks:** " + ", ".join(parsed.get("risk_factors", [])))
            if analysis.get("narrative"):
                st.write("---")
                st.markdown(analysis["narrative"])

with tab2:
    st.subheader("Pattern Recognition")
    st.write("AI-identified patterns across all CIs.")

    if cis and st.button("Run Pattern Analysis", type="primary"):
        import boto3
        with st.spinner("Analyzing patterns across all CIs..."):
            ci_text = ""
            for c in cis:
                ci_text += "CI-" + str(c.get("id")) + ": " + c.get("title", "") + " | "
                ci_text += "Cat: " + c.get("category", "") + " | "
                ci_text += "Platform: " + c.get("platform", "") + " " + c.get("generation", "") + " | "
                ci_text += "Vendor: " + c.get("vendor", "") + " | "
                ci_text += "Impact: " + c.get("impact", "") + " | "
                ci_text += "Status: " + c.get("status", "") + " | "
                ci_text += "Desc: " + c.get("description", "")[:150] + "\n"

            prompt = "You are a Manufacturing DFM Optimizer Agent performing pattern analysis.\n\n"
            prompt += "Here are all CIs in the system:\n" + ci_text + "\n\n"
            prompt += "Identify:\n"
            prompt += "1. RECURRING ISSUES - same problem appearing multiple times\n"
            prompt += "2. VENDOR PATTERNS - issues concentrated with specific vendors\n"
            prompt += "3. PLATFORM PATTERNS - issues specific to certain platforms/generations\n"
            prompt += "4. CATEGORY CLUSTERS - related issues that should be addressed together\n"
            prompt += "5. SYSTEMIC ISSUES - problems that indicate a deeper root cause\n\n"
            prompt += "For each pattern, provide: description, affected CIs, severity, and recommended systemic fix.\n"
            prompt += "If there are too few CIs to identify patterns, say so."

            client = boto3.client("bedrock-runtime", region_name="us-west-2")
            body_data = {"anthropic_version": "bedrock-2023-05-31", "max_tokens": 3000,
                "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}]}
            response = client.invoke_model(modelId="anthropic.claude-3-haiku-20240307-v1:0", body=json.dumps(body_data))
            result = json.loads(response["body"].read())
            patterns = result["content"][0]["text"]

            agent_data["patterns"] = [{"timestamp": datetime.datetime.now().isoformat(), "analysis": patterns, "ci_count": len(cis)}]
            save_agent_data(agent_data)

        st.markdown(patterns)

    elif agent_data.get("patterns"):
        latest = agent_data["patterns"][-1]
        st.write("*Last analysis: " + latest.get("timestamp", "")[:19] + " (" + str(latest.get("ci_count", 0)) + " CIs)*")
        st.markdown(latest.get("analysis", ""))
    else:
        st.info("Submit some CIs first, then run pattern analysis.")

with tab3:
    st.subheader("Cross-Platform Intelligence")
    st.write("Identify solutions from one platform that could apply to others.")

    if cis and st.button("Run Cross-Platform Analysis", type="primary"):
        import boto3
        with st.spinner("Analyzing cross-platform opportunities..."):
            ci_text = ""
            for c in cis:
                ci_text += "CI-" + str(c.get("id")) + ": " + c.get("title", "") + " | "
                ci_text += "Platform: " + c.get("platform", "") + " " + c.get("generation", "") + " | "
                ci_text += "Vendor: " + c.get("vendor", "") + " | "
                ci_text += "Status: " + c.get("status", "") + " | "
                ci_text += "Outcome: " + c.get("outcome", "") + " | "
                ci_text += "Desc: " + c.get("description", "")[:150] + "\n"

            prompt = "You are a Manufacturing DFM Optimizer Agent focused on cross-platform leverage.\n\n"
            prompt += "Here are all CIs:\n" + ci_text + "\n\n"
            prompt += "Identify:\n"
            prompt += "1. SOLUTIONS that were implemented on one platform that could benefit others\n"
            prompt += "2. ISSUES on one platform that likely exist on others but have not been reported\n"
            prompt += "3. VENDOR-SPECIFIC fixes that should be applied across all platforms that vendor supplies\n"
            prompt += "4. GENERATIONAL improvements that should carry forward to next gen\n\n"
            prompt += "For each opportunity: describe it, list source and target platforms, estimate effort to transfer, and estimate impact.\n"
            prompt += "If there are too few CIs or platforms to identify cross-platform opportunities, say so."

            client = boto3.client("bedrock-runtime", region_name="us-west-2")
            body_data = {"anthropic_version": "bedrock-2023-05-31", "max_tokens": 3000,
                "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}]}
            response = client.invoke_model(modelId="anthropic.claude-3-haiku-20240307-v1:0", body=json.dumps(body_data))
            result = json.loads(response["body"].read())
            cross_plat = result["content"][0]["text"]

            agent_data["recommendations"] = [{"timestamp": datetime.datetime.now().isoformat(), "analysis": cross_plat, "ci_count": len(cis)}]
            save_agent_data(agent_data)

        st.markdown(cross_plat)

    elif agent_data.get("recommendations"):
        latest = agent_data["recommendations"][-1]
        st.write("*Last analysis: " + latest.get("timestamp", "")[:19] + " (" + str(latest.get("ci_count", 0)) + " CIs)*")
        st.markdown(latest.get("analysis", ""))
    else:
        st.info("Submit CIs across multiple platforms, then run cross-platform analysis.")

with tab4:
    st.subheader("Agent History")
    analyses = agent_data.get("analyses", [])
    st.write("**Total CI analyses:** " + str(len(analyses)))
    st.write("**Pattern analyses run:** " + str(len(agent_data.get("patterns", []))))
    st.write("**Cross-platform analyses run:** " + str(len(agent_data.get("recommendations", []))))

    if analyses:
        st.subheader("Analysis Summary")
        for a in reversed(analyses):
            p = a.get("parsed", {})
            st.write("- **" + a.get("ci_id", "?") + "** | Impact: " + p.get("validated_impact", "?") + " | Priority: " + str(p.get("recommended_priority", "?")) + " | " + a.get("timestamp", "")[:19])

    if st.button("Clear All Agent Data"):
        save_agent_data({"analyses": [], "patterns": [], "recommendations": []})
        st.success("Cleared!")
        st.rerun()
