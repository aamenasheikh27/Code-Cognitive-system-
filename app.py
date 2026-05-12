import os
import tempfile
import streamlit as st

from modules.parser import parse_python_file
from modules.summary_module import generate_code_summary
from modules.cognitive import compute_confidence, get_analogy, UserModel, generate_cognitive_explanation, generate_comparison_explanation
from modules.nlp_module import summarize_function, detect_intent, find_function, generate_nlp_explanation, detect_system_type
from modules.dependency import build_dependency_graph, build_failure_impact_graph
from modules.metrics import generate_metrics, simulate_failure_impact
from modules.llm_module import answer_code_question_with_gemini

plotly_config = {
    "displayModeBar": True,
    "displaylogo": False,
    "modeBarButtonsToRemove": [
        "select2d",
        "lasso2d",
        "autoScale2d",
        "toggleSpikelines"
    ]
}
st.set_page_config(
    page_title="Code Cognitive System",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS ---
st.markdown("""
<style>
/* Base theme variables */
:root {
    --bg-dark: #0B0E14;
    --card-bg: #111827;
    --card-border: #1F2937;
    --accent-cyan: #06B6D4;
    --accent-green: #10B981;
    --accent-red: #EF4444;
    --accent-orange: #F59E0B;
    --accent-blue: #3B82F6;
    --text-main: #E2E8F0;
    --text-muted: #94A3B8;
}

.stApp { background-color: var(--bg-dark); }

/* Custom Tabs override */
div[data-testid="stTabs"] button {
    background-color: transparent !important;
    border: 1px solid #1E293B !important;
    border-radius: 20px !important;
    color: #94A3B8 !important;
    padding: 6px 16px !important;
    margin-right: 8px !important;
    transition: all 0.3s ease;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
    border-color: #06B6D4 !important;
    color: #06B6D4 !important;
    background-color: rgba(6, 182, 212, 0.1) !important;
    box-shadow: 0 0 10px rgba(6, 182, 212, 0.2);
}

/* Header */
.main-header {
    display: flex; justify-content: space-between; align-items: center;
    padding-bottom: 20px; border-bottom: 1px solid var(--card-border); margin-bottom: 20px;
}
.header-left { display: flex; align-items: center; gap: 15px; }
.app-logo {
    width: 48px; height: 48px; background: linear-gradient(135deg, #06B6D4, #3B82F6);
    border-radius: 12px; display: flex; align-items: center; justify-content: center;
    font-size: 24px; box-shadow: 0 0 15px rgba(6, 182, 212, 0.4); color: white;
}
.header-title { margin: 0; font-size: 1.8rem; font-weight: 700; color: var(--text-main); }
.header-subtitle { margin: 0; font-size: 0.9rem; color: var(--accent-cyan); text-transform: uppercase; letter-spacing: 1px; }
.status-badge {
    background: rgba(16, 185, 129, 0.1); color: var(--accent-green);
    border: 1px solid rgba(16, 185, 129, 0.2); padding: 6px 12px; border-radius: 20px;
    font-size: 0.85rem; font-weight: 600; box-shadow: 0 0 10px rgba(16, 185, 129, 0.2);
}
.status-badge-waiting {
    background: rgba(245, 158, 11, 0.1); color: var(--accent-orange);
    border: 1px solid rgba(245, 158, 11, 0.2); padding: 6px 12px; border-radius: 20px;
    font-size: 0.85rem; font-weight: 600;
}

/* File Info Bar */
.file-info-bar {
    background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 8px;
    padding: 12px 20px; display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 24px; color: var(--text-muted); font-size: 0.95rem;
}
.file-info-name { color: var(--text-main); font-weight: 600; display: flex; align-items: center; gap: 8px; }

/* Cards */
.modern-card {
    background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 12px;
    padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
}
.card-title { font-size: 1.1rem; font-weight: 600; color: var(--text-main); margin-bottom: 15px; display: flex; align-items: center; gap: 8px; }

/* Metric Cards */
.metric-container { display: flex; flex-direction: column; }
.metric-label { font-size: 0.85rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 5px; }
.metric-value { font-size: 2.2rem; font-weight: 700; color: var(--accent-cyan); }

/* Summary Card */
.summary-card {
    background: linear-gradient(145deg, #111827, #0F172A); border: 1px solid var(--card-border);
    border-left: 4px solid var(--accent-cyan); border-radius: 12px; padding: 20px; margin-bottom: 20px;
}
.hl-cyan { color: var(--accent-cyan); font-weight: 600; }
.hl-red { color: var(--accent-red); font-weight: 600; }

/* Pipeline */
.pipeline-step { display: flex; align-items: center; margin-bottom: 12px; }
.pipeline-dot { width: 12px; height: 12px; border-radius: 50%; background-color: var(--accent-green); margin-right: 12px; box-shadow: 0 0 8px rgba(16,185,129,0.5); }
.pipeline-text { color: var(--text-main); font-size: 0.95rem; }

/* Badges */
.badge { padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: 500; display: inline-block; margin: 2px; }
.badge-green { background: rgba(16, 185, 129, 0.1); color: var(--accent-green); border: 1px solid rgba(16, 185, 129, 0.2); }
.badge-red { background: rgba(239, 68, 68, 0.1); color: var(--accent-red); border: 1px solid rgba(239, 68, 68, 0.2); }
.badge-orange { background: rgba(245, 158, 11, 0.1); color: var(--accent-orange); border: 1px solid rgba(245, 158, 11, 0.2); }
.badge-cyan { background: rgba(6, 182, 212, 0.1); color: var(--accent-cyan); border: 1px solid rgba(6, 182, 212, 0.2); }
.badge-gray { background: rgba(148, 163, 184, 0.1); color: var(--text-muted); border: 1px solid rgba(148, 163, 184, 0.2); }

/* Progress bar */
.progress-bg { width: 100%; height: 8px; background: #1E293B; border-radius: 4px; margin-top: 10px; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #06B6D4, #3B82F6); border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# --- State Initialization ---
if "user_model" not in st.session_state:
    st.session_state.user_model = UserModel()
if "parsed" not in st.session_state:
    st.session_state.parsed = None
if "parsed_b" not in st.session_state:
    st.session_state.parsed_b = None
if "name_a" not in st.session_state:
    st.session_state.name_a = ""
if "name_b" not in st.session_state:
    st.session_state.name_b = ""
if "lines_a" not in st.session_state:
    st.session_state.lines_a = 0
if "lines_b" not in st.session_state:
    st.session_state.lines_b = 0
if "failure_sim" not in st.session_state:
    st.session_state.failure_sim = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Header Section ---
status_html = '<div class="status-badge">🟢 Analyzed</div>' if st.session_state.parsed else '<div class="status-badge-waiting">⏳ Waiting for upload</div>'
st.markdown(f"""
<div class="main-header">
    <div class="header-left">
        <div class="app-logo">🧠</div>
        <div>
            <div class="header-title">Code Cognitive System</div>
            <div class="header-subtitle">AI-Powered Code Understanding</div>
        </div>
    </div>
    <div>{status_html}</div>
</div>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.markdown('<div style="font-size: 1.2rem; font-weight: 600; color: #E2E8F0; margin-bottom: 15px;">📁 Upload Code</div>', unsafe_allow_html=True)
    mode = st.radio("Mode", ["Single File Analysis", "Compare Files"], label_visibility="collapsed")
    st.write("")

    if mode == "Single File Analysis":
        uploaded = st.file_uploader("Choose a Python file", type=["py"])
        if uploaded:
            content = uploaded.read()
            st.session_state.lines_a = len(content.splitlines())
            with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            st.session_state.parsed = parse_python_file(tmp_path)
            st.session_state.name_a = uploaded.name

            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    else:
        uploaded_a = st.file_uploader("Choose File A", type=["py"], key="file_a")
        uploaded_b = st.file_uploader("Choose File B", type=["py"], key="file_b")
        
        if uploaded_a and uploaded_b:
            cont_a = uploaded_a.read()
            cont_b = uploaded_b.read()
            st.session_state.lines_a = len(cont_a.splitlines())
            st.session_state.lines_b = len(cont_b.splitlines())
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as tmp_a:
                tmp_a.write(cont_a)
                tmp_path_a = tmp_a.name
            with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as tmp_b:
                tmp_b.write(cont_b)
                tmp_path_b = tmp_b.name
                
            st.session_state.parsed = parse_python_file(tmp_path_a)
            st.session_state.parsed_b = parse_python_file(tmp_path_b)
            st.session_state.name_a = uploaded_a.name
            st.session_state.name_b = uploaded_b.name
            
            if os.path.exists(tmp_path_a): os.remove(tmp_path_a)
            if os.path.exists(tmp_path_b): os.remove(tmp_path_b)

    st.markdown("<hr style='border-color: #1F2937;'>", unsafe_allow_html=True)
    if st.button("Reset Session", use_container_width=True):
        st.session_state.parsed = None
        st.session_state.parsed_b = None
        st.session_state.failure_sim = None
        st.rerun()

# --- Main App Logic ---
if mode == "Single File Analysis":
    if st.session_state.parsed:
        parsed = st.session_state.parsed
        metrics = generate_metrics(parsed)
        intent = detect_system_type(parsed)
        
        # File Info Bar
        st.markdown(f"""
        <div class="file-info-bar">
            <div class="file-info-name">📄 {st.session_state.name_a}</div>
            <div>
                <span>{len(parsed.get('functions', []))} functions</span> &nbsp;·&nbsp;
                <span>{len(parsed.get('classes', []))} classes</span> &nbsp;·&nbsp;
                <span>{st.session_state.lines_a} lines</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        tabs = st.tabs([
            "Overview", 
            "Dependency Graph", 
            "Metrics", 
            "Cognitive Summary", 
            "Failure Simulation", 
            "Ask Questions"
        ])

        # --- TAB 1: OVERVIEW ---
        with tabs[0]:
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(f"""
                <div class="modern-card metric-container">
                    <div class="metric-label">🧩 Functions</div>
                    <div class="metric-value">{len(parsed.get('functions', []))}</div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div class="modern-card metric-container">
                    <div class="metric-label">📦 Classes</div>
                    <div class="metric-value" style="color: #10B981;">{len(parsed.get('classes', []))}</div>
                </div>
                """, unsafe_allow_html=True)
            with c3:
                risk_count = len(metrics.get("risk_functions", []))
                st.markdown(f"""
                <div class="modern-card metric-container">
                    <div class="metric-label">⚠️ Risk Score</div>
                    <div class="metric-value" style="color: #EF4444;">{risk_count}</div>
                </div>
                """, unsafe_allow_html=True)
            with c4:
                mod_score = metrics['modularity']['score']
                st.markdown(f"""
                <div class="modern-card metric-container">
                    <div class="metric-label">🧱 Modularity</div>
                    <div class="metric-value" style="color: #F59E0B;">{mod_score}%</div>
                </div>
                """, unsafe_allow_html=True)

            colA, colB = st.columns([2, 1])
            with colA:
                central_func = metrics.get('central_function', 'None')
                risk_func = metrics['risk_functions'][0]['name'] if metrics.get('risk_functions') else 'None'
                main_flow = " → ".join(metrics.get('main_flow', [])) if metrics.get('main_flow') else 'No clear flow'
                
                st.markdown(f"""
                <div class="summary-card">
                    <div class="card-title">📝 Summary</div>
                    <p style="color: #E2E8F0; font-size: 0.95rem; line-height: 1.6;">
                        <strong>Code Intent:</strong> {intent}<br><br>
                        <strong>Central Entry Function:</strong> <span class="hl-cyan">{central_func}()</span><br>
                        <strong>Failure-sensitive Function:</strong> <span class="hl-red">{risk_func}()</span><br>
                        <strong>Critical Path:</strong> <span class="badge badge-cyan">{main_flow}</span><br><br>
                        This system primarily processes the workflow listed above, organized around the central function to manage execution logic.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
            with colB:
                st.markdown("""
                <div class="modern-card">
                    <div class="card-title">⚙️ Processing Pipeline</div>
                    <div class="pipeline-step"><div class="pipeline-dot"></div><div class="pipeline-text">Code Upload</div></div>
                    <div class="pipeline-step"><div class="pipeline-dot"></div><div class="pipeline-text">AST Parsing</div></div>
                    <div class="pipeline-step"><div class="pipeline-dot"></div><div class="pipeline-text">Dependency Graph</div></div>
                    <div class="pipeline-step"><div class="pipeline-dot"></div><div class="pipeline-text">Metrics Computation</div></div>
                    <div class="pipeline-step"><div class="pipeline-dot"></div><div class="pipeline-text">NLP Understanding</div></div>
                    <div class="pipeline-step"><div class="pipeline-dot"></div><div class="pipeline-text">Cognitive Reasoning</div></div>
                    <div class="pipeline-step"><div class="pipeline-dot"></div><div class="pipeline-text">Dashboard Output</div></div>
                </div>
                """, unsafe_allow_html=True)

        # --- TAB 2: DEPENDENCY GRAPH ---
        with tabs[1]:
            st.markdown('<div style="display: flex; justify-content: flex-end; margin-bottom: 10px;">', unsafe_allow_html=True)
            show_external = st.checkbox("Show external/library calls", value=False, key="dep_graph_ext")
            st.markdown('</div>', unsafe_allow_html=True)

            g1, g2 = st.columns([2.5, 1])
            with g1:
                st.markdown('<div class="modern-card" style="padding: 0; overflow: hidden;">', unsafe_allow_html=True)
                fig = build_dependency_graph(parsed, failure_sim=st.session_state.failure_sim, show_external=show_external)
                st.plotly_chart(fig, use_container_width=True, key="dependency_graph_main", config=plotly_config)
                st.markdown('</div>', unsafe_allow_html=True)
            with g2:
                st.markdown('<div class="modern-card">', unsafe_allow_html=True)
                st.markdown('<div class="card-title">📌 Graph Insights</div>', unsafe_allow_html=True)
                
                st.markdown(f'<div style="margin-bottom:10px;"><span class="metric-label">Central Function</span><br><span class="badge badge-cyan">{metrics.get("central_function", "None")}</span></div>', unsafe_allow_html=True)
                
                entry_pts = ", ".join(metrics.get("entry_points", [])) if metrics.get("entry_points") else "None"
                st.markdown(f'<div style="margin-bottom:10px;"><span class="metric-label">Entry Points</span><br><span class="badge badge-green">{entry_pts}</span></div>', unsafe_allow_html=True)
                
                c_path = " → ".join(metrics.get("critical_path", [])) if metrics.get("critical_path") else "None"
                st.markdown(f'<div style="margin-bottom:10px;"><span class="metric-label">Critical Path</span><br><div style="color:var(--text-main);font-size:0.9rem;margin-top:5px;">{c_path}</div></div>', unsafe_allow_html=True)
                
                iso = ", ".join(metrics.get("isolated_functions", [])) if metrics.get("isolated_functions") else "None"
                st.markdown(f'<div style="margin-bottom:10px;"><span class="metric-label">Isolated Functions</span><br><span class="badge badge-gray">{iso}</span></div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

        # --- TAB 3: METRICS ---
        with tabs[2]:
            m1, m2, m3 = st.columns(3)
            with m1:
                comp_pct = min(100, metrics['complexity']['score'] * 2)
                st.markdown(f"""
                <div class="modern-card">
                    <div class="card-title">🧠 Complexity</div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: #E2E8F0;">{metrics['complexity']['level']}</div>
                    <div style="font-size: 0.85rem; color: #94A3B8;">Raw Score: {metrics['complexity']['score']}</div>
                    <div class="progress-bg"><div class="progress-fill" style="width: {comp_pct}%;"></div></div>
                </div>
                """, unsafe_allow_html=True)
                
                risk_pct = min(100, len(metrics['risk_functions']) * 20)
                st.markdown(f"""
                <div class="modern-card">
                    <div class="card-title">⚠️ Risk Score</div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: #E2E8F0;">{len(metrics['risk_functions'])}</div>
                    <div style="font-size: 0.85rem; color: #94A3B8;">Functions Flagged</div>
                    <div class="progress-bg"><div class="progress-fill" style="width: {risk_pct}%; background: linear-gradient(90deg, #F59E0B, #EF4444);"></div></div>
                </div>
                """, unsafe_allow_html=True)

            with m2:
                coup_pct = min(100, metrics['coupling']['score'] * 30)
                st.markdown(f"""
                <div class="modern-card">
                    <div class="card-title">🔗 Coupling</div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: #E2E8F0;">{metrics['coupling']['level']}</div>
                    <div style="font-size: 0.85rem; color: #94A3B8;">Avg Outgoing: {metrics['coupling']['score']}</div>
                    <div class="progress-bg"><div class="progress-fill" style="width: {coup_pct}%;"></div></div>
                </div>
                """, unsafe_allow_html=True)
                
                inf = metrics['central_score']
                inf_pct = min(100, inf * 10)
                st.markdown(f"""
                <div class="modern-card">
                    <div class="card-title">🎯 Max Influence</div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: #E2E8F0;">{inf}</div>
                    <div style="font-size: 0.85rem; color: #94A3B8;">Edges on Central Node</div>
                    <div class="progress-bg"><div class="progress-fill" style="width: {inf_pct}%;"></div></div>
                </div>
                """, unsafe_allow_html=True)

            with m3:
                mod_pct = metrics['modularity']['score']
                st.markdown(f"""
                <div class="modern-card">
                    <div class="card-title">🧱 Modularity</div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: #E2E8F0;">{metrics['modularity']['level']}</div>
                    <div style="font-size: 0.85rem; color: #94A3B8;">Isolated Ratio: {mod_pct}%</div>
                    <div class="progress-bg"><div class="progress-fill" style="width: {mod_pct}%;"></div></div>
                </div>
                """, unsafe_allow_html=True)
                
                iso_count = metrics['modularity']['isolated_count']
                st.markdown(f"""
                <div class="modern-card">
                    <div class="card-title">🏝️ Isolated Functions</div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: #E2E8F0;">{iso_count}</div>
                    <div style="font-size: 0.85rem; color: #94A3B8;">Standalone Utilities</div>
                    <div class="progress-bg"><div class="progress-fill" style="width: {(iso_count / (len(parsed.get('functions', [])) or 1)) * 100}%; background: linear-gradient(90deg, #10B981, #06B6D4);"></div></div>
                </div>
                """, unsafe_allow_html=True)

        # --- TAB 4: COGNITIVE SUMMARY ---
        with tabs[3]:
            st.markdown('<div class="modern-card">', unsafe_allow_html=True)
            st.write(generate_cognitive_explanation(parsed))
            st.markdown('</div>', unsafe_allow_html=True)

        # --- TAB 5: FAILURE SIMULATION ---
        with tabs[4]:
            st.markdown('<div class="modern-card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">⚠️ Failure Simulation</div>', unsafe_allow_html=True)
            st.markdown('<p style="color: var(--text-muted);">Identify high-impact functions and visualize what happens if they fail or are modified incorrectly.</p>', unsafe_allow_html=True)
            
            functions = [f["name"] for f in parsed.get("functions", [])]
            
            col_drop, col_btn = st.columns([3, 1])
            with col_drop:
                selected_func = st.selectbox("Select a function to simulate failure:", ["None"] + functions, label_visibility="collapsed")
            with col_btn:
                sim_btn = st.button("Simulate Failure", use_container_width=True)
                
            if sim_btn or st.session_state.failure_sim is not None:
                if sim_btn and selected_func != "None":
                    st.session_state.failure_sim = simulate_failure_impact(parsed, selected_func)
                elif sim_btn and selected_func == "None":
                    st.session_state.failure_sim = None
                    
            if st.session_state.failure_sim:
                impact_data = st.session_state.failure_sim
                failed = impact_data["failed_function"]
                affected = impact_data["affected_functions"]
                count = impact_data["impact_count"]
                severity = impact_data["severity"]
                paths = impact_data["impact_paths"]
                
                sev_color = "#10B981" if severity == "No Impact" else "#F59E0B" if severity in ["Low", "Medium"] else "#EF4444"
                
                st.markdown(f"""
                <div style="background: rgba(17, 24, 39, 0.8); border: 1px solid #334155; border-left: 4px solid {sev_color}; border-radius: 8px; padding: 20px; margin-top: 20px; margin-bottom: 20px;">
                    <div style="font-size: 1.2rem; font-weight: 600; color: #E2E8F0; margin-bottom: 10px;">Impact Summary</div>
                    <div style="color: #94A3B8; font-size: 0.95rem; line-height: 1.6;">
                        <strong>Failed Function:</strong> <span style="color: #EF4444;">{failed}()</span><br>
                        <strong>Impact:</strong> {count} downstream functions affected<br>
                        <strong>Severity:</strong> <span style="color: {sev_color}; font-weight: 600;">{severity}</span><br>
                        <strong>Reason:</strong> If `{failed}()` fails or is modified incorrectly, it directly breaks its callers and propagates through the system.
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if paths:
                    st.markdown('<div style="font-size: 1.1rem; font-weight: 600; color: #E2E8F0; margin-bottom: 15px;">🔗 Impact Chain</div>', unsafe_allow_html=True)
                    for p in paths[:3]: # Max 3 paths to keep UI clean
                        chain_html = ' <span style="color: #64748B; font-weight: bold;">→</span> '.join([f'<span style="background: #1E293B; border: 1px solid #334155; padding: 6px 12px; border-radius: 6px; color: #E2E8F0;">{node}()</span>' for node in p])
                        st.markdown(f'<div style="margin-bottom: 12px; display: flex; align-items: center; gap: 8px; overflow-x: auto; padding-bottom: 5px;">{chain_html}</div>', unsafe_allow_html=True)
                        
                if affected:
                    st.markdown('<div style="font-size: 1.1rem; font-weight: 600; color: #E2E8F0; margin-top: 20px; margin-bottom: 10px;">⚠️ Affected Functions</div>', unsafe_allow_html=True)
                    badges_html = " ".join([f'<span class="badge badge-orange">{a}()</span>' for a in affected])
                    st.markdown(f'<div style="margin-bottom: 20px;">{badges_html}</div>', unsafe_allow_html=True)
                    
                unaffected = [f for f in functions if f not in affected and f != failed]
                if unaffected:
                    with st.expander("Show Unaffected Functions"):
                        unaffected_html = " ".join([f'<span class="badge badge-gray">{u}()</span>' for u in unaffected])
                        st.markdown(unaffected_html, unsafe_allow_html=True)
                
                if affected:
                    st.markdown('<div style="font-size: 1.1rem; font-weight: 600; color: #E2E8F0; margin-top: 20px; margin-bottom: 10px;">📊 Impact Table</div>', unsafe_allow_html=True)
                    st.dataframe(impact_data["impact_table"], use_container_width=True, hide_index=True)
                
                st.markdown('<div style="font-size: 1.1rem; font-weight: 600; color: #E2E8F0; margin-top: 30px; margin-bottom: 15px;">🕸️ Impact Graph</div>', unsafe_allow_html=True)
                
                show_full_graph = st.checkbox("Show full dependency graph", value=False, key=f"sim_full_graph_{failed}")
                
                st.markdown('<div style="margin-top: 10px;">', unsafe_allow_html=True)
                if show_full_graph:
                    # Pass the impact_data correctly to the full graph so it knows what to highlight
                    full_sim_format = {
                        "selected_function": failed,
                        "affected_functions": affected
                    }
                    fig_sim = build_dependency_graph(parsed, failure_sim=full_sim_format, show_external=False)
                    st.plotly_chart(fig_sim, use_container_width=True, key=f"failure_impact_full_{failed}", config=plotly_config)
                else:
                    fig_sim = build_failure_impact_graph(parsed, failed)
                    st.plotly_chart(fig_sim, use_container_width=True, key=f"failure_impact_{failed}", config=plotly_config)
                st.markdown('</div>', unsafe_allow_html=True)
                
            else:
                st.info("Select a function and click 'Simulate Failure' to see the visual impact.")
            st.markdown('</div>', unsafe_allow_html=True)

        # --- TAB 6: ASK QUESTIONS ---
        def build_llm_context(parsed, metrics, cognitive_summary, failure_data, intent):
            return {
                "parsed": parsed,
                "metrics": metrics,
                "cognitive_summary": cognitive_summary,
                "failure_sim": failure_data,
                "intent": intent
            }

        def get_local_fallback_answer(question, parsed, metrics, failure_data):
            q_lower = question.lower()
            if "workflow" in q_lower or "flow" in q_lower:
                return "Main workflow: " + (" → ".join(metrics.get("main_flow", [])) if metrics.get("main_flow") else "No strong path detected")
            elif "important" in q_lower or "central" in q_lower:
                return f"The most important function appears to be `{metrics.get('central_function')}()`."
            elif "risky" in q_lower or "risk" in q_lower or "failure" in q_lower or "impact" in q_lower:
                if metrics.get("risk_functions"):
                    names = ", ".join(f"`{item['name']}()`" for item in metrics.get("risk_functions", [])[:3])
                    return f"The main failure-sensitive functions are {names}. If they fail, multiple downstream functions break."
                else:
                    return "No major failure-sensitive functions were detected."
            elif "improve" in q_lower or "refactor" in q_lower:
                return "Consider reducing coupling on central functions, renaming vaguely named variables, and isolating high-risk functions."
            elif "explain" in q_lower or "simply" in q_lower:
                return generate_cognitive_explanation(parsed)
            else:
                try:
                    result = find_function(question, parsed)
                    if result["function"] != "No function found":
                        analogy = get_analogy(result["function"])
                        return (
                            f"**Most relevant function:** `{result['function']}`\n\n"
                            f"**Description:** {result['description']}\n\n"
                            f"**Analogy:** {analogy}"
                        )
                    else:
                        return "I could not generate a detailed answer, but the uploaded code has been parsed successfully."
                except Exception:
                    return "I could not generate a detailed answer, but the uploaded code has been parsed successfully."

        def handle_question(question):
            if not question or not question.strip():
                return

            st.session_state.chat_history.append({
                "role": "user",
                "content": question
            })

            context = build_llm_context(
                parsed=parsed,
                metrics=metrics,
                cognitive_summary=generate_cognitive_explanation(parsed),
                failure_data=st.session_state.failure_sim,
                intent=intent
            )

            answer, source, error = answer_code_question_with_gemini(question, context)

            if answer:
                final_answer = answer
                final_source = source
                final_error = None
            else:
                final_answer = get_local_fallback_answer(
                    question,
                    parsed,
                    metrics,
                    st.session_state.failure_sim
                )
                final_source = "local reasoning fallback"
                final_error = error

            if not final_answer:
                final_answer = "I could not generate a detailed response, but the code analysis is available in the dashboard."
                final_source = "local reasoning fallback"

            st.session_state.chat_history.append({
                "role": "assistant",
                "content": final_answer,
                "source": final_source,
                "error": final_error
            })

        with tabs[5]:
            st.markdown('<div class="modern-card">', unsafe_allow_html=True)
            st.markdown('<div class="card-title">💬 Ask About Your Code</div>', unsafe_allow_html=True)

            if os.getenv("GEMINI_API_KEY"):
                st.success("Gemini API key detected")
            else:
                st.warning("Gemini API key not detected. Using local fallback.")

            suggested_questions = [
                ("What is the main workflow?", "q_main_workflow"),
                ("Which function is most important?", "q_important_function"),
                ("Which function failure affects the system most?", "q_failure_impact"),
                ("Explain the code simply", "q_simple_explain"),
                ("How can this code be improved?", "q_improve_code"),
                ("Which function should be refactored first?", "q_refactor_first")
            ]

            cols = st.columns(3)
            for i, (q_text, q_key) in enumerate(suggested_questions):
                with cols[i % 3]:
                    if st.button(q_text, use_container_width=True, key=q_key):
                        handle_question(q_text)
                        st.rerun()

            st.markdown("<hr style='border-color: #334155;'>", unsafe_allow_html=True)
            
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])
                    if msg["role"] == "assistant":
                        st.caption(f"Answered using {msg.get('source', 'unknown')}")
                        if msg.get("error") and msg.get("source") == "local reasoning fallback":
                            with st.expander("Gemini debug info"):
                                st.write(msg["error"])

            user_question = st.chat_input("Ask anything about this code...")
            if user_question:
                handle_question(user_question)
                st.rerun()
                    
            st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.markdown("""
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 50vh; color: #94A3B8;">
            <div style="font-size: 4rem; margin-bottom: 20px;">📁</div>
            <h2 style="color: #E2E8F0;">No file uploaded yet</h2>
            <p>Upload a Python file from the sidebar to start cognitive analysis</p>
        </div>
        """, unsafe_allow_html=True)

elif mode == "Compare Files":
    if st.session_state.parsed and st.session_state.parsed_b:
        parsed_a = st.session_state.parsed
        parsed_b = st.session_state.parsed_b
        name_a = st.session_state.name_a
        name_b = st.session_state.name_b
        
        metrics_a = generate_metrics(parsed_a)
        metrics_b = generate_metrics(parsed_b)
        
        st.markdown('<h2 style="color: var(--text-main);">⚖️ Side-by-Side Comparison</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="modern-card">
                <div class="card-title">📄 {name_a}</div>
                <div style="margin-bottom:15px;"><span class="metric-label">Final Design Score</span><br><span style="color:#10B981; font-size:1.4rem; font-weight:700;">{metrics_a['design_metrics']['final_score']}/100</span></div>
                <div style="margin-bottom:15px;"><span class="metric-label">Complexity & Coupling</span><br><span style="color:#E2E8F0; font-size:1.1rem; font-weight:600;">{metrics_a['complexity']['score']} | {metrics_a['coupling']['score']} avg out</span></div>
                <div style="margin-bottom:15px;"><span class="metric-label">Useful Modularity</span><br><span style="color:#E2E8F0; font-size:1.1rem; font-weight:600;">{metrics_a['design_metrics']['useful_modul']}%</span></div>
                <div style="margin-bottom:15px;"><span class="metric-label">Naming Quality</span><br><span style="color:#E2E8F0; font-size:1.1rem; font-weight:600;">{metrics_a['design_metrics']['naming_quality']}%</span></div>
                <div style="margin-bottom:15px;"><span class="metric-label">Single Responsibility</span><br><span style="color:#E2E8F0; font-size:1.1rem; font-weight:600;">{metrics_a['design_metrics']['sr_score']}%</span></div>
                <div style="margin-bottom:15px;"><span class="metric-label">Dead Code Risk</span><br><span style="color:#EF4444; font-size:1.1rem; font-weight:600;">{metrics_a['design_metrics']['dead_code_risk']} penalty</span></div>
                <div style="margin-bottom:15px;"><span class="metric-label">Monolithic Risk</span><br><span style="color:#EF4444; font-size:1.1rem; font-weight:600;">{metrics_a['design_metrics']['monolithic_risk']} penalty</span></div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div class="modern-card">
                <div class="card-title">📄 {name_b}</div>
                <div style="margin-bottom:15px;"><span class="metric-label">Final Design Score</span><br><span style="color:#10B981; font-size:1.4rem; font-weight:700;">{metrics_b['design_metrics']['final_score']}/100</span></div>
                <div style="margin-bottom:15px;"><span class="metric-label">Complexity & Coupling</span><br><span style="color:#E2E8F0; font-size:1.1rem; font-weight:600;">{metrics_b['complexity']['score']} | {metrics_b['coupling']['score']} avg out</span></div>
                <div style="margin-bottom:15px;"><span class="metric-label">Useful Modularity</span><br><span style="color:#E2E8F0; font-size:1.1rem; font-weight:600;">{metrics_b['design_metrics']['useful_modul']}%</span></div>
                <div style="margin-bottom:15px;"><span class="metric-label">Naming Quality</span><br><span style="color:#E2E8F0; font-size:1.1rem; font-weight:600;">{metrics_b['design_metrics']['naming_quality']}%</span></div>
                <div style="margin-bottom:15px;"><span class="metric-label">Single Responsibility</span><br><span style="color:#E2E8F0; font-size:1.1rem; font-weight:600;">{metrics_b['design_metrics']['sr_score']}%</span></div>
                <div style="margin-bottom:15px;"><span class="metric-label">Dead Code Risk</span><br><span style="color:#EF4444; font-size:1.1rem; font-weight:600;">{metrics_b['design_metrics']['dead_code_risk']} penalty</span></div>
                <div style="margin-bottom:15px;"><span class="metric-label">Monolithic Risk</span><br><span style="color:#EF4444; font-size:1.1rem; font-weight:600;">{metrics_b['design_metrics']['monolithic_risk']} penalty</span></div>
            </div>
            """, unsafe_allow_html=True)

        score_a = metrics_a['design_metrics']['final_score']
        score_b = metrics_b['design_metrics']['final_score']
        
        if score_a > score_b:
            verdict = name_a
            winner, loser = metrics_a, metrics_b
            loser_name = name_b
        elif score_b > score_a:
            verdict = name_b
            winner, loser = metrics_b, metrics_a
            loser_name = name_a
        else:
            verdict = "Tie"
            winner, loser = metrics_a, metrics_b
            loser_name = name_b

        comp_exp = f"<ul style='margin-left: 20px;'><li>It separates components meaningfully, yielding a higher Single Responsibility score ({winner['design_metrics']['sr_score']}% vs {loser['design_metrics']['sr_score']}%).</li>"
        comp_exp += f"<li>It has clearer, more descriptive function names ({winner['design_metrics']['naming_quality']}% vs {loser['design_metrics']['naming_quality']}%).</li>"
        
        if loser['design_metrics']['monolithic_functions']:
            comp_exp += f"<li>It avoids monolithic design. The poorer file ({loser_name}) relies on monolithic functions like: <b>{', '.join(loser['design_metrics']['monolithic_functions'])}()</b>.</li>"
            
        if loser['design_metrics']['dead_code_functions']:
            comp_exp += f"<li>The poorer file has vague isolated functions like <b>{', '.join(loser['design_metrics']['dead_code_functions'])}()</b>, which the system correctly treats as dead/unclear code rather than good modularity.</li>"
            
        comp_exp += "</ul>"

        st.markdown(f"""
        <div class="summary-card" style="border-left-color: #10B981;">
            <div class="card-title">🏆 Verdict: Better Design</div>
            <div style="font-size: 1.2rem; color: #10B981; font-weight: 700; margin-bottom: 15px;">{verdict}</div>
            <div style="color: #E2E8F0; line-height: 1.6;">{comp_exp}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 50vh; color: #94A3B8;">
            <div style="font-size: 4rem; margin-bottom: 20px;">⚖️</div>
            <h2 style="color: #E2E8F0;">Upload 2 files to compare</h2>
            <p>Upload both Python files from the sidebar to begin comparison</p>
        </div>
        """, unsafe_allow_html=True)
