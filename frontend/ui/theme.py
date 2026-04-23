from __future__ import annotations

import base64
from pathlib import Path


def safe_text(text: str | None) -> str:
    if text is None:
        return ""
    return str(text)


def image_to_base64(image_path: str) -> str:
    path = Path(image_path)
    if not path.exists():
        return ""
    return base64.b64encode(path.read_bytes()).decode()


def get_theme_tokens(modo: str = "General") -> dict[str, str]:
    if modo == "Estadístico":
        return {
            "APP_BG_START": "#FCF4F8",
            "APP_BG_END": "#F7EDF2",
            "TEXT_MAIN": "#22111A",
            "TEXT_SOFT": "#4B5563",
            "TEXT_MUTED": "#6B7280",
            "TEXT_INVERSE": "#F8FAFC",
            "ACCENT_MAIN": "#8A1538",
            "ACCENT_SECOND": "#5A1026",
            "ACCENT_SOFT": "rgba(138, 21, 56, 0.10)",
            "ACCENT_BORDER": "rgba(138, 21, 56, 0.18)",
            "CARD_BG": "#FFFFFF",
            "PANEL_BG": "#FFFFFF",
            "PANEL_BG_2": "#FFF7FA",
            "SIDEBAR_BG": "#7A1633",
            "SIDEBAR_BG_2": "#4F0D20",
            "SIDEBAR_TEXT": "#FFF7FA",
            "SIDEBAR_BORDER": "rgba(255, 255, 255, 0.10)",
            "SUCCESS": "#16A34A",
            "DANGER": "#DC2626",
            "WARNING": "#D97706",
            "INFO": "#8A1538",
            "PLOT_GRID": "rgba(148, 163, 184, 0.18)",
            "BORDER_SOFT": "rgba(148, 163, 184, 0.20)",
            "SHADOW": "0 14px 34px rgba(58, 12, 26, 0.12)",
            "ACTIVE_NAV_TEXT": "#8A1538",
            "CHIP_BG": "#FBE7EF",
            "CHIP_TEXT": "#7A1633",
            "CHIP_BORDER": "rgba(131, 24, 67, 0.16)",
        }

    return {
        "APP_BG_START": "#FFFFFF",
        "APP_BG_END": "#F8FBFF",
        "TEXT_MAIN": "#0B132B",
        "TEXT_SOFT": "#243B53",
        "TEXT_MUTED": "#52667A",
        "TEXT_INVERSE": "#F8FAFC",
        "ACCENT_MAIN": "#1D4ED8",
        "ACCENT_SECOND": "#2563EB",
        "ACCENT_SOFT": "rgba(37, 99, 235, 0.10)",
        "ACCENT_BORDER": "rgba(37, 99, 235, 0.18)",
        "CARD_BG": "#FFFFFF",
        "PANEL_BG": "#FFFFFF",
        "PANEL_BG_2": "#F4F8FF",
        "SIDEBAR_BG": "#0B3A8C",
        "SIDEBAR_BG_2": "#082C6C",
        "SIDEBAR_TEXT": "#EFF6FF",
        "SIDEBAR_BORDER": "rgba(255, 255, 255, 0.10)",
        "SUCCESS": "#16A34A",
        "DANGER": "#DC2626",
        "WARNING": "#D97706",
        "INFO": "#2563EB",
        "PLOT_GRID": "rgba(148, 163, 184, 0.18)",
        "BORDER_SOFT": "rgba(148, 163, 184, 0.20)",
        "SHADOW": "0 12px 30px rgba(15, 23, 42, 0.10)",
        "ACTIVE_NAV_TEXT": "#1D4ED8",
        "CHIP_BG": "#EFF6FF",
        "CHIP_TEXT": "#1E3A8A",
        "CHIP_BORDER": "rgba(30, 58, 138, 0.14)",
    }


def build_global_css(modo: str = "General") -> str:
    theme = get_theme_tokens(modo)

    css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    :root {
        --app-bg-start: __APP_BG_START__;
        --app-bg-end: __APP_BG_END__;
        --text-main: __TEXT_MAIN__;
        --text-soft: __TEXT_SOFT__;
        --text-muted: __TEXT_MUTED__;
        --text-inverse: __TEXT_INVERSE__;
        --accent-main: __ACCENT_MAIN__;
        --accent-second: __ACCENT_SECOND__;
        --accent-soft: __ACCENT_SOFT__;
        --accent-border: __ACCENT_BORDER__;
        --card-bg: __CARD_BG__;
        --panel-bg: __PANEL_BG__;
        --panel-bg-2: __PANEL_BG_2__;
        --sidebar-bg: __SIDEBAR_BG__;
        --sidebar-bg-2: __SIDEBAR_BG_2__;
        --sidebar-text: __SIDEBAR_TEXT__;
        --sidebar-border: __SIDEBAR_BORDER__;
        --success: __SUCCESS__;
        --danger: __DANGER__;
        --warning: __WARNING__;
        --info: __INFO__;
        --plot-grid: __PLOT_GRID__;
        --border-soft: __BORDER_SOFT__;
        --shadow-main: __SHADOW__;
        --active-nav-text: __ACTIVE_NAV_TEXT__;
        --chip-bg: __CHIP_BG__;
        --chip-text: __CHIP_TEXT__;
        --chip-border: __CHIP_BORDER__;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background:
            radial-gradient(circle at top right, var(--accent-soft), transparent 22%),
            linear-gradient(180deg, var(--app-bg-start) 0%, var(--app-bg-end) 100%);
        color: var(--text-soft);
    }

    .block-container {
        padding-top: 1.25rem;
        max-width: 1320px;
    }

    h1, h2, h3, h4, h5, h6 {
        color: var(--text-main) !important;
    }

    h1 { font-size: 2.25rem; font-weight: 900; margin-bottom: 0.2rem; letter-spacing: -0.02em; }
    h2 { font-size: 1.28rem; font-weight: 900; margin-top: 1.3rem; margin-bottom: 0.4rem; letter-spacing: -0.01em; }
    h3 { font-size: 1.04rem; font-weight: 800; }

    .stMarkdown, .stMarkdown p, .stMarkdown li, p, label {
        color: var(--text-soft) !important;
        font-weight: 500 !important;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--sidebar-bg) 0%, var(--sidebar-bg-2) 100%) !important;
        border-right: 1px solid var(--sidebar-border);
    }

    [data-testid="stSidebar"] > div:first-child {
        background: linear-gradient(180deg, var(--sidebar-bg) 0%, var(--sidebar-bg-2) 100%) !important;
    }

    [data-testid="stSidebar"] * {
        color: var(--sidebar-text) !important;
    }

    [data-testid="stSidebarNav"] a {
        background: rgba(255, 255, 255, 0.10);
        border: 1px solid rgba(255, 255, 255, 0.14);
        border-radius: 16px;
        padding: 0.8rem 0.95rem;
        min-height: 48px;
        display: flex;
        align-items: center;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.10);
        transition: all 0.18s ease;
        font-weight: 700;
    }

    [data-testid="stSidebarNav"] a:hover {
        background: rgba(255, 255, 255, 0.16);
        border-color: rgba(255, 255, 255, 0.24);
        transform: translateY(-1px);
    }

    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: #ffffff;
        border: 1px solid rgba(255, 255, 255, 0.85);
        box-shadow: 0 8px 18px rgba(0, 0, 0, 0.14);
    }

    [data-testid="stSidebarNav"] a[aria-current="page"] span,
    [data-testid="stSidebarNav"] a[aria-current="page"] p,
    [data-testid="stSidebarNav"] a[aria-current="page"] div {
        color: var(--active-nav-text) !important;
        font-weight: 800 !important;
    }

    [data-testid="stSidebarNav"] > div:first-child {
        display: none;
    }

    .sidebar-brand-wrap {
        margin-bottom: 0.85rem;
    }

    .sidebar-brand {
        background: #ffffff;
        border: 1px solid rgba(255, 255, 255, 0.70);
        border-radius: 20px;
        padding: 0.95rem 0.9rem;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.12);
    }

    .sidebar-brand-inner {
        display: flex;
        align-items: center;
        gap: 0.8rem;
    }

    .sidebar-brand-logo {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        object-fit: contain;
        flex-shrink: 0;
    }

    .sidebar-brand-title {
        font-size: 1.35rem;
        line-height: 1.02;
        font-weight: 800;
        color: var(--accent-main) !important;
        margin: 0;
    }

    .sidebar-brand-subtitle {
        font-size: 0.82rem;
        color: #64748b !important;
        margin-top: 0.18rem;
        font-weight: 600;
    }

    [data-testid="stSidebar"] .streamlit-expanderHeader {
        background: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.70) !important;
        border-radius: 20px !important;
        padding: 0.85rem 0.95rem !important;
        font-weight: 800 !important;
        color: var(--accent-main) !important;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.12);
    }

    [data-testid="stSidebar"] details > div {
        background: linear-gradient(180deg, #EAF2FF 0%, #DCEBFF 100%) !important;
        border: 1px solid rgba(37, 99, 235, 0.18) !important;
        border-top: none !important;
        border-bottom-left-radius: 20px !important;
        border-bottom-right-radius: 20px !important;
        padding: 0.95rem 0.9rem 0.85rem 0.9rem !important;
        color: #0F172A !important;
        box-shadow: 0 10px 20px rgba(37, 99, 235, 0.08) !important;
    }

    [data-testid="stSidebar"] details summary {
        background: #ffffff !important;
        border: 1px solid rgba(37, 99, 235, 0.18) !important;
        border-radius: 20px !important;
    }

    [data-testid="stSidebar"] details[open] summary {
        border-bottom-left-radius: 0 !important;
        border-bottom-right-radius: 0 !important;
    }

    [data-testid="stSidebar"] details > div *,
    [data-testid="stSidebar"] .stRadio label,
    [data-testid="stSidebar"] .stCheckbox label,
    [data-testid="stSidebar"] .stCheckbox p,
    [data-testid="stSidebar"] .stCheckbox span,
    [data-testid="stSidebar"] .stCheckbox div,
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stMultiSelect label,
    [data-testid="stSidebar"] .stTextInput label,
    [data-testid="stSidebar"] .stDateInput label,
    [data-testid="stSidebar"] .stNumberInput label,
    [data-testid="stSidebar"] .stSlider label,
    [data-testid="stSidebar"] .stSlider span,
    [data-testid="stSidebar"] .stSlider div {
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        font-weight: 700 !important;
        opacity: 1 !important;
    }

    [data-testid="stSidebar"] .stSelectbox > div > div,
    [data-testid="stSidebar"] .stMultiSelect > div > div,
    [data-testid="stSidebar"] .stTextInput > div > div,
    [data-testid="stSidebar"] .stDateInput > div > div,
    [data-testid="stSidebar"] .stNumberInput > div {
        background: #ffffff !important;
        border-radius: 12px !important;
        border: 1px solid #d6dbe3 !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, var(--accent-main), var(--accent-second));
        color: white;
        border-radius: 12px;
        padding: 0.5rem 1rem;
        font-weight: 700;
        border: none;
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.12);
    }

    div[data-testid="stDataFrame"] {
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid var(--border-soft);
        background: #ffffff;
        box-shadow: var(--shadow-main);
    }

    div[data-testid="stPlotlyChart"] {
        border-radius: 20px;
        overflow: hidden;
        background: linear-gradient(180deg, #ffffff 0%, var(--panel-bg-2) 100%);
        border: 1px solid var(--border-soft);
        padding: 0.55rem 0.45rem 0.15rem 0.45rem;
        box-shadow: var(--shadow-main);
        margin-bottom: 0.55rem;
    }

    .ui-help {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        margin-left: 0.45rem;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        font-size: 0.72rem;
        font-weight: 800;
        color: var(--accent-main);
        background: var(--accent-soft);
        border: 1px solid var(--accent-border);
        cursor: help;
        vertical-align: middle;
        flex-shrink: 0;
    }

    .ui-divider {
        border: none;
        height: 1px;
        background: rgba(148, 163, 184, 0.22);
        margin: 0.55rem 0 0.95rem 0;
    }

    .ui-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.46rem 0.82rem;
        border-radius: 999px;
        background: var(--chip-bg);
        border: 1px solid var(--chip-border);
        color: var(--chip-text) !important;
        font-size: 0.82rem;
        font-weight: 800;
        margin-right: 0.45rem;
        margin-bottom: 0.45rem;
    }

    .ui-note {
        background: linear-gradient(180deg, #ffffff 0%, var(--panel-bg-2) 100%);
        padding: 1rem 1.05rem;
        border-left: 4px solid var(--accent-main);
        border-radius: 16px;
        margin-bottom: 1rem;
        border: 1px solid var(--border-soft);
        box-shadow: var(--shadow-main);
        color: var(--text-soft) !important;
        font-weight: 600;
    }

    .ui-hero {
        background: linear-gradient(
            135deg,
            color-mix(in srgb, var(--accent-main) 11%, white),
            color-mix(in srgb, var(--accent-second) 8%, white)
        );
        padding: 1.6rem;
        border-radius: 22px;
        margin-bottom: 1rem;
        border: 1px solid var(--accent-border);
        box-shadow: var(--shadow-main);
    }

    .ui-hero-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.8rem;
        flex-wrap: wrap;
        margin-bottom: 0.25rem;
    }

    .ui-mode-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-height: 34px;
        padding: 0.42rem 0.92rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 900;
        color: #FFFFFF !important;
        background: linear-gradient(135deg, var(--accent-main), var(--accent-second));
        border: 1px solid rgba(255,255,255,0.35);
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.16);
        white-space: nowrap;
    }

    .ui-kpi-card {
        background: linear-gradient(180deg, #ffffff 0%, var(--panel-bg-2) 100%);
        border: 1px solid rgba(148, 163, 184, 0.20);
        border-radius: 20px;
        padding: 1.05rem 1.1rem;
        min-height: 142px;
        box-shadow: 0 12px 26px rgba(15, 23, 42, 0.08);
        transition: all 0.18s ease;
        position: relative;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    .ui-kpi-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 4px;
        background: linear-gradient(90deg, var(--accent-main), var(--accent-second));
    }

    .ui-kpi-title {
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 900;
        color: var(--text-muted) !important;
        line-height: 1.2;
        text-align: left;
        margin-bottom: 0.35rem;
    }

    .ui-kpi-value {
        font-size: 2.15rem;
        font-weight: 900;
        color: var(--text-main) !important;
        line-height: 1.02;
        margin-bottom: 0.35rem;
        letter-spacing: -0.03em;
        text-align: center;
    }

    .ui-kpi-delta {
        font-size: 0.92rem;
        font-weight: 800;
        line-height: 1.3;
        margin-bottom: 0.24rem;
        text-align: center;
    }

    .ui-kpi-delta.pos { color: var(--success) !important; }
    .ui-kpi-delta.neg { color: var(--danger) !important; }
    .ui-kpi-delta.neu { color: var(--text-soft) !important; }

    .ui-kpi-sub {
        font-size: 0.96rem;
        color: var(--text-soft) !important;
        line-height: 1.5;
        margin-top: 0.18rem;
        font-weight: 600;
        text-align: center;
    }

    .ui-test-card {
        background: linear-gradient(180deg, #ffffff 0%, var(--panel-bg-2) 100%);
        border: 1px solid var(--border-soft);
        border-radius: 20px;
        padding: 1.1rem 1.15rem;
        min-height: 160px;
        box-shadow: var(--shadow-main);
        position: relative;
        overflow: hidden;
    }

    .ui-test-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 4px;
        background: linear-gradient(90deg, var(--accent-main), var(--accent-second));
    }

    .ui-test-head {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 0.6rem;
        margin-bottom: 0.8rem;
    }

    .ui-test-title {
        font-size: 1.05rem;
        font-weight: 800;
        color: var(--text-main) !important;
    }

    .ui-test-value {
        font-size: 1.18rem;
        font-weight: 900;
        color: var(--text-main) !important;
        text-align: center;
        margin-bottom: 0.55rem;
    }

    .ui-test-conclusion {
        font-size: 0.98rem;
        font-weight: 700;
        color: var(--text-soft) !important;
        text-align: center;
        line-height: 1.45;
    }

    .ui-test-note {
        margin-top: 0.55rem;
        font-size: 0.88rem;
        font-weight: 600;
        color: var(--text-muted) !important;
        text-align: center;
        line-height: 1.4;
    }

    .ui-plot-head {
        background: linear-gradient(180deg, #ffffff 0%, var(--panel-bg-2) 100%);
        border: 1px solid var(--border-soft);
        border-radius: 18px;
        padding: 1rem 1rem 0.9rem 1rem;
        margin-bottom: 0.65rem;
        box-shadow: var(--shadow-main);
    }

    .ui-plot-head-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.8rem;
        flex-wrap: wrap;
    }

    .ui-plot-title {
        font-size: 1.02rem;
        font-weight: 800;
        color: var(--text-main) !important;
        margin: 0;
    }

    .ui-plot-caption {
        margin-top: 0.42rem;
        font-size: 0.92rem;
        color: var(--text-soft) !important;
        line-height: 1.45;
    }

    .ui-plot-foot {
        background: linear-gradient(180deg, #ffffff 0%, var(--panel-bg-2) 100%);
        border: 1px solid var(--border-soft);
        border-radius: 16px;
        padding: 0.78rem 0.95rem;
        margin-top: 0.1rem;
        margin-bottom: 1rem;
        color: var(--text-soft) !important;
        box-shadow: var(--shadow-main);
    }

    .ui-toolbar-label {
        font-size: 0.82rem;
        font-weight: 800;
        color: var(--text-muted) !important;
        margin-bottom: 0.35rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.55rem;
        background: linear-gradient(180deg, #eef4fb 0%, #e8f0fa 100%);
        border: 1px solid rgba(148, 163, 184, 0.22);
        padding: 0.4rem;
        border-radius: 18px;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
        width: fit-content;
    }

    .stTabs [data-baseweb="tab"] {
        min-height: 44px;
        padding: 0.55rem 1rem !important;
        border-radius: 12px !important;
        background: transparent !important;
        color: var(--text-soft) !important;
        font-weight: 700 !important;
        border: 1px solid transparent !important;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%) !important;
        color: var(--accent-main) !important;
        border: 1px solid rgba(148,163,184,0.24) !important;
        box-shadow: 0 6px 14px rgba(15, 23, 42, 0.08);
    }
    </style>
    """

    for key, value in theme.items():
        css = css.replace(f"__{key}__", value)

    return css