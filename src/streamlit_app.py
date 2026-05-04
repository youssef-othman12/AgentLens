import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json
from pathlib import Path
from html import escape


# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="AgentLens — Performance Intelligence",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# DEFAULT DOMAIN → MODELS MAPPING
# ============================================================
DEFAULT_DOMAIN_MODELS = {
    "Business Leadership": ["svm_business_adoption"],
    "Coding": [],
    "Customer Support": []
}


# ============================================================
# SESSION STATE
# ============================================================
if "domain_models" not in st.session_state:
    st.session_state.domain_models = {
        domain: models.copy()
        for domain, models in DEFAULT_DOMAIN_MODELS.items()
    }

if "history" not in st.session_state:
    st.session_state.history = []

if "comparison" not in st.session_state:
    st.session_state.comparison = []


# ============================================================
# CONFIG
# ============================================================
API_BASE = "http://localhost:8000"


# ============================================================
# HELPERS
# ============================================================
def check_api_status():
    try:
        r = requests.get(f"{API_BASE}/health", timeout=1)
        return r.status_code == 200
    except Exception:
        return False


def fetch_models_from_api():
    try:
        r = requests.get(f"{API_BASE}/models", timeout=2)
        return r.json().get("models", [])
    except Exception:
        return []


def h(value):
    """HTML escape helper."""
    return escape(str(value))


# ============================================================
# PROFESSIONAL CSS
# ============================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    :root {
        --bg: #f4f7fb;
        --surface: #ffffff;
        --surface-soft: #f8fafc;
        --surface-muted: #eef2f7;

        --primary: #2563eb;
        --primary-dark: #1e40af;
        --primary-soft: #dbeafe;

        --accent: #0f766e;
        --accent-soft: #ccfbf1;

        --success: #15803d;
        --success-soft: #dcfce7;

        --warning: #b45309;
        --warning-soft: #fef3c7;

        --danger: #b91c1c;
        --danger-soft: #fee2e2;

        --text: #0f172a;
        --text-muted: #475569;
        --text-light: #94a3b8;

        --border: #e2e8f0;
        --border-strong: #cbd5e1;

        --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.06);
        --shadow-md: 0 8px 24px rgba(15, 23, 42, 0.08);
        --shadow-lg: 0 18px 45px rgba(15, 23, 42, 0.12);
    }

    html, body {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: var(--text);
        background: var(--bg);
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(37, 99, 235, 0.08), transparent 28rem),
            radial-gradient(circle at top right, rgba(15, 118, 110, 0.08), transparent 26rem),
            var(--bg);
    }

    #MainMenu, footer, .stDeployButton {
        visibility: hidden;
    }

    .main .block-container {
        max-width: 1440px;
        padding-top: 1.6rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', sans-serif;
        color: var(--text);
        letter-spacing: -0.025em;
    }

    p {
        color: var(--text-muted);
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
        border-right: 1px solid var(--border);
    }

    section[data-testid="stSidebar"] .block-container {
        padding-top: 1.5rem;
        padding-left: 1.25rem;
        padding-right: 1.25rem;
    }

    .app-title {
        font-size: 2rem;
        font-weight: 750;
        color: var(--text);
        letter-spacing: -0.035em;
        margin-bottom: 0.2rem;
    }

    .app-subtitle {
        font-size: 0.96rem;
        color: var(--text-muted);
        margin-top: 0;
    }

    .section-label {
        font-size: 0.72rem;
        font-weight: 700;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.105em;
        margin-bottom: 0.65rem;
    }

    .card {
        background: rgba(255, 255, 255, 0.92);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: var(--shadow-sm);
        transition: all 0.18s ease;
    }

    .card:hover {
        border-color: var(--border-strong);
        box-shadow: var(--shadow-md);
        transform: translateY(-1px);
    }

    .badge {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.28rem 0.68rem;
        font-size: 0.74rem;
        font-weight: 650;
        border-radius: 999px;
        letter-spacing: 0.01em;
        line-height: 1;
    }

    .badge-success {
        background: var(--success-soft);
        color: var(--success);
        border: 1px solid #86efac;
    }

    .badge-warning {
        background: var(--warning-soft);
        color: var(--warning);
        border: 1px solid #fde68a;
    }

    .badge-error {
        background: var(--danger-soft);
        color: var(--danger);
        border: 1px solid #fecaca;
    }

    .badge-info {
        background: var(--primary-soft);
        color: var(--primary-dark);
        border: 1px solid #bfdbfe;
    }

    .badge-neutral {
        background: #f1f5f9;
        color: var(--text-muted);
        border: 1px solid var(--border);
    }

    .badge-accent {
        background: var(--accent-soft);
        color: var(--accent);
        border: 1px solid #99f6e4;
    }

    .result-panel {
        background:
            radial-gradient(circle at top right, rgba(255,255,255,0.22), transparent 15rem),
            linear-gradient(135deg, #0f172a 0%, #1e3a8a 52%, #2563eb 100%);
        border-radius: 20px;
        padding: 2rem;
        color: #ffffff;
        margin: 1.5rem 0;
        box-shadow: 0 24px 60px rgba(30, 64, 175, 0.28);
        position: relative;
        overflow: hidden;
    }

    .result-label {
        font-size: 0.72rem;
        color: rgba(255, 255, 255, 0.76);
        text-transform: uppercase;
        letter-spacing: 0.13em;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }

    .result-value {
        font-size: 2.8rem;
        font-weight: 800;
        letter-spacing: -0.04em;
        margin: 0.25rem 0;
        line-height: 1.05;
    }

    .result-confidence {
        font-size: 0.9rem;
        color: rgba(255, 255, 255, 0.86);
        font-family: 'JetBrains Mono', monospace;
        margin-top: 0.7rem;
    }

    .stButton > button {
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
        color: #ffffff !important;
        border: 1px solid var(--primary);
        border-radius: 10px;
        padding: 0.58rem 1.2rem;
        font-weight: 650;
        font-size: 0.88rem;
        transition: all 0.16s ease;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.18);
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 10px 22px rgba(37, 99, 235, 0.25);
        filter: brightness(1.03);
    }

    .stButton > button:active {
        transform: translateY(0);
    }

    .stButton > button:disabled {
        background: #e2e8f0 !important;
        color: #94a3b8 !important;
        border-color: var(--border) !important;
        box-shadow: none !important;
    }

    .stDownloadButton > button {
        background: #ffffff !important;
        color: var(--text) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px;
        font-weight: 650;
        box-shadow: var(--shadow-sm);
    }

    .stDownloadButton > button:hover {
        background: var(--primary-soft) !important;
        border-color: #93c5fd !important;
        color: var(--primary-dark) !important;
    }

    label,
    .stSelectbox label,
    .stSlider label,
    .stTextInput label,
    .stFileUploader label,
    .stRadio label {
        font-size: 0.82rem !important;
        font-weight: 650 !important;
        color: var(--text) !important;
    }

    /* Selectbox container */
    div[data-baseweb="select"] {
        font-family: 'Inter', sans-serif !important;
    }

    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border: 1px solid var(--border-strong) !important;
        border-radius: 10px !important;
        min-height: 42px !important;
        box-shadow: var(--shadow-sm);
    }

    div[data-baseweb="select"] > div:hover {
        border-color: var(--primary) !important;
    }

    div[data-baseweb="select"] > div:focus-within {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.14) !important;
    }

    /* This fixes selected dropdown text visibility */
    div[data-baseweb="select"] div,
    div[data-baseweb="select"] span {
        color: var(--text) !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
    }

    div[data-baseweb="select"] input {
        color: var(--text) !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
    }

    div[data-baseweb="select"] input::placeholder {
        color: var(--text-light) !important;
        opacity: 1 !important;
    }

    div[data-baseweb="popover"] {
        z-index: 999999 !important;
    }

    div[data-baseweb="menu"] {
        background: #ffffff !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        box-shadow: var(--shadow-lg) !important;
        padding: 0.35rem !important;
    }

    div[role="option"] {
        color: var(--text) !important;
        font-size: 0.9rem !important;
        border-radius: 8px !important;
    }

    div[role="option"]:hover {
        background: var(--primary-soft) !important;
        color: var(--primary-dark) !important;
    }

    .stTextInput input,
    .stNumberInput input,
    textarea {
        background: #ffffff !important;
        color: var(--text) !important;
        border: 1px solid var(--border-strong) !important;
        border-radius: 10px !important;
    }

    .stTextInput input:focus,
    .stNumberInput input:focus,
    textarea:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.14) !important;
    }

    .stSlider [data-baseweb="slider"] > div > div {
        background: var(--primary) !important;
    }

    .stSlider [role="slider"] {
        background: #ffffff !important;
        border: 3px solid var(--primary) !important;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.25);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.35rem;
        background: rgba(255, 255, 255, 0.65);
        border: 1px solid var(--border);
        padding: 0.35rem;
        border-radius: 14px;
        box-shadow: var(--shadow-sm);
    }

    .stTabs [data-baseweb="tab"] {
        height: 42px;
        padding: 0 1.15rem;
        background: transparent;
        border-radius: 10px;
        color: var(--text-muted);
        font-weight: 650;
        font-size: 0.88rem;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background: #f1f5f9;
        color: var(--text);
    }

    .stTabs [aria-selected="true"] {
        background: var(--primary) !important;
        color: #ffffff !important;
    }

    .stTabs [aria-selected="true"] p {
        color: #ffffff !important;
    }

    .streamlit-expanderHeader,
    [data-testid="stExpander"] details summary {
        background: #ffffff !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        font-weight: 650 !important;
        color: var(--text) !important;
        box-shadow: var(--shadow-sm);
    }

    .streamlit-expanderHeader:hover,
    [data-testid="stExpander"] details summary:hover {
        border-color: #93c5fd !important;
        background: #eff6ff !important;
    }

    div[data-testid="stExpander"] {
        border: none !important;
        box-shadow: none !important;
    }

    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.92);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 0.9rem 1.05rem;
        box-shadow: var(--shadow-sm);
    }

    [data-testid="stMetricValue"] {
        font-size: 1.55rem !important;
        font-weight: 800 !important;
        color: var(--text) !important;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.72rem !important;
        color: var(--text-muted) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        font-weight: 700 !important;
    }

    .stDataFrame {
        border: 1px solid var(--border);
        border-radius: 14px;
        overflow: hidden;
        box-shadow: var(--shadow-sm);
    }

    code {
        font-family: 'JetBrains Mono', monospace !important;
        background: #eff6ff !important;
        color: var(--primary-dark) !important;
        padding: 0.16rem 0.45rem !important;
        border-radius: 6px !important;
        font-size: 0.84em !important;
        font-weight: 600 !important;
    }

    .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 999px;
        margin-right: 7px;
        vertical-align: middle;
    }

    .dot-online {
        background: var(--success);
        box-shadow: 0 0 0 4px rgba(21, 128, 61, 0.15);
    }

    .dot-offline {
        background: var(--danger);
        box-shadow: 0 0 0 4px rgba(185, 28, 28, 0.15);
    }

    .stAlert {
        border-radius: 14px !important;
        border: 1px solid var(--border) !important;
    }

    .info-panel {
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        border-radius: 14px;
        padding: 1rem 1.15rem;
        color: var(--primary-dark);
        box-shadow: var(--shadow-sm);
    }

    .empty-state {
        background: rgba(255, 255, 255, 0.88);
        border: 1px dashed var(--border-strong);
        border-radius: 18px;
        padding: 3rem 2rem;
        text-align: center;
        color: var(--text-muted);
        box-shadow: var(--shadow-sm);
    }

    a {
        color: var(--primary-dark);
        text-decoration: none;
        font-weight: 650;
    }

    a:hover {
        color: var(--primary);
        text-decoration: underline;
    }

    hr {
        border-color: var(--border);
        margin: 1.35rem 0;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("""
    <div style="margin-bottom: 1.6rem;">
        <div style="
            background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 55%, #2563eb 100%);
            border-radius: 18px;
            padding: 1.15rem;
            box-shadow: 0 18px 36px rgba(30, 64, 175, 0.24);
        ">
            <div style="display: flex; align-items: center; gap: 0.75rem;">
                <div style="
                    width: 38px;
                    height: 38px;
                    background: rgba(255,255,255,0.16);
                    border: 1px solid rgba(255,255,255,0.25);
                    border-radius: 12px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: 800;
                    font-size: 1.05rem;
                ">
                    ◆
                </div>
                <div>
                    <div style="
                        font-size: 1.2rem;
                        font-weight: 800;
                        color: white;
                        letter-spacing: -0.035em;
                        line-height: 1;
                    ">
                        AgentLens
                    </div>
                    <div style="
                        font-size: 0.72rem;
                        color: rgba(255,255,255,0.72);
                        margin-top: 0.28rem;
                        font-weight: 500;
                    ">
                        Performance Intelligence
                    </div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    api_online = check_api_status()
    status_color = "dot-online" if api_online else "dot-offline"
    status_text = "Connected" if api_online else "Offline"

    st.markdown(f"""
    <div style="background: white; border: 1px solid #e2e8f0; border-radius: 14px;
                padding: 0.85rem 1rem; margin-bottom: 1.5rem;
                box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);">
        <div style="font-size: 0.68rem; color: #475569; text-transform: uppercase;
                    letter-spacing: 0.1em; font-weight: 700; margin-bottom: 0.35rem;">
            API Status
        </div>
        <div style="font-size: 0.9rem; font-weight: 650; color: #0f172a;">
            <span class="status-dot {status_color}"></span>{status_text}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-label">Configuration</div>', unsafe_allow_html=True)

    selected_domain = st.selectbox(
        "Domain",
        list(st.session_state.domain_models.keys()),
        help="Choose a business domain. Available models are filtered automatically."
    )

    domain_models = st.session_state.domain_models.get(selected_domain, [])

    if domain_models:
        selected_model = st.selectbox(
            "Model",
            domain_models,
            help=f"Models trained for the {selected_domain} domain"
        )
        model_available = True
    else:
        st.selectbox("Model", ["None available"], disabled=True)
        selected_model = None
        model_available = False

    st.markdown("---")

    st.markdown('<div class="section-label">Active Configuration</div>', unsafe_allow_html=True)

    if model_available:
        st.markdown(f"""
        <div style="background: white; border: 1px solid #e2e8f0; border-radius: 14px;
                    padding: 0.95rem 1rem; border-left: 4px solid #2563eb;
                    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem;
                        color: #0f172a; font-weight: 700;">
                {h(selected_model)}
            </div>
            <div style="font-size: 0.74rem; color: #475569; margin-top: 0.35rem;">
                {h(selected_domain)}
            </div>
            <div style="margin-top: 0.7rem;">
                <span class="badge badge-success">Ready</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background: #fef3c7; border: 1px solid #fde68a; border-radius: 14px;
                    padding: 0.95rem 1rem;">
            <div style="font-size: 0.84rem; color: #92400e; font-weight: 700; margin-bottom: 0.35rem;">
                No Model Available
            </div>
            <div style="font-size: 0.76rem; color: #b45309; line-height: 1.5;">
                The <strong>{h(selected_domain)}</strong> domain has no trained models yet.
                Upload a model below or switch to <strong>Business Leadership</strong>.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown('<div class="section-label">Upload Model</div>', unsafe_allow_html=True)

    upload_domain = st.selectbox(
        "Assign to domain",
        list(st.session_state.domain_models.keys()),
        key="upload_domain",
        label_visibility="collapsed"
    )

    uploaded_file = st.file_uploader(
        "Drop a .pkl or .joblib file",
        type=["pkl", "joblib"],
        label_visibility="collapsed"
    )

    if uploaded_file:
        models_dir = Path("app/models")
        models_dir.mkdir(parents=True, exist_ok=True)

        safe_filename = Path(uploaded_file.name).name
        file_path = models_dir / safe_filename

        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        model_name = safe_filename.replace(".pkl", "").replace(".joblib", "")

        if model_name not in st.session_state.domain_models[upload_domain]:
            st.session_state.domain_models[upload_domain].append(model_name)

        st.markdown(
            f'<span class="badge badge-success">Uploaded to {h(upload_domain)}</span>',
            unsafe_allow_html=True
        )

    st.markdown("---")

    st.markdown('<div class="section-label">Session</div>', unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    col_a.metric("Predictions", len(st.session_state.history))
    col_b.metric("Compared", len(st.session_state.comparison))


# ============================================================
# MAIN HEADER
# ============================================================
col_title, col_action = st.columns([3, 1])

with col_title:
    st.markdown("""
    <div>
        <h1 class="app-title">Adoption Performance Intelligence</h1>
        <p class="app-subtitle">
            Predict AI agent adoption success with explainable machine learning.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col_action:
    st.markdown('<div style="height: 1.2rem;"></div>', unsafe_allow_html=True)
    if st.button("Clear Session", use_container_width=True):
        st.session_state.history = []
        st.session_state.comparison = []
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)


# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Single Prediction",
    "Compare Configurations",
    "Batch Analysis",
    "Model Registry",
    "Documentation"
])


# ============================================================
# TAB 1 — SINGLE PREDICTION
# ============================================================
with tab1:
    if not model_available:
        st.markdown(f"""
        <div style="background: #fef3c7; border: 1px solid #fde68a; border-radius: 16px;
                    padding: 1.25rem 1.5rem; margin-bottom: 1.5rem;">
            <div style="font-weight: 700; color: #92400e; margin-bottom: 0.4rem;">
                No model is available for the {h(selected_domain)} domain
            </div>
            <div style="color: #b45309; font-size: 0.9rem; line-height: 1.6;">
                Predictions are disabled. To proceed, switch to <strong>Business Leadership</strong>
                in the sidebar, or upload a trained model for this domain.
            </div>
        </div>
        """, unsafe_allow_html=True)

    left, right = st.columns([1.3, 1])

    with left:
        st.markdown('<div class="section-label">Input Configuration</div>', unsafe_allow_html=True)

        with st.expander("Organizational Context", expanded=True):
            c1, c2 = st.columns(2)

            with c1:
                industry = st.selectbox(
                    "Industry",
                    ["Finance", "Healthcare", "Retail", "Manufacturing", "Technology", "Education"]
                )
                org_size = st.selectbox(
                    "Organization Size",
                    ["Small", "Medium", "Large", "Enterprise"]
                )
                leadership_fn = st.selectbox(
                    "Leadership Function",
                    ["Operations", "Strategy", "HR", "Finance", "Marketing", "IT"]
                )

            with c2:
                ai_maturity = st.selectbox(
                    "AI Maturity Level",
                    ["Beginner", "Intermediate", "Advanced", "Expert"]
                )
                use_case = st.selectbox(
                    "Use Case Area",
                    [
                        "Customer Service",
                        "Decision Support",
                        "Data Analysis",
                        "Process Automation",
                        "Strategic Planning"
                    ]
                )

        with st.expander("Agent Configuration", expanded=True):
            c1, c2 = st.columns(2)

            with c1:
                agent_type = st.selectbox(
                    "Agent Type",
                    ["Chatbot", "Decision Agent", "Analytical Agent", "Autonomous Agent"]
                )
                autonomy = st.select_slider(
                    "Autonomy Level",
                    options=["Low", "Medium", "High"]
                )
                decision_type = st.selectbox(
                    "Decision Making",
                    ["Rule-based", "ML-based", "Hybrid"]
                )
                task_complexity = st.select_slider(
                    "Task Complexity",
                    options=["Low", "Medium", "High"]
                )

            with c2:
                oversight = st.select_slider(
                    "Human Oversight",
                    options=["Low", "Medium", "High"]
                )
                explainability = st.select_slider(
                    "Explainability",
                    options=["Low", "Medium", "High"]
                )
                privacy = st.selectbox(
                    "Privacy Compliance",
                    ["Compliant", "Partial", "Non-compliant"]
                )
                integration = st.select_slider(
                    "Integration Level",
                    options=["Standalone", "Partial", "Full"]
                )

        with st.expander("Performance Metrics", expanded=True):
            c1, c2 = st.columns(2)

            with c1:
                context_score = st.slider(
                    "Context Awareness Score",
                    0.0,
                    10.0,
                    7.0,
                    0.1
                )
                success_rate = st.slider(
                    "Task Success Rate (%)",
                    0.0,
                    100.0,
                    80.0
                )
                response_time = st.slider(
                    "Response Time (seconds)",
                    0.0,
                    60.0,
                    2.0,
                    0.1
                )

            with c2:
                productivity = st.slider(
                    "Productivity Improvement (%)",
                    0.0,
                    100.0,
                    30.0
                )
                trust_score = st.slider(
                    "Leadership Trust Score",
                    0.0,
                    10.0,
                    7.0,
                    0.1
                )

        st.markdown("<br>", unsafe_allow_html=True)

        col_btn1, col_btn2 = st.columns([1, 1])

        with col_btn1:
            predict_clicked = st.button(
                "Run Prediction",
                use_container_width=True,
                disabled=not model_available
            )

        with col_btn2:
            add_to_compare = st.button(
                "Save to Compare",
                use_container_width=True,
                disabled=not model_available
            )

    with right:
        st.markdown('<div class="section-label">Live Configuration Preview</div>', unsafe_allow_html=True)

        radar_categories = [
            "Context<br>Awareness",
            "Task<br>Success",
            "Response<br>Speed",
            "Productivity",
            "Trust"
        ]

        radar_values = [
            context_score * 10,
            success_rate,
            max(0, 100 - response_time * 1.66),
            productivity,
            trust_score * 10
        ]

        fig_radar = go.Figure()

        fig_radar.add_trace(go.Scatterpolar(
            r=radar_values,
            theta=radar_categories,
            fill='toself',
            fillcolor='rgba(37, 99, 235, 0.16)',
            line=dict(color='#2563eb', width=2.8),
            marker=dict(
                size=7,
                color='#1e40af',
                line=dict(color='white', width=2)
            ),
            name='Current'
        ))

        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    tickfont=dict(size=10, color='#94a3b8', family='Inter'),
                    gridcolor='#e2e8f0',
                    linecolor='#e2e8f0'
                ),
                angularaxis=dict(
                    tickfont=dict(size=11, color='#475569', family='Inter'),
                    gridcolor='#e2e8f0',
                    linecolor='#e2e8f0'
                ),
                bgcolor='#f8fafc'
            ),
            showlegend=False,
            height=330,
            margin=dict(l=60, r=60, t=30, b=30),
            paper_bgcolor='rgba(0,0,0,0)'
        )

        st.plotly_chart(fig_radar, use_container_width=True)

        m1, m2, m3 = st.columns(3)
        m1.metric("Trust", f"{trust_score:.1f}/10")
        m2.metric("Success", f"{success_rate:.0f}%")
        m3.metric("Latency", f"{response_time:.1f}s")

    # ========================================================
    # BUILD PAYLOAD
    # ========================================================
    payload = {
        "model_name": selected_model,
        "features": {
            "Industry": industry,
            "Organization_Size": org_size,
            "Leadership_Function": leadership_fn,
            "AI_Maturity_Level": ai_maturity,
            "Agent_Type": agent_type,
            "Use_Case_Area": use_case,
            "Agent_Autonomy_Level": autonomy,
            "Decision_Making_Type": decision_type,
            "Context_Awareness_Score": context_score,
            "Task_Complexity_Level": task_complexity,
            "Human_Oversight_Level": oversight,
            "Explainability_Level": explainability,
            "Data_Privacy_Compliance": privacy,
            "Integration_Level": integration,
            "Task_Success_Rate": success_rate,
            "Response_Time_Seconds": response_time,
            "Productivity_Improvement_Percent": productivity,
            "Leadership_Trust_Score": trust_score
        }
    }

    if add_to_compare and model_available:
        st.session_state.comparison.append({
            "label": f"Config #{len(st.session_state.comparison) + 1}",
            "domain": selected_domain,
            "model": selected_model,
            "payload": payload
        })
        st.toast("Configuration saved to comparison.")

    if predict_clicked and model_available:
        st.markdown("<br>", unsafe_allow_html=True)

        with st.spinner("Computing prediction..."):
            try:
                response = requests.post(
                    f"{API_BASE}/predict",
                    json=payload,
                    timeout=10
                )

                if response.status_code == 200:
                    result = response.json()

                    pred = result["prediction"]
                    conf = result["confidence"]
                    probs = result["probabilities"]

                    st.session_state.history.append({
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                        "domain": selected_domain,
                        "model": selected_model,
                        "prediction": pred,
                        "confidence": conf,
                        "industry": industry,
                        "agent_type": agent_type
                    })

                    st.markdown(f"""
                    <div class="result-panel">
                        <div class="result-label">Predicted Adoption Success</div>
                        <div class="result-value">{h(pred)}</div>
                        <div class="result-confidence">
                            Confidence {conf * 100:.2f}% · Model {h(selected_model)}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    g1, g2 = st.columns(2)

                    with g1:
                        st.markdown(
                            '<div class="section-label">Class Probabilities</div>',
                            unsafe_allow_html=True
                        )

                        prob_df = pd.DataFrame({
                            "Class": list(probs.keys()),
                            "Probability": [v * 100 for v in probs.values()]
                        }).sort_values("Probability", ascending=True)

                        fig_bar = go.Figure(go.Bar(
                            x=prob_df["Probability"],
                            y=prob_df["Class"],
                            orientation="h",
                            marker=dict(
                                color=prob_df["Probability"],
                                colorscale=[
                                    [0, "#dbeafe"],
                                    [0.5, "#60a5fa"],
                                    [1, "#1e40af"]
                                ],
                                line=dict(color="#1e40af", width=0)
                            ),
                            text=[f"{v:.1f}%" for v in prob_df["Probability"]],
                            textposition="outside",
                            textfont=dict(
                                size=12,
                                color="#0f172a",
                                family="Inter"
                            )
                        ))

                        fig_bar.update_layout(
                            height=270,
                            margin=dict(l=10, r=50, t=10, b=10),
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            xaxis=dict(
                                showgrid=False,
                                showticklabels=False,
                                range=[0, 110]
                            ),
                            yaxis=dict(
                                showgrid=False,
                                tickfont=dict(
                                    size=12,
                                    color="#0f172a",
                                    family="Inter"
                                )
                            ),
                            showlegend=False
                        )

                        st.plotly_chart(fig_bar, use_container_width=True)

                    with g2:
                        st.markdown(
                            '<div class="section-label">Confidence Level</div>',
                            unsafe_allow_html=True
                        )

                        fig_gauge = go.Figure(go.Indicator(
                            mode="gauge+number",
                            value=conf * 100,
                            number=dict(
                                suffix="%",
                                font=dict(
                                    size=34,
                                    color="#0f172a",
                                    family="Inter"
                                )
                            ),
                            gauge=dict(
                                axis=dict(
                                    range=[0, 100],
                                    tickwidth=1,
                                    tickcolor="#cbd5e1",
                                    tickfont=dict(
                                        size=10,
                                        color="#94a3b8"
                                    )
                                ),
                                bar=dict(
                                    color="#2563eb",
                                    thickness=0.28
                                ),
                                bgcolor="#f8fafc",
                                borderwidth=0,
                                steps=[
                                    dict(range=[0, 50], color="#fee2e2"),
                                    dict(range=[50, 75], color="#fef3c7"),
                                    dict(range=[75, 100], color="#dcfce7")
                                ],
                                threshold=dict(
                                    line=dict(color="#1e40af", width=3),
                                    thickness=0.75,
                                    value=conf * 100
                                )
                            )
                        ))

                        fig_gauge.update_layout(
                            height=270,
                            margin=dict(l=20, r=20, t=20, b=10),
                            paper_bgcolor="rgba(0,0,0,0)"
                        )

                        st.plotly_chart(fig_gauge, use_container_width=True)

                    st.markdown(
                        '<div class="section-label">Recommendation</div>',
                        unsafe_allow_html=True
                    )

                    if pred == "High":
                        rec_text = (
                            "Strong adoption indicators. Configuration is well-aligned "
                            "with successful deployment patterns. Proceed with rollout planning."
                        )
                        rec_class = "badge-success"
                    elif pred == "Medium":
                        rec_text = (
                            "Moderate adoption likelihood. Consider strengthening human oversight, "
                            "increasing explainability, or improving trust scores before full deployment."
                        )
                        rec_class = "badge-warning"
                    else:
                        rec_text = (
                            "Low adoption signal. Critical configuration review required. "
                            "Re-evaluate task complexity, integration depth, and stakeholder alignment."
                        )
                        rec_class = "badge-error"

                    st.markdown(f"""
                    <div class="card">
                        <span class="badge {rec_class}">{h(pred)} Adoption Probability</span>
                        <p style="margin-top: 0.85rem; color: #475569; line-height: 1.6; font-size: 0.92rem;">
                            {h(rec_text)}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                    e1, e2 = st.columns(2)

                    with e1:
                        st.download_button(
                            "Export JSON",
                            data=json.dumps(
                                {
                                    "input": payload,
                                    "result": result
                                },
                                indent=2
                            ),
                            file_name=f"prediction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json",
                            use_container_width=True
                        )

                    with e2:
                        df_export = pd.DataFrame([{
                            **payload["features"],
                            "prediction": pred,
                            "confidence": conf
                        }])

                        st.download_button(
                            "Export CSV",
                            data=df_export.to_csv(index=False),
                            file_name=f"prediction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )

                else:
                    st.error(f"API returned {response.status_code}: {response.text}")

            except requests.exceptions.ConnectionError:
                st.error(
                    "Cannot connect to FastAPI server. "
                    "Ensure it is running on port 8000."
                )
            except Exception as e:
                st.error(f"Unexpected error: {e}")

    if st.session_state.history:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            '<div class="section-label">Recent Predictions</div>',
            unsafe_allow_html=True
        )

        hist_df = pd.DataFrame(st.session_state.history[-5:][::-1])
        st.dataframe(hist_df, use_container_width=True, hide_index=True)


# ============================================================
# TAB 2 — COMPARE CONFIGURATIONS
# ============================================================
with tab2:
    st.markdown(
        '<div class="section-label">Configuration Comparison</div>',
        unsafe_allow_html=True
    )

    if not st.session_state.comparison:
        st.markdown("""
        <div class="empty-state">
            <div style="font-size: 1rem; color: #0f172a; font-weight: 700; margin-bottom: 0.4rem;">
                No configurations saved
            </div>
            <div style="font-size: 0.88rem;">
                Use <strong>Save to Compare</strong> on the prediction tab to add configurations here.
            </div>
        </div>
        """, unsafe_allow_html=True)

    else:
        st.markdown(f"""
        <div class="info-panel" style="margin-bottom: 1rem;">
            Comparing <strong>{len(st.session_state.comparison)}</strong> configuration(s)
        </div>
        """, unsafe_allow_html=True)

        col_run, col_clear = st.columns([1, 1])

        with col_run:
            run_compare = st.button(
                "Run Comparison Predictions",
                use_container_width=True
            )

        with col_clear:
            if st.button("Clear All", use_container_width=True):
                st.session_state.comparison = []
                st.rerun()

        if run_compare:
            results_data = []

            with st.spinner("Running predictions..."):
                for cfg in st.session_state.comparison:
                    if cfg.get("model") is None:
                        continue

                    try:
                        r = requests.post(
                            f"{API_BASE}/predict",
                            json=cfg["payload"],
                            timeout=10
                        )

                        if r.status_code == 200:
                            res = r.json()

                            results_data.append({
                                "Configuration": cfg["label"],
                                "Domain": cfg.get("domain", "N/A"),
                                "Industry": cfg["payload"]["features"]["Industry"],
                                "Agent Type": cfg["payload"]["features"]["Agent_Type"],
                                "Trust Score": cfg["payload"]["features"]["Leadership_Trust_Score"],
                                "Success Rate": cfg["payload"]["features"]["Task_Success_Rate"],
                                "Prediction": res["prediction"],
                                "Confidence": f"{res['confidence'] * 100:.1f}%"
                            })
                        else:
                            st.warning(
                                f"{cfg['label']} failed with status {r.status_code}: {r.text}"
                            )

                    except Exception as e:
                        st.warning(f"Failed for {cfg['label']}: {e}")

            if results_data:
                comp_df = pd.DataFrame(results_data)
                st.dataframe(comp_df, use_container_width=True, hide_index=True)

                fig_comp = px.bar(
                    comp_df,
                    x="Configuration",
                    y="Trust Score",
                    color="Prediction",
                    color_discrete_map={
                        "High": "#15803d",
                        "Medium": "#b45309",
                        "Low": "#b91c1c"
                    }
                )

                fig_comp.update_layout(
                    height=380,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="#f8fafc",
                    font=dict(family="Inter", color="#0f172a"),
                    xaxis=dict(
                        gridcolor="#e2e8f0",
                        title=None
                    ),
                    yaxis=dict(gridcolor="#e2e8f0"),
                    legend=dict(
                        bgcolor="rgba(255,255,255,0.85)",
                        bordercolor="#e2e8f0",
                        borderwidth=1
                    )
                )

                st.plotly_chart(fig_comp, use_container_width=True)


# ============================================================
# TAB 3 — BATCH ANALYSIS
# ============================================================
with tab3:
    st.markdown(
        '<div class="section-label">Batch Predictions</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <p style="color: #475569; font-size: 0.9rem;">
            Upload a CSV file with multiple agent configurations to predict in bulk.
        </p>
        """,
        unsafe_allow_html=True
    )

    if not model_available:
        st.markdown(f"""
        <div class="empty-state">
            <div style="font-size: 1rem; color: #0f172a; font-weight: 700; margin-bottom: 0.4rem;">
                Batch predictions disabled
            </div>
            <div style="font-size: 0.88rem;">
                The <strong>{h(selected_domain)}</strong> domain has no available model.
                Switch to <strong>Business Leadership</strong> in the sidebar.
            </div>
        </div>
        """, unsafe_allow_html=True)

    else:
        batch_file = st.file_uploader(
            "Drop CSV file",
            type=["csv"],
            key="batch"
        )

        if batch_file:
            df = pd.read_csv(batch_file)

            c1, c2, c3 = st.columns(3)
            c1.metric("Records", len(df))
            c2.metric("Features", len(df.columns))
            c3.metric(
                "Memory",
                f"{df.memory_usage(deep=True).sum() / 1024:.1f} KB"
            )

            st.markdown(
                '<div class="section-label">Preview</div>',
                unsafe_allow_html=True
            )
            st.dataframe(df.head(10), use_container_width=True, hide_index=True)

            if st.button("Run Batch Predictions"):
                with st.spinner(f"Processing {len(df)} records..."):
                    try:
                        response = requests.post(
                            f"{API_BASE}/predict_batch",
                            files={
                                "file": (
                                    batch_file.name,
                                    batch_file.getvalue(),
                                    "text/csv"
                                )
                            },
                            params={
                                "model_name": selected_model
                            },
                            timeout=60
                        )

                        if response.status_code == 200:
                            results = pd.DataFrame(
                                response.json()["predictions"]
                            )

                            st.markdown(
                                f'<span class="badge badge-success">Predicted {len(results)} records</span>',
                                unsafe_allow_html=True
                            )

                            st.dataframe(
                                results,
                                use_container_width=True,
                                hide_index=True
                            )

                            st.download_button(
                                "Download Results",
                                results.to_csv(index=False),
                                "predictions.csv",
                                "text/csv",
                                use_container_width=True
                            )
                        else:
                            st.error(
                                f"API returned {response.status_code}: {response.text}"
                            )

                    except Exception as e:
                        st.error(f"Batch error: {e}")


# ============================================================
# TAB 4 — MODEL REGISTRY
# ============================================================
with tab4:
    st.markdown(
        '<div class="section-label">Domain Coverage</div>',
        unsafe_allow_html=True
    )

    cols = st.columns(len(st.session_state.domain_models))

    for i, (domain, models) in enumerate(st.session_state.domain_models.items()):
        with cols[i]:
            count = len(models)
            badge_class = "badge-success" if count > 0 else "badge-neutral"
            status = f"{count} model(s)" if count > 0 else "No models"

            models_html = "<br>".join([h(model) for model in models]) if models else "—"

            st.markdown(f"""
            <div class="card" style="text-align: center;">
                <div style="font-size: 0.95rem; font-weight: 700; color: #0f172a; margin-bottom: 0.6rem;">
                    {h(domain)}
                </div>
                <span class="badge {badge_class}">{h(status)}</span>
                <div style="margin-top: 0.85rem; font-family: 'JetBrains Mono', monospace;
                            font-size: 0.75rem; color: #475569; min-height: 2.5rem;">
                    {models_html}
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        '<div class="section-label">Registered Models</div>',
        unsafe_allow_html=True
    )

    all_models = []

    for domain, models in st.session_state.domain_models.items():
        for model in models:
            all_models.append({
                "domain": domain,
                "model": model
            })

    if not all_models:
        st.markdown("""
        <div class="empty-state">
            <div style="font-size: 1rem; color: #0f172a; font-weight: 700; margin-bottom: 0.4rem;">
                No models registered
            </div>
            <div style="font-size: 0.88rem;">
                Upload a model from the sidebar to get started.
            </div>
        </div>
        """, unsafe_allow_html=True)

    else:
        for item in all_models:
            st.markdown(f"""
            <div class="card">
                <div style="display: flex; justify-content: space-between; align-items: center; gap: 1rem;">
                    <div style="flex: 1;">
                        <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem;">
                            <div style="width: 36px; height: 36px;
                                        background: linear-gradient(135deg, #0f172a, #2563eb);
                                        border-radius: 10px; display: flex; align-items: center;
                                        justify-content: center; color: white; font-weight: 800;
                                        font-size: 0.9rem;">
                                ◆
                            </div>
                            <div>
                                <div style="font-family: 'JetBrains Mono', monospace;
                                            font-size: 0.95rem; font-weight: 700; color: #0f172a;">
                                    {h(item['model'])}
                                </div>
                                <div style="margin-top: 0.35rem; display: flex; gap: 0.4rem; flex-wrap: wrap;">
                                    <span class="badge badge-info">{h(item['domain'])}</span>
                                    <span class="badge badge-accent">SVM</span>
                                    <span class="badge badge-success">Active</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div style="text-align: right; font-size: 0.78rem; color: #475569;">
                        <div style="text-transform: uppercase; letter-spacing: 0.08em;
                                    font-weight: 700; margin-bottom: 0.2rem;">Type</div>
                        <div style="font-family: 'JetBrains Mono', monospace; color: #0f172a;">
                            Classification
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)


# ============================================================
# TAB 5 — DOCUMENTATION
# ============================================================
with tab5:
    doc_col1, doc_col2 = st.columns([2, 1])

    with doc_col1:
        st.markdown(
            '<div class="section-label">Platform Overview</div>',
            unsafe_allow_html=True
        )

        st.markdown("""
        <div class="card">
            <h3 style="margin-top: 0; color: #0f172a;">About AgentLens</h3>
            <p style="color: #475569; line-height: 1.7;">
                AgentLens is an explainable machine learning platform for predicting AI agent
                adoption success across enterprise domains. The platform combines a Support Vector
                Machine classifier with PCA dimensionality reduction to deliver fast, interpretable
                predictions.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(
            '<div class="section-label" style="margin-top: 1.5rem;">Architecture</div>',
            unsafe_allow_html=True
        )

        arch_data = pd.DataFrame({
            "Layer": [
                "Modeling",
                "API",
                "Interface",
                "Persistence"
            ],
            "Technology": [
                "scikit-learn SVM and PCA",
                "FastAPI and Uvicorn",
                "Streamlit and Plotly",
                "joblib"
            ],
            "Purpose": [
                "Classification pipeline",
                "RESTful prediction endpoints",
                "Interactive dashboard",
                "Model serialization"
            ]
        })

        st.dataframe(arch_data, use_container_width=True, hide_index=True)

        st.markdown(
            '<div class="section-label" style="margin-top: 1.5rem;">Prediction Pipeline</div>',
            unsafe_allow_html=True
        )

        pipeline_steps = [
            (
                "01",
                "Imputation",
                "Fills missing numerical values with median values and categorical values with mode values."
            ),
            (
                "02",
                "Encoding",
                "One-hot encodes categorical features."
            ),
            (
                "03",
                "Scaling",
                "Standardizes numerical features to zero mean and unit variance."
            ),
            (
                "04",
                "PCA",
                "Retains 95% of variance and reduces multicollinearity."
            ),
            (
                "05",
                "SVM",
                "Uses an RBF kernel classifier with probability calibration."
            )
        ]

        for num, name, desc in pipeline_steps:
            st.markdown(f"""
            <div class="card" style="margin-bottom: 0.6rem;">
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <div style="font-family: 'JetBrains Mono', monospace; font-size: 1rem;
                                font-weight: 800; color: #2563eb; min-width: 36px;">
                        {h(num)}
                    </div>
                    <div style="flex: 1;">
                        <div style="font-weight: 700; color: #0f172a; margin-bottom: 0.2rem;">
                            {h(name)}
                        </div>
                        <div style="color: #475569; font-size: 0.88rem;">
                            {h(desc)}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with doc_col2:
        st.markdown(
            '<div class="section-label">Quick Reference</div>',
            unsafe_allow_html=True
        )

        st.markdown(f"""
        <div class="card">
            <div style="font-size: 0.8rem; color: #475569; margin-bottom: 0.3rem;
                        text-transform: uppercase; letter-spacing: 0.08em; font-weight: 700;">
                API Base
            </div>
            <code style="font-size: 0.85rem;">{h(API_BASE)}</code>

            <div style="font-size: 0.8rem; color: #475569; margin: 1rem 0 0.3rem 0;
                        text-transform: uppercase; letter-spacing: 0.08em; font-weight: 700;">
                Documentation
            </div>
            <code style="font-size: 0.85rem;">/docs</code>

            <div style="font-size: 0.8rem; color: #475569; margin: 1rem 0 0.3rem 0;
                        text-transform: uppercase; letter-spacing: 0.08em; font-weight: 700;">
                Model Format
            </div>
            <code style="font-size: 0.85rem;">.pkl · .joblib</code>
        </div>

        <div class="card">
            <div style="font-size: 0.8rem; color: #475569; margin-bottom: 0.6rem;
                        text-transform: uppercase; letter-spacing: 0.08em; font-weight: 700;">
                Endpoints
            </div>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem;
                        color: #0f172a; line-height: 1.9;">
                <div><span style="color: #15803d; font-weight: 700;">GET</span> /health</div>
                <div><span style="color: #15803d; font-weight: 700;">GET</span> /models</div>
                <div><span style="color: #2563eb; font-weight: 700;">POST</span> /predict</div>
                <div><span style="color: #2563eb; font-weight: 700;">POST</span> /predict_batch</div>
                <div><span style="color: #2563eb; font-weight: 700;">POST</span> /models/upload</div>
            </div>
        </div>

        <div class="card">
            <div style="font-size: 0.8rem; color: #475569; margin-bottom: 0.4rem;
                        text-transform: uppercase; letter-spacing: 0.08em; font-weight: 700;">
                Resources
            </div>
            <a href="https://github.com/youssef-othman12/AgentLens" target="_blank">
                GitHub Repository →
            </a>
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# FOOTER
# ============================================================
st.markdown("<br><br>", unsafe_allow_html=True)

st.markdown("""
<div style="border-top: 1px solid #e2e8f0; padding-top: 1.5rem; text-align: center;
            color: #94a3b8; font-size: 0.8rem;">
    <span style="color: #2563eb; font-weight: 800;">◆</span>
    <strong style="color: #475569;">AgentLens</strong> v1.0
    &nbsp;·&nbsp; Built with FastAPI, scikit-learn, and Streamlit
    &nbsp;·&nbsp; <a href="https://github.com/youssef-othman12/AgentLens">Source</a>
</div>
""", unsafe_allow_html=True)