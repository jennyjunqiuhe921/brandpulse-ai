import streamlit as st
from config.settings import BRAND_DISPLAY_NAMES, BRAND_FOCUS
from core.rag_engine import collection_count
from core.llm_client import DEMO_MODE, get_demo_snapshot


def _preload_demo_for_brand(brand_key: str):
    """Fill session_state with demo preview content for all modules.
    Only fills keys that don't already have real results (preserves user-run output).
    Clears stale previews when brand changes."""
    snapshot = get_demo_snapshot(brand_key)
    for key, value in snapshot.items():
        existing = st.session_state.get(key)
        # Skip if there's already a real (non-preview) result
        if existing and not existing.get("_is_demo_preview"):
            continue
        st.session_state[key] = value

# ── Global CSS ────────────────────────────────────────────────────────────────
GLOBAL_CSS = """
<style>
/* ═══════════════════════════════════════════════════════════════════
   PinSight AI — Warm Editorial Theme
   Aesthetic: 织织风格 · 温暖纸质 · 编辑感
   Fonts: Noto Serif SC (衬线标题) + Noto Sans SC (正文)
═══════════════════════════════════════════════════════════════════ */

@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700;900&family=Noto+Sans+SC:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

/* ── CSS Variables ── */
:root {
    --bg-base:        #F5EFE4;
    --bg-surface:     #FDFAF5;
    --bg-elevated:    #FFFFFF;
    --bg-hover:       #EDE6D8;
    --border:         #DDD4C4;
    --border-light:   #EDE6D8;
    --text-primary:   #1C1510;
    --text-secondary: #5C4F42;
    --text-muted:     #9C8E82;
    --accent:         #C4522A;
    --accent-dim:     rgba(196,82,42,0.08);
    --accent-light:   #E8755A;
    --green:          #3D7A5A;
    --green-dim:      rgba(61,122,90,0.09);
    --amber:          #B5860D;
    --amber-dim:      rgba(181,134,13,0.10);
    --red:            #C4391A;
    --red-dim:        rgba(196,57,26,0.08);
    --blue:           #2B6CB0;
    --blue-dim:       rgba(43,108,176,0.08);
    --font-display:   'Noto Serif SC', 'Source Han Serif SC', serif;
    --font-body:      'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif;
    --font-mono:      'DM Mono', 'SF Mono', monospace;
    --font-nav:       'Noto Sans SC', sans-serif;
    --radius:         10px;
    --radius-sm:      6px;
    --shadow:         0 2px 12px rgba(60,40,20,0.08);
    --shadow-lg:      0 6px 32px rgba(60,40,20,0.12);
}

/* ── Base ── */
html, body, [class*="css"] {
    font-family: var(--font-body) !important;
    color: var(--text-primary) !important;
}

/* ── Page background ── */
.stApp {
    background-color: var(--bg-base) !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }
[data-testid="stStatusWidget"] { display: none; }

/* ── Page load animation ── */
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
}
.main .block-container {
    animation: fadeUp 0.35s ease both;
}

/* ══════════════════════════════════════════════
   SIDEBAR
══════════════════════════════════════════════ */
[data-testid="stSidebar"] {
    background: #FDFAF5 !important;
    border-right: 1px solid var(--border) !important;
    min-width: 220px !important;
    max-width: 220px !important;
}
/* 桌面端：侧边栏始终可见，禁止折叠到屏幕外（该 Streamlit 版本折叠后展开按钮
   会被移出屏幕导致再也展不开）。隐藏折叠按钮，避免用户误触陷入卡死状态。 */
@media (min-width: 641px) {
    [data-testid="stSidebar"] {
        transform: none !important;
        visibility: visible !important;
        margin-left: 0 !important;
    }
    [data-testid="stSidebar"] [data-testid="stBaseButton-headerNoPadding"] {
        display: none !important;
    }
}

[data-testid="stSidebar"] > div:first-child { padding: 0 !important; }
[data-testid="stSidebarContent"] { padding: 0 !important; }
section[data-testid="stSidebar"] .block-container { padding: 0 !important; }

/* ── Logo area ── */
.sidebar-logo {
    padding: 28px 22px 20px 22px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 6px;
}

.sidebar-logo .logo-icon {
    width: 32px;
    height: 32px;
    background: var(--text-primary);
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--bg-base);
    font-size: 14px;
    font-weight: 700;
    font-family: var(--font-display);
    margin-bottom: 10px;
}

.sidebar-logo .logo-name {
    font-family: var(--font-display);
    font-size: 15px;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: 0.2px;
    line-height: 1.2;
}

.sidebar-logo .logo-sub {
    font-size: 10.5px;
    color: var(--text-muted);
    letter-spacing: 0.3px;
    margin-top: 3px;
}

/* ── Sidebar nav label ── */
.sidebar-section-label {
    padding: 16px 22px 6px 22px;
    font-size: 9.5px;
    font-weight: 600;
    color: var(--text-muted);
    letter-spacing: 2px;
    text-transform: uppercase;
    font-family: var(--font-nav);
}

/* ── Sidebar page_link nav ── */
[data-testid="stSidebar"] [data-testid="stPageLink"] a {
    padding: 9px 22px !important;
    font-size: 13px !important;
    font-weight: 400 !important;
    color: var(--text-secondary) !important;
    border-radius: 0 !important;
    display: flex !important;
    align-items: center !important;
    text-decoration: none !important;
    transition: all 0.15s ease !important;
    border-left: 2px solid transparent !important;
    font-family: var(--font-nav) !important;
}
[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {
    background: var(--bg-hover) !important;
    color: var(--text-primary) !important;
}
[data-testid="stSidebar"] [data-testid="stPageLink-active"] a {
    background: var(--accent-dim) !important;
    color: var(--accent) !important;
    border-left-color: var(--accent) !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] [data-testid="stPageLink"] {
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* ── Radio (brand selector) ── */
[data-testid="stSidebar"] .stRadio > label { display: none; }
[data-testid="stSidebar"] .stRadio > div {
    gap: 0 !important;
    flex-direction: column !important;
}
[data-testid="stSidebar"] .stRadio > div > label {
    padding: 8px 22px !important;
    border-radius: 0 !important;
    border: none !important;
    border-left: 2px solid transparent !important;
    font-size: 12.5px !important;
    font-weight: 400 !important;
    color: var(--text-secondary) !important;
    background: transparent !important;
    cursor: pointer !important;
    transition: all 0.15s ease !important;
    display: flex !important;
    align-items: center !important;
    font-family: var(--font-nav) !important;
}
[data-testid="stSidebar"] .stRadio > div > label:hover {
    background: var(--bg-hover) !important;
    color: var(--text-primary) !important;
}
[data-testid="stSidebar"] .stRadio [aria-checked="true"] ~ span,
[data-testid="stSidebar"] .stRadio [aria-checked="true"] {
    color: var(--text-primary) !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] .stRadio [role="radio"] { display: none !important; }

/* ── Sidebar status ── */
.sidebar-status {
    padding: 10px 14px;
    margin: 0 14px 12px 14px;
    border-radius: var(--radius-sm);
    font-size: 11px;
    line-height: 1.55;
}
.sidebar-status.demo {
    background: var(--amber-dim);
    border: 1px solid rgba(181,134,13,0.25);
    color: var(--amber);
}
.sidebar-status.live {
    background: var(--green-dim);
    border: 1px solid rgba(61,122,90,0.2);
    color: var(--green);
}

/* ── Sidebar metric ── */
[data-testid="stSidebar"] [data-testid="stMetric"] {
    background: var(--bg-base) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    padding: 10px 14px !important;
    margin: 0 14px 12px 14px !important;
}
[data-testid="stSidebar"] [data-testid="stMetricValue"] {
    font-family: var(--font-display) !important;
    font-size: 22px !important;
    font-weight: 700 !important;
    color: var(--text-primary) !important;
}
[data-testid="stSidebar"] [data-testid="stMetricLabel"] {
    font-size: 10px !important;
    color: var(--text-muted) !important;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}

/* ══════════════════════════════════════════════
   MAIN CONTENT
══════════════════════════════════════════════ */
.main .block-container {
    padding: 44px 52px 64px 52px !important;
    max-width: 1200px !important;
}

/* ── Page header ── */
.page-header { margin-bottom: 28px; }

.page-header h1, .page-title {
    font-family: var(--font-display) !important;
    font-size: 30px !important;
    font-weight: 700 !important;
    color: var(--text-primary) !important;
    margin: 0 0 6px 0 !important;
    letter-spacing: -0.3px;
    line-height: 1.25;
}

.page-header .page-desc {
    font-size: 13.5px;
    color: var(--text-secondary);
    margin: 0;
    line-height: 1.65;
}

/* ── Markdown headings ── */
.main h1 {
    font-family: var(--font-display) !important;
    font-size: 26px !important; font-weight: 700 !important;
    color: var(--text-primary) !important; letter-spacing: -0.3px;
}
.main h2 {
    font-family: var(--font-display) !important;
    font-size: 19px !important; font-weight: 600 !important;
    color: var(--text-primary) !important;
}
.main h3 {
    font-family: var(--font-display) !important;
    font-size: 15px !important; font-weight: 600 !important;
    color: var(--text-primary) !important;
}
.main p, .main li { color: var(--text-primary) !important; line-height: 1.8; }
.main strong { color: var(--text-primary) !important; font-weight: 600 !important; }
.main code {
    font-family: var(--font-mono) !important;
    background: var(--bg-hover) !important;
    border: 1px solid var(--border) !important;
    border-radius: 4px !important;
    padding: 1px 6px !important;
    font-size: 12px !important;
    color: var(--accent) !important;
}
.main hr {
    border-color: var(--border) !important;
    margin: 24px 0 !important;
}

/* ── Section label ── */
.section-title {
    font-family: var(--font-nav);
    font-size: 10px;
    font-weight: 600;
    color: var(--text-muted);
    letter-spacing: 2.5px;
    text-transform: uppercase;
    margin-bottom: 14px;
}

/* ── Brand cards ── */
.brand-card {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 16px 18px !important;
    margin-bottom: 8px !important;
    display: flex !important;
    align-items: center !important;
    gap: 14px !important;
    transition: border-color 0.18s, box-shadow 0.18s !important;
    box-shadow: var(--shadow) !important;
}
.brand-card:hover {
    border-color: var(--accent) !important;
    box-shadow: 0 4px 16px rgba(60,40,20,0.12) !important;
}
.brand-dot {
    width: 38px; height: 38px; border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 15px; font-weight: 800; color: #fff;
    flex-shrink: 0;
    font-family: var(--font-display);
}
.brand-name {
    font-size: 14px !important; font-weight: 600 !important;
    color: var(--text-primary) !important; margin: 0 0 2px !important;
    font-family: var(--font-display) !important;
}
.brand-meta { font-size: 11.5px !important; color: var(--text-muted) !important; margin: 0 !important; }
.demo-badge {
    display: inline-block;
    background: var(--blue-dim);
    border: 1px solid rgba(43,108,176,0.2);
    border-radius: 20px; padding: 1px 7px;
    font-size: 9.5px; color: var(--blue);
    font-weight: 600; letter-spacing: 0.3px; margin-left: 6px;
    vertical-align: middle;
}

/* ── Knowledge base stat boxes ── */
.kb-stat-box {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 16px 20px !important;
    text-align: center !important;
    box-shadow: var(--shadow) !important;
}
.kb-stat-num {
    font-family: var(--font-display);
    font-size: 30px !important; font-weight: 700 !important;
    color: var(--text-primary) !important; line-height: 1 !important;
}
.kb-stat-label { font-size: 10px !important; color: var(--text-muted) !important; margin-top: 5px !important; letter-spacing: 0.8px; text-transform: uppercase; }
.kb-source-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 14px;
    background: var(--bg-elevated);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    margin-bottom: 5px;
    transition: border-color 0.15s;
}
.kb-source-row:hover { border-color: var(--accent); }
.kb-source-name { font-size: 12.5px; font-weight: 500; color: var(--text-primary); }
.kb-source-meta { font-size: 11px; color: var(--text-muted); font-family: var(--font-mono); }

/* ══════════════════════════════════════════════
   STREAMLIT COMPONENTS
══════════════════════════════════════════════ */

/* ── Info / Warning / Success / Error ── */
[data-testid="stInfo"] {
    background: var(--blue-dim) !important;
    border: 1px solid rgba(43,108,176,0.18) !important;
    border-left: 3px solid var(--blue) !important;
    border-radius: var(--radius-sm) !important;
    color: #1E4E8C !important;
    font-size: 13px !important;
}
[data-testid="stWarning"] {
    background: var(--amber-dim) !important;
    border: 1px solid rgba(181,134,13,0.2) !important;
    border-left: 3px solid var(--amber) !important;
    border-radius: var(--radius-sm) !important;
    color: #7A5500 !important;
    font-size: 13px !important;
}
[data-testid="stSuccess"] {
    background: var(--green-dim) !important;
    border: 1px solid rgba(61,122,90,0.2) !important;
    border-left: 3px solid var(--green) !important;
    border-radius: var(--radius-sm) !important;
    color: #1E5C3A !important;
    font-size: 13px !important;
}
[data-testid="stError"] {
    background: var(--red-dim) !important;
    border: 1px solid rgba(196,57,26,0.18) !important;
    border-left: 3px solid var(--red) !important;
    border-radius: var(--radius-sm) !important;
    color: #8C2010 !important;
    font-size: 13px !important;
}

/* ── Buttons ── */
.stButton > button[kind="primary"] {
    background: var(--text-primary) !important;
    color: var(--bg-base) !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    font-family: var(--font-body) !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    padding: 8px 22px !important;
    letter-spacing: 0.1px;
    transition: all 0.18s ease !important;
}
.stButton > button[kind="primary"]:hover {
    background: var(--accent) !important;
    color: #fff !important;
    box-shadow: 0 3px 12px rgba(196,82,42,0.25) !important;
    transform: translateY(-1px);
}
.stButton > button[kind="secondary"] {
    background: transparent !important;
    color: var(--text-secondary) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    transition: all 0.15s !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: var(--text-secondary) !important;
    color: var(--text-primary) !important;
    background: var(--bg-hover) !important;
}

/* ── Text inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    background: var(--bg-elevated) !important;
    font-size: 13px !important;
    color: var(--text-primary) !important;
    font-family: var(--font-body) !important;
    transition: border-color 0.15s !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-dim) !important;
}
.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder {
    color: var(--text-muted) !important;
}

/* ── Select / Multiselect ── */
.stSelectbox > div > div,
.stMultiSelect > div > div {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    background: var(--bg-elevated) !important;
    font-size: 13px !important;
    color: var(--text-primary) !important;
}
.stSelectbox [data-baseweb="select"] > div:first-child,
.stMultiSelect [data-baseweb="select"] > div:first-child {
    background: var(--bg-elevated) !important;
    color: var(--text-primary) !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid var(--border) !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    color: var(--text-muted) !important;
    font-size: 13px !important;
    font-weight: 400 !important;
    padding: 10px 18px !important;
    margin: 0 !important;
    transition: color 0.15s !important;
    font-family: var(--font-nav) !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: var(--text-secondary) !important;
}
.stTabs [aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent) !important;
    font-weight: 600 !important;
}

/* ── 移动端：标签自动换行，全部铺开，无需横向滑动 ── */
@media (max-width: 640px) {
    .stTabs [data-baseweb="tab-list"] {
        flex-wrap: wrap !important;
        overflow-x: visible !important;
        row-gap: 2px !important;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 12px !important;
        font-size: 12.5px !important;
    }
}

/* ── Expander ── */
.streamlit-expanderHeader {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    color: var(--text-secondary) !important;
    transition: border-color 0.15s !important;
}
.streamlit-expanderHeader:hover {
    border-color: var(--text-secondary) !important;
    color: var(--text-primary) !important;
}
.streamlit-expanderContent {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border) !important;
    border-top: none !important;
}
[data-testid="stExpander"] > details {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
}
[data-testid="stExpander"] summary {
    color: var(--text-secondary) !important;
    font-size: 13px !important;
    background: var(--bg-elevated) !important;
}
[data-testid="stExpander"] summary:hover {
    color: var(--text-primary) !important;
}

/* ── Spinner ── */
.stSpinner > div { border-top-color: var(--accent) !important; }

/* ── Caption / small text ── */
.stCaption, [data-testid="stCaptionContainer"] {
    color: var(--text-muted) !important;
    font-size: 11.5px !important;
}

/* ── Checkbox ── */
[data-testid="stCheckbox"] span {
    color: var(--text-secondary) !important;
    font-size: 13px !important;
}

/* ── Divider ── */
hr, .styled-divider {
    border-color: var(--border) !important;
    margin: 24px 0 !important;
}

/* ── Dataframe / Table ── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    overflow: hidden !important;
}

/* ── Progress bar ── */
.stProgress > div > div { background: var(--accent) !important; }
.stProgress > div { background: var(--border) !important; }

/* ── Form submit button ── */
[data-testid="stFormSubmitButton"] > button {
    background: var(--text-primary) !important;
    color: var(--bg-base) !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    transition: all 0.18s !important;
}
[data-testid="stFormSubmitButton"] > button:hover {
    background: var(--accent) !important;
    color: #fff !important;
}

/* ── Color picker ── */
[data-testid="stColorPicker"] > div > div {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    background: var(--bg-elevated) !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    border: 1px dashed var(--border) !important;
    border-radius: var(--radius) !important;
    background: var(--bg-elevated) !important;
    transition: border-color 0.15s !important;
}
[data-testid="stFileUploader"]:hover { border-color: var(--accent) !important; }

/* ── Metric (main area) ── */
[data-testid="stMetric"] {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 16px 20px !important;
    box-shadow: var(--shadow) !important;
}
[data-testid="stMetricValue"] {
    font-family: var(--font-display) !important;
    color: var(--text-primary) !important;
    font-size: 28px !important;
    font-weight: 700 !important;
}
[data-testid="stMetricLabel"] {
    color: var(--text-muted) !important;
    font-size: 11px !important;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}

/* ── Selectbox dropdown menu ── */
[data-baseweb="popover"] [role="listbox"],
[data-baseweb="menu"] {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border) !important;
    box-shadow: var(--shadow-lg) !important;
}
[data-baseweb="option"] {
    background: transparent !important;
    color: var(--text-secondary) !important;
}
[data-baseweb="option"]:hover {
    background: var(--bg-hover) !important;
    color: var(--text-primary) !important;
}

/* ── Alert banner for demo preview ── */
.demo-preview-banner {
    background: var(--amber-dim);
    border: 1px solid rgba(181,134,13,0.2);
    border-radius: var(--radius-sm);
    padding: 10px 14px;
    font-size: 12px;
    color: var(--amber);
    margin-bottom: 12px;
}

/* ── Page header block ── */
.page-header-block {
    padding: 0 0 20px 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 28px;
    position: relative;
}
.page-header-block::after {
    content: '';
    position: absolute;
    bottom: -1px; left: 0; width: 48px;
    height: 2px;
    background: var(--accent);
    border-radius: 1px;
}

/* ── Guide panel (replaces st.info) ── */
.guide-panel {
    background: var(--bg-elevated);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: var(--radius-sm);
    padding: 12px 16px;
    font-size: 13px;
    color: var(--text-secondary);
    line-height: 1.7;
    margin-bottom: 18px;
}
.guide-panel strong { color: var(--text-primary); }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }
</style>
"""

BRAND_ICONS = {
    "heytea": "喜",
    "nayuki": "奈",
    "chapanda": "茶",
}

BRAND_COLORS = {
    "heytea": "#E8F4FD",
    "nayuki": "#FDF0F8",
    "chapanda": "#F0FDF4",
}

NAV_ITEMS = [
    ("01", "品牌 & 产品分析"),
    ("02", "GEO 可见度"),
    ("03", "内容生成"),
    ("04", "市场定位"),
    ("05", "数据采集"),
    ("06", "舆情分析"),
    ("07", "合规审查"),
    ("08", "竞品对标"),
]


# 分组导航：(分组标题, [(icon, label, page_file), ...])
_NAV_GROUPS = [
    ("概览", [
        ("🏠", "工作台",    "1_工作台.py"),
        ("🔔", "消息中心",  "10_消息中心.py"),
    ]),
    ("品牌与资产", [
        ("🏢", "品牌管理",  "0_品牌管理.py"),
        ("📦", "资产库",    "2_资产库.py"),
    ]),
    ("洞察分析", [
        ("📡", "数据采集",  "6_数据采集.py"),
        ("📰", "舆情中心",  "7_舆情分析.py"),
        ("🌐", "GEO",       "3_GEO.py"),
        ("🔭", "竞品情报",  "17_竞品情报.py"),
    ]),
    ("创作与选品", [
        ("✍️", "内容工坊",  "4_内容工坊.py"),
        ("🛒", "智能选品",  "16_智能选品.py"),
    ]),
    ("合规与审批", [
        ("✅", "合规自查",  "9_合规自查.py"),
        ("🛡️", "合规卫士",  "8_合规卫士.py"),
        ("📝", "我的审批",  "12_我的审批.py"),
    ]),
    ("个人", [
        ("👤", "个人中心",  "14_个人中心.py"),
    ]),
]


def render() -> str:
    # Inject global CSS on every page
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

    with st.sidebar:
        # ── Logo (TOP) ────────────────────────────────────────────────────
        st.markdown(
            """
<div class="sidebar-logo">
  <div class="logo-icon">P</div>
  <div class="logo-name">PinSight AI</div>
  <div class="logo-sub">品觉 · 品牌智能工作台</div>
</div>
""",
            unsafe_allow_html=True,
        )

        # ── Navigation links（分组导航）─────────────────────────────────────
        try:
            from auth.login import is_admin
            _admin = is_admin()
        except Exception:
            _admin = False

        # 套餐功能门控：按当前租户套餐隐藏未授权菜单
        try:
            from config.plan_features import has_feature, current_plan
            _plan = current_plan()
        except Exception:
            _plan, has_feature = "企业集团版", lambda k: True
        _PAGE_FEATURE = {"16_智能选品.py": "selection_full", "17_竞品情报.py": "competitor"}

        for _section, _items in _NAV_GROUPS:
            st.markdown(f'<div class="sidebar-section-label">{_section}</div>',
                        unsafe_allow_html=True)
            for icon, label, page_file in _items:
                feat = _PAGE_FEATURE.get(page_file)
                if feat and not has_feature(feat):
                    continue  # 套餐未授权，隐藏
                st.page_link(f"pages/{page_file}", label=f"{icon} {label}")
            # 管理项并入「合规与审批」分组，仅企业领导可见
            if _section == "概览" and _admin:
                st.page_link("pages/18_管理驾驶舱.py", label="📊 管理驾驶舱")
                st.page_link("pages/21_冷启动向导.py", label="🚀 冷启动向导")
            if _section == "合规与审批" and _admin:
                st.page_link("pages/11_审批中心.py", label="🗂️ 审批中心")
                st.page_link("pages/19_合规审计台账.py", label="📒 审计台账")
                st.page_link("pages/20_企业管理.py", label="🏢 企业管理")
                st.page_link("pages/5_账号管理.py", label="👥 账号管理")

        # ── Brand selector ────────────────────────────────────────────────
        st.markdown(
            '<div class="sidebar-section-label" style="margin-top:8px">分析品牌</div>',
            unsafe_allow_html=True,
        )
        brand_options = list(BRAND_DISPLAY_NAMES.keys()) or ["heytea"]

        # 跨页面持久化：用「普通 key」brand_perm 作为唯一真相源（它在 st.navigation
        # 切页时不会被清空），每次渲染前强制把它同步进 radio 的 widget key，
        # 避免 Streamlit 多页应用里带 key 的 widget 状态切页后被重置回默认值。
        if st.session_state.get("brand_perm") not in brand_options:
            st.session_state["brand_perm"] = brand_options[0]
        # 在 widget 实例化前写入其 key（允许），消除跨页 stale/clobber
        st.session_state["brand_widget"] = st.session_state["brand_perm"]

        def _on_brand_change():
            st.session_state["brand_perm"] = st.session_state["brand_widget"]

        st.radio(
            "选择分析品牌",
            brand_options,
            key="brand_widget",
            on_change=_on_brand_change,
            format_func=lambda k: BRAND_DISPLAY_NAMES[k],
            label_visibility="collapsed",
        )
        selected = st.session_state["brand_perm"]

        prev_brand = st.session_state.get("_active_brand", selected)
        if prev_brand != selected:
            for k in list(st.session_state.keys()):
                if k.endswith("_result") or k.endswith("_data"):
                    del st.session_state[k]
        st.session_state["_active_brand"] = selected

        _preload_demo_for_brand(selected)

        # ── Knowledge base metric ──────────────────────────────────────────
        st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
        kb_count = collection_count(selected)
        st.metric(
            "知识库文档块",
            kb_count,
            help="✅ 就绪" if kb_count > 0 else "⚠️ 知识库为空",
        )

        # ── API status ────────────────────────────────────────────────────
        if DEMO_MODE:
            st.markdown(
                '<div class="sidebar-status demo">💡 Demo 模式（使用预置数据）<br>'
                '若要处理自有文件，请在设置中配置 API Key</div>',
                unsafe_allow_html=True,
            )
            # 每会话仅弹一次轻提示，不打扰操作
            if not st.session_state.get("_demo_toast_shown"):
                st.toast("当前处于 Demo 模式（使用预置数据），若要处理自有文件，请在设置中配置 API Key。",
                         icon="💡")
                st.session_state["_demo_toast_shown"] = True
        else:
            st.markdown(
                '<div class="sidebar-status live">🟢 API 已连接 · 动态生成模式</div>',
                unsafe_allow_html=True,
            )

        # ── 套餐标识 ───────────────────────────────────────────────────────
        try:
            _pc = {"基础执行版": "#9C8E82", "标准管控版": "#2B6CB0", "企业集团版": "#3D7A5A"}
            st.markdown(
                f'<div style="margin:6px 14px 0;padding:4px 10px;border-radius:6px;'
                f'background:{_pc.get(_plan,"#9C8E82")}1A;color:{_pc.get(_plan,"#9C8E82")};'
                f'font-size:11px;text-align:center">📦 当前套餐：{_plan}</div>',
                unsafe_allow_html=True)
        except Exception:
            pass

        # ── 账号 + 登出 ────────────────────────────────────────────────────
        try:
            from auth.login import render_account_widget
            render_account_widget()
        except Exception:
            pass

        # ── Disclaimer ────────────────────────────────────────────────────
        st.markdown(
            '<div style="padding:0 16px 24px 16px;font-size:10px;color:var(--text-muted,#4A5168);line-height:1.6">'
            "本工具仅供品牌研究参考，输出需人工复核后方可商业使用。"
            "</div>",
            unsafe_allow_html=True,
        )

    # ── 顶部导航栏 + 底部状态栏（S1-1 标准页面范式）──────────────────────────────
    try:
        from utils.ui import render_top_bar, render_status_bar
        render_top_bar(BRAND_DISPLAY_NAMES.get(selected, selected))
        render_status_bar()  # 固定定位，显示在每个页面底部
    except Exception:
        pass

    # ── Demo 模式软提示横条（页面顶部，不干扰操作）──────────────────────────────
    if DEMO_MODE:
        st.markdown(
            '<div style="background:#FFF7E6;border:1px solid #FFE0A3;border-radius:6px;'
            'padding:8px 14px;margin:0 0 12px;font-size:12.5px;color:#8A6D3B">'
            '💡 当前处于 <b>Demo 模式</b>（使用预置数据），若要处理自有文件，请在设置中配置 API Key。'
            '</div>',
            unsafe_allow_html=True,
        )

    return selected


def render_footer() -> None:
    """页面底部状态栏（S1-1）。建议在每页末尾调用。"""
    try:
        from utils.ui import render_status_bar
        render_status_bar()
    except Exception:
        pass
