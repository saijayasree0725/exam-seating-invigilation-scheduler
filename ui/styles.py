
"""Styling and theme configuration: Purple, Teal, Light Blue-Grey, and Warm Neutral."""

CUSTOM_CSS = """
<style>
:root {
    --primary-purple: #5B21B6;
    --accent-teal: #0D9488;
    --warm-bg: #FAF7F2;
    --text-primary: #111827;
}

/* Main application background */
.stApp,
[data-testid="stAppViewContainer"] {
    background-color: #FAF7F2 !important;
    color: #111827 !important;
    font-family: "Segoe UI", Arial, sans-serif;
}

/* Main page text */
[data-testid="stMain"],
[data-testid="stMain"] p,
[data-testid="stMain"] label,
[data-testid="stMain"] [data-testid="stWidgetLabel"] p,
[data-testid="stMain"] h1,
[data-testid="stMain"] h2,
[data-testid="stMain"] h3,
[data-testid="stMain"] h4 {
    color: #111827 !important;
}

/* Light blue-grey sidebar */
section[data-testid="stSidebar"] {
    background: #EAF2F8 !important;
    border-right: 1px solid #CBD5E1 !important;
}

section[data-testid="stSidebar"] > div {
    background: #EAF2F8 !important;
}

/* Sidebar text */
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] div[role="radiogroup"] *,
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] * {
    color: #172033 !important;
    opacity: 1 !important;
}

/* Navigation options */
section[data-testid="stSidebar"] div[role="radiogroup"] > label {
    background: #F8FAFC !important;
    border: 1px solid #D5E0EA !important;
    border-radius: 8px !important;
    padding: 7px 10px !important;
    margin-bottom: 4px !important;
}

section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
    background: #D7EAF7 !important;
    border-color: #0D9488 !important;
}

/* Selected navigation option */
section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
    background: #CFE8F5 !important;
    border: 1px solid #0D9488 !important;
}

/* Sidebar dataset information */
section[data-testid="stSidebar"] [data-testid="stMetric"],
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
    color: #172033;
}

/* Headings */
h1, h2, h3, h4 {
    color: #3B1B68;
    font-weight: 700;
}

/* Metric cards */
.metric-card {
    background: #FFFFFF;
    border: 1px solid #D9E2EC;
    border-radius: 12px;
    padding: 18px 20px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
    margin-bottom: 15px;
}

.metric-title {
    color: #475569 !important;
    font-size: 0.82rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 6px;
}

.metric-value {
    color: #5B21B6 !important;
    font-size: 1.85rem;
    font-weight: 800;
    line-height: 1.2;
}

.metric-sub {
    color: #0F766E !important;
    font-size: 0.8rem;
    margin-top: 4px;
    font-weight: 600;
}

/* Page header banners */
.page-header {
    background: linear-gradient(135deg, #5B21B6 0%, #0D9488 100%);
    border-radius: 12px;
    padding: 24px 28px;
    color: #FFFFFF !important;
    margin-bottom: 24px;
    box-shadow: 0 4px 12px rgba(91, 33, 182, 0.15);
}

.page-header h1,
.page-header p {
    color: #FFFFFF !important;
}

/* Conflict callout */
.conflict-box {
    background: #FFF1F2;
    border-left: 5px solid #E11D48;
    border-radius: 8px;
    padding: 16px 20px;
    margin: 14px 0;
    color: #881337 !important;
}

.conflict-box h4 {
    color: #9F1239 !important;
}

/* Success callout */
.success-box {
    background: #ECFDF5;
    border-left: 5px solid #059669;
    border-radius: 8px;
    padding: 16px 20px;
    margin: 14px 0;
    color: #065F46 !important;
}

.success-box h4 {
    color: #065F46 !important;
}

/* Interactive seating layout */
.seating-grid {
    display: inline-block;
    background: #FFFFFF;
    border: 2px solid #CBD5E1;
    border-radius: 10px;
    padding: 18px;
    margin: 10px 0;
}

.seat-pod {
    display: inline-block;
    box-sizing: border-box;
    width: 95px;
    height: 72px;
    margin: 4px;
    border-radius: 8px;
    padding: 6px 4px;
    text-align: center;
    vertical-align: top;
    font-size: 0.75rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

.seat-pod-occupied {
    background: #EDE9FE !important;
    border: 1px solid #A78BFA;
    color: #3B0764 !important;
}

.seat-pod-empty {
    background: #F1F5F9 !important;
    border: 1px dashed #94A3B8;
    color: #475569 !important;
}

.seat-code {
    font-weight: 700;
    font-size: 0.8rem;
}

.seat-student {
    font-size: 0.72rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.seat-tag {
    display: inline-block;
    padding: 1px 6px;
    border-radius: 4px;
    font-size: 0.65rem;
    font-weight: 600;
}

/* Subject badges */
.badge-cs {
    background: #EDE9FE;
    color: #5B21B6 !important;
    border: 1px solid #DDD6FE;
}

.badge-ec {
    background: #CCFBF1;
    color: #0F766E !important;
    border: 1px solid #99F6E4;
}

.badge-me {
    background: #FEF3C7;
    color: #92400E !important;
    border: 1px solid #FDE68A;
}

.badge-ma {
    background: #FCE7F3;
    color: #9D174D !important;
    border: 1px solid #FBCFE8;
}

/* Tables: clean borders and readable text */
[data-testid="stMain"] [data-testid="stTable"] {
    background-color: #FFFFFF !important;
    border: 1px solid #D9E2EC !important;
    border-radius: 8px !important;
}

[data-testid="stMain"] [data-testid="stDataFrame"] {
    border: 1px solid #D9E2EC !important;
    border-radius: 8px !important;
}

[data-testid="stMain"] [data-testid="stDataFrame"] *,
[data-testid="stMain"] [data-testid="stTable"] * {
    color: #111827 !important;
}

/* Regular buttons */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    border: 1px solid #CBD5E1 !important;
    color: #FFFFFF !important;
    background-color: #5B21B6 !important;
    transition: all 0.2s ease-in-out;
}

.stButton > button p,
.stButton > button span {
    color: #FFFFFF !important;
}

.stButton > button:hover {
    background-color: #0F766E !important;
    border-color: #0F766E !important;
    color: #FFFFFF !important;
}

/* Universal download-button styling */
[data-testid="stDownloadButton"] {
    width: 100% !important;
}

/* Target download buttons and their actual inner button */
[data-testid="stDownloadButton"] button,
[data-testid="stDownloadButton"] button[kind],
[data-testid="stDownloadButton"] button[kind="secondary"],
.stDownloadButton button {
    background: #7C3AED !important;
    background-color: #7C3AED !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    border: 1px solid #6D28D9 !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    min-height: 42px !important;
    padding: 8px 16px !important;
    opacity: 1 !important;
    filter: none !important;
    box-shadow: 0 2px 5px rgba(91, 33, 182, 0.15) !important;
}

/* Force white text and icons inside download buttons */
[data-testid="stDownloadButton"] button *,
.stDownloadButton button * {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    fill: #FFFFFF !important;
    stroke: #FFFFFF !important;
    opacity: 1 !important;
}

/* Hover effect for all download buttons */
[data-testid="stDownloadButton"] button:hover,
.stDownloadButton button:hover {
    background: #0F766E !important;
    background-color: #0F766E !important;
    border-color: #0F766E !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}

/* Disabled download buttons */
[data-testid="stDownloadButton"] button:disabled,
.stDownloadButton button:disabled {
    background: #64748B !important;
    background-color: #64748B !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    opacity: 0.8 !important;
}

/* Reset Demo Data button: white text */
section[data-testid="stSidebar"] .stButton button,
section[data-testid="stSidebar"] .stButton button p {
    color: #FFFFFF !important;
}

/* Print */
@media print {
    section[data-testid="stSidebar"],
    .stButton,
    .stDownloadButton,
    [data-testid="stDownloadButton"],
    header {
        display: none !important;
    }

    .print-only {
        display: block !important;
    }
}


/* FINAL OVERRIDE: readable download buttons across the application */
[data-testid="stMain"] [data-testid="stDownloadButton"] button,
[data-testid="stMain"] button[data-testid="stBaseButton-secondary"],
[data-testid="stMain"] button[data-testid="stBaseButton-primary"],
[data-testid="stMain"] .stDownloadButton button {
    background: #7C3AED !important;
    background-color: #7C3AED !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    border: 1px solid #6D28D9 !important;
    border-radius: 9px !important;
    font-size: 15px !important;
    font-weight: 700 !important;
    min-height: 44px !important;
    padding: 10px 16px !important;
    opacity: 1 !important;
    visibility: visible !important;
    box-shadow: 0 2px 6px rgba(91, 33, 182, 0.18) !important;
}

/* Force download labels and icons to remain visible */
[data-testid="stMain"] [data-testid="stDownloadButton"] button p,
[data-testid="stMain"] [data-testid="stDownloadButton"] button span,
[data-testid="stMain"] [data-testid="stDownloadButton"] button div,
[data-testid="stMain"] [data-testid="stDownloadButton"] button *,
[data-testid="stMain"] button[data-testid^="stBaseButton-"] p,
[data-testid="stMain"] button[data-testid^="stBaseButton-"] span {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    opacity: 1 !important;
    visibility: visible !important;
}

/* Professional teal hover effect */
[data-testid="stMain"] [data-testid="stDownloadButton"] button:hover,
[data-testid="stMain"] button[data-testid^="stBaseButton-"]:hover,
[data-testid="stMain"] .stDownloadButton button:hover {
    background: #0F766E !important;
    background-color: #0F766E !important;
    border-color: #0F766E !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}

/* Disabled state */
[data-testid="stMain"] [data-testid="stDownloadButton"] button:disabled {
    background: #64748B !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    opacity: 0.85 !important;
}


</style>
"""
