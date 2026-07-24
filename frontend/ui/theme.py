from __future__ import annotations

import base64
from html import escape
from pathlib import Path


def safe_text(text: str | None) -> str:
    if text is None:
        return ""
    return escape(str(text), quote=True)


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
    @import url('https://fonts.googleapis.com/css2family=Inter:wght@300;400;500;600;700;800;900&display=swap');

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

    [data-testid="stSidebarNav"],
    [data-testid="collapsedControl"] {
        display: none !important;
    }

    [data-testid="stSidebar"] {
        display: block !important;
    }

    h1, h2, h3, h4, h5, h6 {
        color: var(--text-main) !important;
    }

    h1 { font-size: 2.25rem; font-weight: 900; margin-bottom: 0.2rem; letter-spacing: 0; }
    h2 { font-size: 1.28rem; font-weight: 900; margin-top: 1.3rem; margin-bottom: 0.4rem; letter-spacing: 0; }
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

    .sidebar-session {
        background: rgba(255, 255, 255, 0.12);
        border: 1px solid rgba(255, 255, 255, 0.16);
        border-radius: 18px;
        padding: 0.9rem;
        margin: 0.8rem 0 1rem 0;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.10);
    }

    .sidebar-session-name {
        color: #ffffff !important;
        font-size: 0.98rem;
        font-weight: 900;
        line-height: 1.2;
        margin-bottom: 0.2rem;
    }

    .sidebar-session-role {
        display: inline-flex;
        align-items: center;
        min-height: 26px;
        padding: 0.22rem 0.62rem;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.18);
        border: 1px solid rgba(255, 255, 255, 0.18);
        color: #ffffff !important;
        font-size: 0.76rem;
        font-weight: 800;
        margin-top: 0.35rem;
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

    [data-testid="stSidebar"] .stNumberInput input,
    [data-testid="stSidebar"] .stTextInput input,
    [data-testid="stSidebar"] .stDateInput input {
        background: #ffffff !important;
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        caret-color: #0F172A !important;
        font-weight: 600 !important;
        opacity: 1 !important;
    }

    [data-testid="stSidebar"] .stNumberInput button,
    [data-testid="stSidebar"] .stDateInput button,
    [data-testid="stSidebar"] .stSelectbox button {
        color: #8A1538 !important;
        background: transparent !important;
    }

    [data-testid="stSidebar"] .stNumberInput button svg,
    [data-testid="stSidebar"] .stDateInput button svg,
    [data-testid="stSidebar"] .stSelectbox button svg {
        fill: #8A1538 !important;
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

    .stButton > button:hover {
        border: none;
        filter: brightness(1.03);
        transform: translateY(-1px);
    }

    .login-shell {
        min-height: 76vh;
        display: flex;
        flex-direction: column;
        justify-content: center;
        gap: 1rem;
    }

    .login-topbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        padding: 1rem 1.1rem;
        border-radius: 18px;
        background: #ffffff;
        border: 1px solid var(--border-soft);
        box-shadow: var(--shadow-main);
        margin-bottom: 0.7rem;
    }

    .login-brand {
        display: flex;
        align-items: center;
        gap: 0.85rem;
    }

    .login-logo {
        width: 54px;
        height: 54px;
        object-fit: contain;
        border-radius: 50%;
        border: 1px solid var(--border-soft);
        background: #ffffff;
    }

    .login-brand-title {
        font-size: 1rem;
        font-weight: 900;
        color: var(--text-main) !important;
        line-height: 1.15;
    }

    .login-brand-subtitle {
        font-size: 0.82rem;
        font-weight: 700;
        color: var(--text-muted) !important;
        margin-top: 0.12rem;
    }

    .login-status {
        display: inline-flex;
        align-items: center;
        min-height: 32px;
        padding: 0.34rem 0.78rem;
        border-radius: 999px;
        background: #E8F7EF;
        border: 1px solid rgba(22, 163, 74, 0.20);
        color: #166534 !important;
        font-size: 0.8rem;
        font-weight: 900;
    }

    .login-copy {
        background: linear-gradient(180deg, #ffffff 0%, #F7FAFC 100%);
        border: 1px solid var(--border-soft);
        border-radius: 22px;
        padding: 1.35rem;
        box-shadow: var(--shadow-main);
        margin-bottom: 0.8rem;
    }

    .login-eyebrow {
        color: var(--accent-main) !important;
        font-size: 0.78rem;
        font-weight: 900;
        letter-spacing: 0;
        text-transform: uppercase;
        margin-bottom: 0.45rem;
    }

    .login-title {
        color: var(--text-main) !important;
        font-size: 2.05rem;
        line-height: 1.08;
        font-weight: 900;
        letter-spacing: 0;
        margin-bottom: 0.65rem;
    }

    .login-subtitle {
        color: var(--text-soft) !important;
        font-size: 1rem;
        font-weight: 600;
        line-height: 1.55;
    }

    .login-feature-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.85rem;
        margin-top: 1rem;
    }

    .login-feature {
        background: #ffffff;
        border: 1px solid var(--border-soft);
        border-radius: 16px;
        padding: 0.88rem;
    }

    .login-feature strong {
        display: block;
        color: var(--text-main) !important;
        font-size: 0.9rem;
        margin-bottom: 0.25rem;
    }

    .login-feature span {
        color: var(--text-muted) !important;
        font-size: 0.84rem;
        font-weight: 600;
        line-height: 1.35;
    }

    div[data-testid="stForm"] {
        background: #ffffff;
        border: 1px solid var(--border-soft);
        border-radius: 20px;
        padding: 1.05rem 1.05rem 1.1rem 1.05rem;
        box-shadow: var(--shadow-main);
    }

    .home-panel,
    .module-card,
    .session-panel {
        background: linear-gradient(180deg, #ffffff 0%, #F7FAFC 100%);
        border: 1px solid var(--border-soft);
        border-radius: 18px;
        padding: 1.05rem;
        box-shadow: var(--shadow-main);
        min-height: 150px;
        margin-bottom: 0.9rem;
    }

    .home-panel-title,
    .module-card-title,
    .session-panel-title {
        color: var(--text-main) !important;
        font-size: 1.02rem;
        font-weight: 900;
        line-height: 1.25;
        margin-bottom: 0.35rem;
    }

    .home-panel-body,
    .module-card-body,
    .session-panel-body {
        color: var(--text-soft) !important;
        font-size: 0.92rem;
        font-weight: 600;
        line-height: 1.5;
    }

    .module-card-kicker {
        color: var(--accent-main) !important;
        font-size: 0.76rem;
        font-weight: 900;
        text-transform: uppercase;
        letter-spacing: 0;
        margin-bottom: 0.45rem;
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
        padding: 1rem 1.1rem;
        border-left: 4px solid var(--accent-main);
        border-radius: 16px;
        margin-bottom: 1rem;
        border: 1px solid var(--border-soft);
        box-shadow: var(--shadow-main);
        color: var(--text-soft) !important;
        font-weight: 600;
        line-height: 1.55;
    }

    .ui-info-card {
        display: grid;
        grid-template-columns: 7px minmax(0, 1fr);
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FBFF 100%);
        border: 1px solid rgba(148, 163, 184, 0.22);
        border-radius: 16px;
        box-shadow: 0 12px 28px rgba(15, 23, 42, 0.08);
        overflow: hidden;
        margin: 0.65rem 0 1rem 0;
    }

    .ui-info-accent {
        background: linear-gradient(180deg, var(--accent-main), var(--accent-second));
    }

    .ui-info-content {
        padding: 1rem 1.1rem 1.05rem 1.05rem;
    }

    .ui-info-kicker {
        display: inline-flex;
        align-items: center;
        min-height: 24px;
        padding: 0.16rem 0.58rem;
        border-radius: 999px;
        background: var(--accent-soft);
        border: 1px solid var(--accent-border);
        color: var(--accent-main) !important;
        font-size: 0.70rem;
        font-weight: 900;
        text-transform: uppercase;
        margin-bottom: 0.55rem;
    }

    .ui-info-title {
        color: var(--text-main) !important;
        font-size: 1rem;
        font-weight: 900;
        line-height: 1.25;
        margin-bottom: 0.48rem;
    }

    .ui-info-copy {
        display: grid;
        gap: 0.42rem;
    }

    .ui-info-body {
        margin: 0 !important;
        color: var(--text-soft) !important;
        font-size: 0.93rem;
        font-weight: 600 !important;
        line-height: 1.55;
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
        letter-spacing: 0;
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
        letter-spacing: 0;
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
        padding: 0.85rem 1rem;
        margin-top: 0.1rem;
        margin-bottom: 1rem;
        color: var(--text-soft) !important;
        box-shadow: var(--shadow-main);
        border-left: 4px solid var(--accent-main);
        font-weight: 650;
        line-height: 1.55;
    }

    .ui-toolbar-label {
        font-size: 0.82rem;
        font-weight: 800;
        color: var(--text-muted) !important;
        margin-bottom: 0.35rem;
        text-transform: uppercase;
        letter-spacing: 0;
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

    .top-shell {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        border: 1px solid var(--border-soft);
        border-radius: 18px;
        padding: 0.85rem 1rem;
        margin-bottom: 0.8rem;
        background: linear-gradient(180deg, var(--panel-bg) 0%, var(--panel-bg-2) 100%);
        box-shadow: var(--shadow-main);
    }

    .top-brand {
        color: var(--text-main) !important;
        font-size: 1.05rem;
        font-weight: 900;
        line-height: 1.15;
    }

    .top-subtitle {
        color: var(--text-muted) !important;
        font-size: 0.84rem;
        font-weight: 700;
        margin-top: 0.1rem;
    }

    .top-session {
        display: flex;
        align-items: center;
        gap: 0.55rem;
        flex-wrap: wrap;
        justify-content: flex-end;
        color: var(--text-soft) !important;
        font-size: 0.86rem;
        font-weight: 700;
    }

    .top-session strong {
        display: inline-flex;
        align-items: center;
        min-height: 30px;
        padding: 0.25rem 0.65rem;
        border-radius: 999px;
        color: #ffffff !important;
        background: linear-gradient(135deg, var(--accent-main), var(--accent-second));
        font-size: 0.78rem;
        font-weight: 900;
    }

    .nav-ordered-label {
        color: var(--text-muted) !important;
        font-size: 0.78rem;
        font-weight: 900;
        text-transform: uppercase;
        letter-spacing: 0;
        margin: 0.15rem 0 0.42rem 0;
    }

    div[data-testid="stPageLink"] a {
        min-height: 42px;
        border-radius: 999px;
        border: 1px solid var(--accent-border);
        background: linear-gradient(180deg, var(--panel-bg) 0%, var(--panel-bg-2) 100%);
        color: var(--text-main) !important;
        font-weight: 850;
        justify-content: center;
        box-shadow: 0 6px 14px rgba(15, 23, 42, 0.05);
        margin-bottom: 0.35rem;
        padding-left: 0.6rem;
        padding-right: 0.6rem;
    }

    div[data-testid="stPageLink"] a:hover {
        border-color: var(--accent-border);
        color: var(--accent-main) !important;
        transform: translateY(-1px);
    }

    .metric-band {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.85rem;
        margin: 0.8rem 0 1rem 0;
    }

    .login-shell {
        min-height: 82vh;
        justify-content: center;
    }

    .login-stage {
        position: relative;
        overflow: hidden;
        border-radius: 26px;
        min-height: 620px;
        padding: 1.35rem;
        background:
            radial-gradient(circle at 16% 18%, rgba(35, 116, 255, 0.48), transparent 24%),
            radial-gradient(circle at 82% 32%, rgba(31, 212, 255, 0.36), transparent 20%),
            linear-gradient(135deg, #071536 0%, #04102B 54%, #081A43 100%);
        border: 1px solid rgba(129, 180, 255, 0.22);
        box-shadow: 0 28px 70px rgba(4, 16, 43, 0.34);
    }

    .login-stage::before {
        content: "";
        position: absolute;
        inset: 0;
        background:
            linear-gradient(rgba(255,255,255,0.035) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.035) 1px, transparent 1px);
        background-size: 36px 36px;
        mask-image: linear-gradient(90deg, black 0%, rgba(0,0,0,0.25) 75%, transparent 100%);
        pointer-events: none;
    }

    .login-glow {
        position: absolute;
        width: 190px;
        height: 190px;
        border-radius: 999px;
        background: radial-gradient(circle, rgba(61, 220, 255, 0.92), rgba(39, 118, 255, 0.24) 52%, transparent 70%);
        filter: blur(1px);
        opacity: 0.9;
        pointer-events: none;
    }

    .login-glow.one { right: 9%; top: 18%; }
    .login-glow.two { left: 7%; bottom: 9%; width: 150px; height: 150px; opacity: 0.72; }

    .login-frame {
        position: relative;
        z-index: 1;
        display: grid;
        grid-template-columns: minmax(0, 1.05fr) minmax(320px, 0.78fr);
        gap: 1.15rem;
        align-items: center;
        min-height: 528px;
    }

    .login-copy,
    .login-card {
        background: rgba(8, 24, 58, 0.62);
        border: 1px solid rgba(180, 218, 255, 0.18);
        border-radius: 22px;
        padding: 1.25rem;
        backdrop-filter: blur(18px);
        box-shadow: 0 20px 45px rgba(0, 0, 0, 0.24);
    }

    .login-copy {
        background: transparent;
        border-color: transparent;
        box-shadow: none;
        padding: 1.8rem;
    }

    .login-eyebrow,
    .login-title,
    .login-subtitle,
    .login-brand-title,
    .login-brand-subtitle {
        color: #F8FBFF !important;
    }

    .login-eyebrow {
        color: #64D9FF !important;
        text-transform: uppercase;
        font-size: 0.78rem;
        font-weight: 900;
        margin-bottom: 0.65rem;
    }

    .login-title {
        font-size: 2.45rem;
        line-height: 1.05;
        font-weight: 900;
        max-width: 560px;
    }

    .login-subtitle {
        color: #BED3F7 !important;
        max-width: 620px;
        margin-top: 0.85rem;
    }

    .login-logo {
        background: rgba(255,255,255,0.92);
    }

    .login-feature-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .login-feature {
        background: rgba(255,255,255,0.07);
        border-color: rgba(255,255,255,0.12);
    }

    .login-feature strong { color: #FFFFFF !important; }
    .login-feature span { color: #BED3F7 !important; }

    .login-card div[data-testid="stForm"] {
        background: transparent;
        border: none;
        box-shadow: none;
        padding: 0;
    }

    .login-card label,
    .login-card p {
        color: #D8E6FF !important;
    }

    .login-card input {
        background: rgba(255,255,255,0.08) !important;
        border: 1px solid rgba(255,255,255,0.24) !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }

    .login-card-title {
        color: #FFFFFF !important;
        font-size: 1.4rem;
        font-weight: 900;
        margin-bottom: 0.15rem;
    }

    .login-card-subtitle {
        color: #AFC5EA !important;
        font-size: 0.9rem;
        font-weight: 650;
        margin-bottom: 1.1rem;
    }

    .login-trust-row {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
        margin-top: 1rem;
    }

    .login-trust {
        border-radius: 999px;
        border: 1px solid rgba(255,255,255,0.14);
        background: rgba(255,255,255,0.07);
        color: #D9EAFF !important;
        padding: 0.35rem 0.68rem;
        font-size: 0.78rem;
        font-weight: 800;
    }

    @media (max-width: 860px) {
        .login-frame {
            grid-template-columns: 1fr;
            min-height: auto;
        }

        .login-title {
            font-size: 2rem;
        }

        .login-copy {
            padding: 1.1rem;
        }
    }

    @media (prefers-color-scheme: dark) {
        :root {
            --app-bg-start: #07111F;
            --app-bg-end: #0B1424;
            --text-main: #F8FAFC;
            --text-soft: #CBD5E1;
            --text-muted: #94A3B8;
            --accent-main: #38BDF8;
            --accent-second: #2563EB;
            --accent-soft: rgba(56, 189, 248, 0.14);
            --accent-border: rgba(56, 189, 248, 0.24);
            --card-bg: #111827;
            --panel-bg: #111827;
            --panel-bg-2: #0F172A;
            --border-soft: rgba(148, 163, 184, 0.22);
            --shadow-main: 0 16px 36px rgba(0, 0, 0, 0.30);
            --chip-bg: rgba(56, 189, 248, 0.12);
            --chip-text: #BAE6FD;
            --chip-border: rgba(56, 189, 248, 0.24);
        }

        .login-topbar,
        .home-panel,
        .module-card,
        .session-panel,
        .ui-note,
        .ui-hero,
        .ui-kpi-card,
        .ui-test-card,
        .ui-plot-head,
        .ui-plot-foot,
        div[data-testid="stDataFrame"],
        div[data-testid="stPlotlyChart"],
        div[data-testid="stForm"],
        .top-shell {
            background: linear-gradient(180deg, #111827 0%, #0F172A 100%) !important;
            border-color: rgba(148, 163, 184, 0.22) !important;
        }

        .stTabs [data-baseweb="tab-list"] {
            background: rgba(15, 23, 42, 0.92) !important;
            border-color: rgba(148, 163, 184, 0.22) !important;
        }

        .stTabs [data-baseweb="tab"] {
            color: #CBD5E1 !important;
        }

        .stTabs [aria-selected="true"] {
            background: #111827 !important;
            color: #7DD3FC !important;
        }

        div[data-testid="stPageLink"] a {
            background: linear-gradient(180deg, #111827 0%, #0F172A 100%) !important;
            border-color: rgba(148, 163, 184, 0.22) !important;
            color: #E2E8F0 !important;
        }

        .stTextInput input,
        .stNumberInput input,
        .stSelectbox div,
        .stMultiSelect div,
        .stDateInput input {
            background-color: #0F172A !important;
            color: #F8FAFC !important;
            -webkit-text-fill-color: #F8FAFC !important;
        }
    }

    div[data-testid="stDataFrame"] {
        border-radius: 18px !important;
        overflow: hidden !important;
        border: 1px solid rgba(148, 163, 184, 0.24) !important;
        box-shadow: 0 14px 30px rgba(15, 23, 42, 0.12) !important;
    }

    div[data-testid="stDataFrame"] * {
        font-size: 0.82rem !important;
        font-weight: 650 !important;
    }

    div[data-testid="stDataFrame"] [role="columnheader"] {
        background: linear-gradient(135deg, var(--accent-main), var(--accent-second)) !important;
        color: #ffffff !important;
        font-weight: 900 !important;
    }

    .sidebar-user-card {
        background: linear-gradient(180deg, #ffffff 0%, #F7FAFC 100%);
        border: 1px solid rgba(148, 163, 184, 0.24);
        border-radius: 18px;
        padding: 0.95rem;
        margin: 0.65rem 0 0.75rem 0;
        box-shadow: 0 12px 26px rgba(15, 23, 42, 0.10);
    }

    .sidebar-user-eyebrow {
        color: var(--accent-main) !important;
        font-size: 0.72rem;
        font-weight: 900;
        text-transform: uppercase;
        letter-spacing: 0.02em;
        margin-bottom: 0.35rem;
    }

    .sidebar-user-name {
        color: #0F172A !important;
        font-size: 0.96rem;
        font-weight: 900;
        line-height: 1.25;
        margin-bottom: 0.25rem;
    }

    .sidebar-user-role {
        display: inline-flex;
        padding: 0.22rem 0.58rem;
        border-radius: 999px;
        background: #EAF2FF;
        border: 1px solid rgba(37, 99, 235, 0.18);
        color: #1D4ED8 !important;
        font-size: 0.72rem;
        font-weight: 900;
        margin-bottom: 0.65rem;
    }

    .sidebar-user-grid {
        display: grid;
        grid-template-columns: 1fr;
        gap: 0.45rem;
    }

    .sidebar-user-grid div {
        background: #F8FAFC;
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 12px;
        padding: 0.55rem 0.65rem;
    }

    .sidebar-user-grid span {
        display: block;
        color: #64748B !important;
        font-size: 0.70rem;
        font-weight: 850;
        text-transform: uppercase;
        margin-bottom: 0.12rem;
    }

    .sidebar-user-grid strong {
        display: block;
        color: #0F172A !important;
        font-size: 0.86rem;
        font-weight: 900;
    }

    .sidebar-portfolio-card {
        margin-top: 0.75rem;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #07111F 0%, #0B1424 100%) !important;
    }

    [data-testid="stSidebar"] .stToggle label,
    [data-testid="stSidebar"] .stToggle p,
    [data-testid="stSidebar"] .stForm label,
    [data-testid="stSidebar"] .stForm p,
    [data-testid="stSidebar"] .stCaptionContainer,
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] .stMarkdown p {
        color: #E2E8F0 !important;
        -webkit-text-fill-color: #E2E8F0 !important;
    }

    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea {
        background: #FFFFFF !important;
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        caret-color: #0F172A !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 10px !important;
    }

    [data-testid="stSidebar"] [data-baseweb="select"] div,
    [data-testid="stSidebar"] [data-baseweb="input"] div {
        background: #FFFFFF !important;
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
    }

    [data-testid="stSidebar"] button {
        font-weight: 850 !important;
    }

    .sidebar-user-card {
        background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(248,250,252,0.98) 100%);
        border: 1px solid rgba(148, 163, 184, 0.22);
        border-radius: 18px;
        padding: 0.95rem;
        margin: 0.70rem 0 0.75rem 0;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.10);
    }

    .sidebar-user-eyebrow {
        color: #64748B !important;
        font-size: 0.68rem;
        font-weight: 900;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.38rem;
    }

    .sidebar-user-name {
        color: #0F172A !important;
        font-size: 1.00rem;
        font-weight: 900;
        line-height: 1.25;
        margin-bottom: 0.32rem;
    }

    .sidebar-user-role {
        display: inline-flex;
        padding: 0.24rem 0.58rem;
        border-radius: 999px;
        background: #EAF2FF;
        border: 1px solid rgba(37, 99, 235, 0.16);
        color: #2563EB !important;
        font-size: 0.72rem;
        font-weight: 900;
        margin-bottom: 0.72rem;
    }

    .sidebar-user-grid {
        display: grid;
        grid-template-columns: 1fr;
        gap: 0.45rem;
    }

    .sidebar-user-grid div {
        background: #F8FAFC;
        border: 1px solid rgba(148, 163, 184, 0.20);
        border-radius: 12px;
        padding: 0.55rem 0.65rem;
    }

    .sidebar-user-grid span {
        display: block;
        color: #64748B !important;
        font-size: 0.70rem;
        font-weight: 850;
        text-transform: uppercase;
        margin-bottom: 0.14rem;
    }

    .sidebar-user-grid strong {
        display: block;
        color: #0F172A !important;
        font-size: 0.88rem;
        font-weight: 900;
    }

    .sidebar-portfolio-card {
        margin-top: 0.80rem;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0F3D91 0%, #123C88 100%) !important;
    }

    [data-testid="stSidebar"] .stExpander {
        background: rgba(255,255,255,0.08) !important;
        border: 1px solid rgba(255,255,255,0.14) !important;
        border-radius: 14px !important;
    }

    [data-testid="stSidebar"] .stExpander summary,
    [data-testid="stSidebar"] .stExpander label,
    [data-testid="stSidebar"] .stExpander p,
    [data-testid="stSidebar"] .stCaptionContainer,
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] .stMarkdown p {
        color: #F8FAFC !important;
        -webkit-text-fill-color: #F8FAFC !important;
    }

    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea {
        background: #FFFFFF !important;
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        caret-color: #0F172A !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 10px !important;
    }

    [data-testid="stSidebar"] [data-baseweb="input"] input,
    [data-testid="stSidebar"] [data-baseweb="select"] input {
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
    }

    [data-testid="stSidebar"] [data-baseweb="select"] > div,
    [data-testid="stSidebar"] [data-baseweb="input"] > div {
        background: #FFFFFF !important;
        color: #0F172A !important;
        border-radius: 10px !important;
    }

    [data-testid="stSidebar"] .stSlider label,
    [data-testid="stSidebar"] .stNumberInput label,
    [data-testid="stSidebar"] .stSelectbox label {
        color: #F8FAFC !important;
        -webkit-text-fill-color: #F8FAFC !important;
        font-weight: 800 !important;
    }

    [data-testid="stSidebar"] button {
        font-weight: 850 !important;
    }

    header[data-testid="stHeader"] {
        background: transparent !important;
        box-shadow: none !important;
        border-bottom: none !important;
    }

    div[data-testid="stToolbar"] {
        background: transparent !important;
    }


    /* Reparacin final barra lateral */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0B3A89 0%, #082B68 100%) !important;
    }

    [data-testid="stSidebar"] * {
        color: #F8FAFC !important;
        -webkit-text-fill-color: #F8FAFC !important;
    }

    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea,
    [data-testid="stSidebar"] [data-baseweb="input"] input,
    [data-testid="stSidebar"] [data-baseweb="select"] input {
        background: #FFFFFF !important;
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        caret-color: #0F172A !important;
    }

    [data-testid="stSidebar"] [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.16) !important;
        border-radius: 14px !important;
        padding: 0.65rem !important;
    }

    [data-testid="stSidebar"] details {
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.16) !important;
        border-radius: 14px !important;
        padding: 0.25rem 0.45rem !important;
    }

    header[data-testid="stHeader"] {
        background: transparent !important;
        box-shadow: none !important;
        border-bottom: none !important;
    }

    div[data-testid="stToolbar"] {
        background: transparent !important;
    }

    .sidebar-profile-card {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.16);
        border-radius: 18px;
        padding: 1rem 0.95rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 10px 24px rgba(0, 0, 0, 0.18);
    }

    .sidebar-profile-title {
        color: #F8FAFC;
        font-size: 1.05rem;
        font-weight: 700;
        margin-bottom: 0.85rem;
    }

    .sidebar-profile-grid {
        display: grid;
        grid-template-columns: 1fr;
        gap: 0.65rem;
    }

    .sidebar-profile-item {
        background: rgba(255, 255, 255, 0.92);
        border: 1px solid rgba(15, 23, 42, 0.10);
        border-radius: 14px;
        padding: 0.7rem 0.8rem;
    }

    .sidebar-profile-label {
        display: block;
        font-size: 0.75rem;
        font-weight: 700;
        color: #475569 !important;
        margin-bottom: 0.2rem;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }

    .sidebar-profile-value {
        display: block;
        font-size: 0.94rem;
        font-weight: 700;
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
    }

    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea,
    [data-testid="stSidebar"] select,
    [data-testid="stSidebar"] [data-baseweb="input"] input,
    [data-testid="stSidebar"] [data-baseweb="base-input"] input,
    [data-testid="stSidebar"] [data-baseweb="select"] > div,
    [data-testid="stSidebar"] [data-baseweb="select"] span {
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        caret-color: #0F172A !important;
    }

    [data-testid="stSidebar"] [data-baseweb="input"] {
        background: #FFFFFF !important;
        border-radius: 12px !important;
    }

    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background: #FFFFFF !important;
        border-radius: 12px !important;
    }

    [data-testid="stSidebar"] svg {
        color: inherit;
    }
    /* =========================================================
       FIX FINAL: contraste real en sidebar
       ========================================================= */

    /* Tarjetas blancas del usuario y del logo */
    [data-testid="stSidebar"] .sidebar-profile-card,
    [data-testid="stSidebar"] .sidebar-user-card,
    [data-testid="stSidebar"] .sidebar-brand,
    [data-testid="stSidebar"] .sidebar-brand-card,
    [data-testid="stSidebar"] .brand-card,
    [data-testid="stSidebar"] div.sidebar-profile-item,
    [data-testid="stSidebar"] div.sidebar-user-grid div {
        background: rgba(255, 255, 255, 0.96) !important;
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        border-color: rgba(15, 23, 42, 0.12) !important;
    }

    /* Texto dentro de tarjetas blancas */
    [data-testid="stSidebar"] .sidebar-profile-card *,
    [data-testid="stSidebar"] .sidebar-user-card *,
    [data-testid="stSidebar"] .sidebar-brand *,
    [data-testid="stSidebar"] .sidebar-brand-card *,
    [data-testid="stSidebar"] .brand-card *,
    [data-testid="stSidebar"] .sidebar-profile-item *,
    [data-testid="stSidebar"] .sidebar-user-grid div * {
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        opacity: 1 !important;
        text-shadow: none !important;
    }

    /* Etiquetas secundarias dentro de tarjetas */
    [data-testid="stSidebar"] .sidebar-profile-label,
    [data-testid="stSidebar"] .sidebar-user-grid span,
    [data-testid="stSidebar"] .sidebar-user-eyebrow,
    [data-testid="stSidebar"] .sidebar-brand p,
    [data-testid="stSidebar"] .sidebar-brand-card p,
    [data-testid="stSidebar"] .brand-card p {
        color: #475569 !important;
        -webkit-text-fill-color: #475569 !important;
        opacity: 1 !important;
    }

    /* Valores fuertes dentro de tarjetas */
    [data-testid="stSidebar"] .sidebar-profile-value,
    [data-testid="stSidebar"] .sidebar-user-grid strong,
    [data-testid="stSidebar"] .sidebar-user-name,
    [data-testid="stSidebar"] .sidebar-brand h1,
    [data-testid="stSidebar"] .sidebar-brand h2,
    [data-testid="stSidebar"] .sidebar-brand h3,
    [data-testid="stSidebar"] .sidebar-brand-card h1,
    [data-testid="stSidebar"] .sidebar-brand-card h2,
    [data-testid="stSidebar"] .brand-card h1,
    [data-testid="stSidebar"] .brand-card h2 {
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        opacity: 1 !important;
    }

    /* Expander sobre fondo azul */
    [data-testid="stSidebar"] details,
    [data-testid="stSidebar"] details summary {
        color: #F8FAFC !important;
        -webkit-text-fill-color: #F8FAFC !important;
    }

    [data-testid="stSidebar"] details p,
    [data-testid="stSidebar"] details label,
    [data-testid="stSidebar"] details span {
        color: #F8FAFC !important;
        -webkit-text-fill-color: #F8FAFC !important;
    }

    /* Campos blancos: texto SIEMPRE oscuro */
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea,
    [data-testid="stSidebar"] select,
    [data-testid="stSidebar"] [data-baseweb="input"] input,
    [data-testid="stSidebar"] [data-baseweb="base-input"] input,
    [data-testid="stSidebar"] [data-baseweb="select"] input,
    [data-testid="stSidebar"] [data-baseweb="select"] span,
    [data-testid="stSidebar"] [data-baseweb="select"] div {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        caret-color: #0F172A !important;
        opacity: 1 !important;
    }

    [data-testid="stSidebar"] [data-baseweb="input"] > div,
    [data-testid="stSidebar"] [data-baseweb="base-input"],
    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        border-radius: 12px !important;
    }

    /* Flecha del select en campo blanco */
    [data-testid="stSidebar"] [data-baseweb="select"] svg {
        color: #0F172A !important;
        fill: #0F172A !important;
    }

    /* Botones internos */
    [data-testid="stSidebar"] button {
        opacity: 1 !important;
    }


    /* =========================================================
       FIX FINAL: expander datos personales visible
       ========================================================= */

    [data-testid="stSidebar"] details {
        background: #FFFFFF !important;
        border: 1px solid rgba(15, 23, 42, 0.14) !important;
        border-radius: 16px !important;
        padding: 0.45rem 0.60rem !important;
        box-shadow: 0 10px 24px rgba(0, 0, 0, 0.18) !important;
    }

    [data-testid="stSidebar"] details summary,
    [data-testid="stSidebar"] details summary *,
    [data-testid="stSidebar"] details p,
    [data-testid="stSidebar"] details label,
    [data-testid="stSidebar"] details span,
    [data-testid="stSidebar"] details div,
    [data-testid="stSidebar"] details .stCaptionContainer,
    [data-testid="stSidebar"] details .stCaptionContainer *,
    [data-testid="stSidebar"] details .stMarkdown,
    [data-testid="stSidebar"] details .stMarkdown * {
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        opacity: 1 !important;
        text-shadow: none !important;
    }

    [data-testid="stSidebar"] details summary {
        font-weight: 900 !important;
        font-size: 0.88rem !important;
    }

    [data-testid="stSidebar"] details .stCaptionContainer,
    [data-testid="stSidebar"] details .stCaptionContainer p {
        color: #334155 !important;
        -webkit-text-fill-color: #334155 !important;
        font-weight: 750 !important;
        line-height: 1.35 !important;
    }

    [data-testid="stSidebar"] details input,
    [data-testid="stSidebar"] details textarea,
    [data-testid="stSidebar"] details select,
    [data-testid="stSidebar"] details [data-baseweb="input"] input,
    [data-testid="stSidebar"] details [data-baseweb="base-input"] input,
    [data-testid="stSidebar"] details [data-baseweb="select"] input,
    [data-testid="stSidebar"] details [data-baseweb="select"] span,
    [data-testid="stSidebar"] details [data-baseweb="select"] div {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        caret-color: #0F172A !important;
        opacity: 1 !important;
    }

    [data-testid="stSidebar"] details button,
    [data-testid="stSidebar"] details button *,
    [data-testid="stSidebar"] details [data-testid="stFormSubmitButton"] button,
    [data-testid="stSidebar"] details [data-testid="stFormSubmitButton"] button * {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 900 !important;
    }

    [data-testid="stSidebar"] details svg {
        color: #0F172A !important;
        fill: #0F172A !important;
    }


    /* =========================================================
       FIX DEFINITIVO: ttulo del expander visible
       ========================================================= */

    section[data-testid="stSidebar"] div[data-testid="stExpander"] {
        background: #FFFFFF !important;
        border-radius: 16px !important;
        border: 1px solid rgba(15, 23, 42, 0.14) !important;
        box-shadow: 0 10px 24px rgba(0, 0, 0, 0.18) !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stExpander"] details,
    section[data-testid="stSidebar"] div[data-testid="stExpander"] details summary {
        background: #FFFFFF !important;
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        opacity: 1 !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stExpander"] details summary *,
    section[data-testid="stSidebar"] div[data-testid="stExpander"] details summary p,
    section[data-testid="stSidebar"] div[data-testid="stExpander"] details summary span,
    section[data-testid="stSidebar"] div[data-testid="stExpander"] details summary div,
    section[data-testid="stSidebar"] div[data-testid="stExpander"] details summary label {
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        opacity: 1 !important;
        font-weight: 900 !important;
        text-shadow: none !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stExpander"] details summary svg {
        color: #0F172A !important;
        fill: #0F172A !important;
        stroke: #0F172A !important;
        opacity: 1 !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stExpander"] details[open] summary,
    section[data-testid="stSidebar"] div[data-testid="stExpander"] details[open] summary * {
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        opacity: 1 !important;
    }


    /* =========================================================
       Tarjeta resumen de riesgo en sidebar
       ========================================================= */

    [data-testid="stSidebar"] .sidebar-portfolio-summary {
        background: rgba(255, 255, 255, 0.96) !important;
        border: 1px solid rgba(15, 23, 42, 0.12) !important;
        border-radius: 16px !important;
        padding: 0.85rem !important;
        margin: 0.55rem 0 0.75rem 0 !important;
        box-shadow: 0 10px 24px rgba(0, 0, 0, 0.16) !important;
    }

    [data-testid="stSidebar"] .sidebar-portfolio-summary-title {
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        font-size: 0.90rem !important;
        font-weight: 900 !important;
        margin-bottom: 0.65rem !important;
    }

    [data-testid="stSidebar"] .sidebar-portfolio-summary-grid {
        display: grid !important;
        grid-template-columns: 1fr !important;
        gap: 0.55rem !important;
    }

    [data-testid="stSidebar"] .sidebar-portfolio-summary-item {
        background: #F8FAFC !important;
        border: 1px solid rgba(148, 163, 184, 0.28) !important;
        border-radius: 12px !important;
        padding: 0.62rem 0.70rem !important;
    }

    [data-testid="stSidebar"] .sidebar-portfolio-summary-item span {
        display: block !important;
        color: #64748B !important;
        -webkit-text-fill-color: #64748B !important;
        font-size: 0.68rem !important;
        font-weight: 900 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.04em !important;
        margin-bottom: 0.16rem !important;
    }

    [data-testid="stSidebar"] .sidebar-portfolio-summary-item strong {
        display: block !important;
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        font-size: 0.92rem !important;
        font-weight: 950 !important;
        line-height: 1.25 !important;
    }

    /* =========================================================
       FIX VISUAL: rojo institucional en configuracin portafolio
       ========================================================= */

    /* Chips seleccionados del multiselect de acciones */
    [data-testid="stMain"] [data-baseweb="tag"] {
        background: linear-gradient(135deg, #8A1538 0%, #B91C1C 100%) !important;
        border: 1px solid rgba(255, 255, 255, 0.22) !important;
        border-radius: 999px !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 850 !important;
        box-shadow: 0 8px 18px rgba(138, 21, 56, 0.22) !important;
    }

    [data-testid="stMain"] [data-baseweb="tag"] span,
    [data-testid="stMain"] [data-baseweb="tag"] p,
    [data-testid="stMain"] [data-baseweb="tag"] div {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 850 !important;
    }

    [data-testid="stMain"] [data-baseweb="tag"] svg {
        color: #FFFFFF !important;
        fill: #FFFFFF !important;
        stroke: #FFFFFF !important;
    }

    /* Botones submit de formularios en el contenido principal */
    [data-testid="stMain"] [data-testid="stFormSubmitButton"] button {
        background: linear-gradient(135deg, #8A1538 0%, #B91C1C 100%) !important;
        border: 1px solid rgba(255, 255, 255, 0.18) !important;
        border-radius: 14px !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 900 !important;
        box-shadow: 0 10px 24px rgba(138, 21, 56, 0.24) !important;
    }

    [data-testid="stMain"] [data-testid="stFormSubmitButton"] button:hover {
        background: linear-gradient(135deg, #7A1232 0%, #991B1B 100%) !important;
        border-color: rgba(255, 255, 255, 0.26) !important;
        box-shadow: 0 12px 28px rgba(138, 21, 56, 0.30) !important;
        transform: translateY(-1px);
    }

    [data-testid="stMain"] [data-testid="stFormSubmitButton"] button *,
    [data-testid="stMain"] [data-testid="stFormSubmitButton"] button p {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 900 !important;
    }

    /* =========================================================
       FIX CONTRASTE: graficas claras y controles legibles
       ========================================================= */

    [data-testid="stMain"] div[data-testid="stPlotlyChart"] {
        background: #FFFFFF !important;
        border: 1px solid rgba(148, 163, 184, 0.24) !important;
        border-radius: 16px !important;
        box-shadow: 0 12px 28px rgba(15, 23, 42, 0.10) !important;
    }

    [data-testid="stMain"] div[data-testid="stExpander"] {
        background: linear-gradient(180deg, #FFFFFF 0%, #FFF7FA 100%) !important;
        border: 1px solid rgba(138, 21, 56, 0.34) !important;
        border-radius: 14px !important;
        box-shadow: 0 10px 24px rgba(138, 21, 56, 0.13) !important;
        overflow: hidden !important;
    }

    [data-testid="stMain"] div[data-testid="stExpander"] details,
    [data-testid="stMain"] div[data-testid="stExpander"] summary {
        background: transparent !important;
    }

    [data-testid="stMain"] div[data-testid="stExpander"] summary {
        border-left: 5px solid #8A1538 !important;
        min-height: 46px !important;
        padding-left: 0.75rem !important;
    }

    [data-testid="stMain"] div[data-testid="stExpander"] summary *,
    [data-testid="stMain"] div[data-testid="stExpander"] summary p,
    [data-testid="stMain"] div[data-testid="stExpander"] summary span,
    [data-testid="stMain"] div[data-testid="stExpander"] summary svg {
        color: #8A1538 !important;
        -webkit-text-fill-color: #8A1538 !important;
        stroke: #8A1538 !important;
        opacity: 1 !important;
        font-weight: 900 !important;
    }

    [data-testid="stMain"] div[data-testid="stExpander"] details[open] summary {
        background: #FBE7EF !important;
        border-bottom: 1px solid rgba(138, 21, 56, 0.18) !important;
    }

    [data-testid="stMain"] div[data-testid="stExpander"] details > div {
        background: #FFFFFF !important;
    }

    [data-testid="stMain"] div[data-testid="stExpander"] details > div *,
    [data-testid="stMain"] div[data-testid="stExpander"] details label,
    [data-testid="stMain"] div[data-testid="stExpander"] details p {
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        opacity: 1 !important;
    }

    [data-testid="stMain"] .modebar {
        background: rgba(255, 255, 255, 0.94) !important;
        border: 1px solid rgba(148, 163, 184, 0.24) !important;
        border-radius: 10px !important;
        padding: 0.12rem !important;
    }

    [data-testid="stMain"] .modebar-btn {
        background: #FFFFFF !important;
        border-radius: 8px !important;
    }

    [data-testid="stMain"] .modebar-btn path {
        fill: #0F172A !important;
    }

    [data-testid="stMain"] .modebar-btn:hover {
        background: #EAF2FF !important;
    }

    [data-testid="stMain"] [data-testid="stBaseButton-primary"],
    [data-testid="stMain"] button[kind="primary"],
    [data-testid="stMain"] .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #8A1538 0%, #B91C1C 100%) !important;
        border: 1px solid rgba(138, 21, 56, 0.36) !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 900 !important;
        box-shadow: 0 10px 24px rgba(138, 21, 56, 0.24) !important;
    }

    [data-testid="stMain"] [data-testid="stBaseButton-secondary"],
    [data-testid="stMain"] button[kind="secondary"],
    [data-testid="stMain"] .stButton > button[kind="secondary"] {
        background: #FFFFFF !important;
        border: 1px solid rgba(148, 163, 184, 0.34) !important;
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        font-weight: 850 !important;
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.08) !important;
    }

    [data-testid="stMain"] [data-testid="stBaseButton-secondary"]:hover,
    [data-testid="stMain"] button[kind="secondary"]:hover,
    [data-testid="stMain"] .stButton > button[kind="secondary"]:hover {
        background: #F8FBFF !important;
        border-color: rgba(37, 99, 235, 0.34) !important;
    }

    [data-testid="stMain"] [data-testid="stBaseButton-primary"] *,
    [data-testid="stMain"] button[kind="primary"] * {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        opacity: 1 !important;
    }

    [data-testid="stMain"] [data-testid="stBaseButton-secondary"] *,
    [data-testid="stMain"] button[kind="secondary"] * {
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        opacity: 1 !important;
    }

    [data-testid="stMain"] .stTabs [data-baseweb="tab-list"] {
        background: #EAF1FB !important;
        border: 1px solid rgba(148, 163, 184, 0.30) !important;
        border-radius: 14px !important;
        padding: 0.35rem !important;
    }

    [data-testid="stMain"] .stTabs [data-baseweb="tab"] {
        background: #FFFFFF !important;
        border: 1px solid rgba(148, 163, 184, 0.28) !important;
        border-radius: 10px !important;
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        font-weight: 850 !important;
        opacity: 1 !important;
    }

    [data-testid="stMain"] .stTabs [data-baseweb="tab"] *,
    [data-testid="stMain"] .stTabs [data-baseweb="tab"] p,
    [data-testid="stMain"] .stTabs [data-baseweb="tab"] span {
        color: inherit !important;
        -webkit-text-fill-color: inherit !important;
        font-weight: 850 !important;
        opacity: 1 !important;
    }

    [data-testid="stMain"] .stTabs [data-baseweb="tab"]:hover {
        background: #F8FBFF !important;
        border-color: rgba(37, 99, 235, 0.28) !important;
    }

    [data-testid="stMain"] .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, var(--accent-main), var(--accent-second)) !important;
        border-color: rgba(37, 99, 235, 0.50) !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        box-shadow: 0 8px 18px rgba(37, 99, 235, 0.22) !important;
    }

    [data-testid="stMain"] .stTabs [data-baseweb="tab"][aria-selected="true"] *,
    [data-testid="stMain"] .stTabs [data-baseweb="tab"][aria-selected="true"] p,
    [data-testid="stMain"] .stTabs [data-baseweb="tab"][aria-selected="true"] span {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    div[data-testid="stForm"] input,
    div[data-testid="stForm"] [data-baseweb="input"] input,
    div[data-testid="stForm"] [data-baseweb="base-input"] input,
    .login-card input,
    .login-card [data-baseweb="input"] input,
    .login-card [data-baseweb="base-input"] input {
        background: #FFFFFF !important;
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        caret-color: #0F172A !important;
        opacity: 1 !important;
    }

    div[data-testid="stForm"] input::placeholder,
    .login-card input::placeholder {
        color: #64748B !important;
        -webkit-text-fill-color: #64748B !important;
        opacity: 1 !important;
    }

    /* Contraste fuerte para el formulario de datos personales en la barra lateral */
    [data-testid="stSidebar"] div[data-testid="stExpander"] div[data-testid="stForm"],
    [data-testid="stSidebar"] div[data-testid="stExpander"] div[data-testid="stForm"] > div {
        background: #FFFFFF !important;
        border-color: rgba(148, 163, 184, 0.30) !important;
    }

    [data-testid="stSidebar"] div[data-testid="stExpander"] div[data-testid="stForm"] label,
    [data-testid="stSidebar"] div[data-testid="stExpander"] div[data-testid="stForm"] label *,
    [data-testid="stSidebar"] div[data-testid="stExpander"] div[data-testid="stForm"] [data-testid="stWidgetLabel"],
    [data-testid="stSidebar"] div[data-testid="stExpander"] div[data-testid="stForm"] [data-testid="stWidgetLabel"] *,
    [data-testid="stSidebar"] div[data-testid="stExpander"] div[data-testid="stForm"] p {
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        opacity: 1 !important;
        font-weight: 850 !important;
        text-shadow: none !important;
    }

    [data-testid="stSidebar"] div[data-testid="stExpander"] div[data-testid="stForm"] input,
    [data-testid="stSidebar"] div[data-testid="stExpander"] div[data-testid="stForm"] textarea,
    [data-testid="stSidebar"] div[data-testid="stExpander"] div[data-testid="stForm"] [data-baseweb="input"] input,
    [data-testid="stSidebar"] div[data-testid="stExpander"] div[data-testid="stForm"] [data-baseweb="base-input"] input {
        background: #FFFFFF !important;
        color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important;
        caret-color: #0F172A !important;
        border-color: #CBD5E1 !important;
        opacity: 1 !important;
        font-weight: 700 !important;
    }

    [data-testid="stSidebar"] div[data-testid="stExpander"] div[data-testid="stFormSubmitButton"] button,
    [data-testid="stSidebar"] div[data-testid="stExpander"] div[data-testid="stFormSubmitButton"] button[kind="secondary"] {
        background: linear-gradient(135deg, #8A1538 0%, #B91C1C 100%) !important;
        border: 1px solid rgba(138, 21, 56, 0.45) !important;
        border-radius: 14px !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        box-shadow: 0 10px 24px rgba(138, 21, 56, 0.28) !important;
        opacity: 1 !important;
    }

    [data-testid="stSidebar"] div[data-testid="stExpander"] div[data-testid="stFormSubmitButton"] button *,
    [data-testid="stSidebar"] div[data-testid="stExpander"] div[data-testid="stFormSubmitButton"] button p {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 950 !important;
        opacity: 1 !important;
    }

</style>
    """

    for key, value in theme.items():
        css = css.replace(f"__{key}__", value)

    return css
