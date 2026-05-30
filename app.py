
"""Electricity Bill Analysis App"""

import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import requests

from anomaly_detection import load_bill_data, full_anomaly_analysis, classify_anomaly_cause
from dispute_letter import generate_dispute_letter
from tariff_data import compute_bescom_bill, BESCOM_TARIFF, HESCOM_TARIFF, TARIFF_HISTORY

# ─── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BillSense AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
:root {
  --bg:       #080B14;
  --surface:  #0F1221;
  --card:     #131729;
  --card2:    #181D32;
  --border:   rgba(255,255,255,0.07);
  --border2:  rgba(255,255,255,0.12);
  --text:     #E2E8F8;
  --muted:    #6B7594;
  --muted2:   #8B95BA;
  --red:      #F04545;
  --red2:     #C42020;
  --amber:    #F59E0B;
  --blue:     #3B82F6;
  --green:    #10B981;
  --cyan:     #06B6D4;
}

html, body, [class*="css"] {
  font-family: 'Inter', sans-serif !important;
  background: var(--bg) !important;
  color: var(--text) !important;
}
.stApp { background: var(--bg) !important; }
.main .block-container { padding-top: 1.5rem !important; max-width: 1400px !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
  background: var(--surface) !important;
  border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] > div { padding-top: 1rem; }
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] .stMarkdown { color: var(--text) !important; }

/* sidebar logo area */
.sb-logo { padding: 1rem 1rem 0.5rem; margin-bottom: 0.5rem; }
.sb-logo-title { font-size: 1.25rem; font-weight: 700; color: var(--text); letter-spacing: -0.02em; }
.sb-logo-sub   { font-size: 0.72rem; color: var(--muted); margin-top: 2px; }
.sb-divider    { height: 1px; background: var(--border); margin: 0.75rem 0; }
.sb-section    { font-size: 0.68rem; font-weight: 600; color: var(--muted);
                 letter-spacing: 0.08em; text-transform: uppercase; padding: 0 0 0.4rem; }

/* ── Buttons ── */
.stButton > button {
  background: var(--red) !important; color: #fff !important;
  border: none !important; border-radius: 8px !important;
  font-weight: 600 !important; font-size: 0.88rem !important;
  font-family: 'Inter', sans-serif !important;
  padding: 0.55rem 1.2rem !important;
  transition: all 0.15s ease !important;
  width: 100% !important;
}
.stButton > button:hover { background: var(--red2) !important; transform: translateY(-1px) !important; box-shadow: 0 4px 16px rgba(240,69,69,0.35) !important; }

.stDownloadButton > button {
  background: linear-gradient(135deg, #1A237E, #283593) !important;
  border: 1px solid rgba(59,130,246,0.3) !important;
  width: 100% !important;
}
.stDownloadButton > button:hover { box-shadow: 0 4px 16px rgba(59,130,246,0.25) !important; }

/* ── Inputs ── */
.stTextInput input, .stTextArea textarea, .stSelectbox > div > div {
  background: var(--card2) !important; border: 1px solid var(--border2) !important;
  color: var(--text) !important; border-radius: 8px !important;
}
.stSlider [data-baseweb="slider"] { padding: 0 !important; }
[data-testid="stFileUploaderDropzone"] {
  background: var(--card2) !important; border: 1.5px dashed var(--border2) !important;
  border-radius: 10px !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
  background: var(--card) !important; gap: 2px !important;
  border-radius: 10px !important; padding: 3px !important;
  border: 1px solid var(--border) !important;
}
.stTabs [data-baseweb="tab"] {
  color: var(--muted2) !important; font-weight: 500 !important;
  font-size: 0.85rem !important; border-radius: 7px !important;
  padding: 0.4rem 1rem !important;
}
.stTabs [aria-selected="true"] {
  background: var(--red) !important; color: #fff !important;
}
.stTabs [data-baseweb="tab-panel"] { padding-top: 1.5rem !important; }

/* ── Expander ── */
[data-testid="stExpander"] {
  background: var(--card) !important; border: 1px solid var(--border) !important;
  border-radius: 10px !important;
}
[data-testid="stExpander"] summary { color: var(--text) !important; }

/* ── Alerts ── */
[data-testid="stAlert"] { border-radius: 10px !important; }

/* ── Custom components ── */
.kpi-grid { display: grid; grid-template-columns: repeat(5,1fr); gap: 10px; margin-bottom: 1.5rem; }
.kpi { background: var(--card); border: 1px solid var(--border);
       border-radius: 12px; padding: 1rem 0.8rem; text-align: center;
       transition: border-color 0.2s; }
.kpi:hover { border-color: var(--border2); }
.kpi.alert { border-color: rgba(240,69,69,0.4); background: linear-gradient(135deg, rgba(240,69,69,0.08), var(--card)); }
.kpi-val  { font-size: 1.55rem; font-weight: 700; line-height: 1; color: var(--amber); font-family: 'JetBrains Mono', monospace; }
.kpi.alert .kpi-val { color: var(--red); }
.kpi-lbl  { font-size: 0.72rem; color: var(--muted); margin-top: 5px; font-weight: 500; letter-spacing: 0.02em; }
.kpi-sub  { font-size: 0.68rem; color: var(--muted); margin-top: 2px; opacity: 0.7; }

.status-bar {
  background: var(--card); border: 1px solid var(--border);
  border-radius: 10px; padding: 0.65rem 1.1rem;
  display: flex; align-items: center; gap: 1rem;
  margin-bottom: 1.2rem; font-size: 0.82rem;
}
.status-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--green); flex-shrink: 0; box-shadow: 0 0 8px rgba(16,185,129,0.6); }
.status-item { color: var(--muted2); }
.status-item strong { color: var(--text); }
.status-sep { color: var(--border2); }

.anomaly-card {
  background: linear-gradient(135deg, rgba(240,69,69,0.1) 0%, rgba(240,69,69,0.03) 100%);
  border: 1px solid rgba(240,69,69,0.35); border-left: 3px solid var(--red);
  border-radius: 12px; padding: 1.1rem 1.2rem; margin-bottom: 0.9rem;
}
.anomaly-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.6rem; }
.anomaly-month  { font-size: 1rem; font-weight: 700; color: var(--red); }
.anomaly-stats  { font-size: 0.78rem; color: var(--muted2); margin-top: 2px; font-family: 'JetBrains Mono', monospace; }
.anomaly-body   { font-size: 0.85rem; color: var(--text); line-height: 1.6; }
.anomaly-action { margin-top: 0.7rem; background: rgba(245,158,11,0.08); border: 1px solid rgba(245,158,11,0.2); border-radius: 8px; padding: 0.5rem 0.75rem; font-size: 0.8rem; color: var(--amber); }

.normal-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 8px; }
.normal-card { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 0.8rem; }
.normal-month { font-weight: 600; font-size: 0.88rem; color: var(--text); }
.normal-data  { font-size: 0.78rem; color: var(--muted2); margin-top: 3px; font-family: 'JetBrains Mono', monospace; }
.normal-ok    { font-size: 0.72rem; color: var(--green); margin-top: 4px; }

.tag { display: inline-block; border-radius: 5px; padding: 0.18rem 0.55rem;
       font-size: 0.72rem; font-weight: 600; margin-right: 4px; }
.tag-red    { background: rgba(240,69,69,0.12); border: 1px solid rgba(240,69,69,0.3); color: #F87171; }
.tag-amber  { background: rgba(245,158,11,0.12); border: 1px solid rgba(245,158,11,0.3); color: #FCD34D; }
.tag-blue   { background: rgba(59,130,246,0.12); border: 1px solid rgba(59,130,246,0.3); color: #93C5FD; }
.tag-green  { background: rgba(16,185,129,0.12); border: 1px solid rgba(16,185,129,0.3); color: #6EE7B7; }

.section-header { font-size: 0.95rem; font-weight: 700; color: var(--text); margin-bottom: 0.8rem; display: flex; align-items: center; gap: 0.5rem; }
.section-header::after { content: ''; flex: 1; height: 1px; background: var(--border); }

.tariff-slab-row { display: flex; justify-content: space-between; align-items: center;
                   padding: 0.55rem 0.8rem; border-radius: 7px; margin-bottom: 4px; }
.tariff-slab-row:nth-child(odd)  { background: var(--card2); }
.tariff-slab-row:nth-child(even) { background: rgba(255,255,255,0.02); }
.slab-label { font-size: 0.82rem; color: var(--muted2); }
.slab-rate  { font-family: 'JetBrains Mono', monospace; font-size: 0.88rem; font-weight: 600; color: var(--amber); }

.bill-breakdown { background: var(--card2); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }
.bill-row { display: flex; justify-content: space-between; padding: 0.6rem 1rem; border-bottom: 1px solid var(--border); }
.bill-row:last-child { border-bottom: none; }
.bill-row.total { background: rgba(245,158,11,0.08); border-top: 1px solid rgba(245,158,11,0.3); }
.bill-row-label { font-size: 0.85rem; color: var(--muted2); }
.bill-row-val   { font-family: 'JetBrains Mono', monospace; font-size: 0.88rem; color: var(--text); }
.bill-row.total .bill-row-label { color: var(--amber); font-weight: 700; font-size: 0.9rem; }
.bill-row.total .bill-row-val   { color: var(--amber); font-weight: 700; font-size: 1rem; }

.letter-preview { background: var(--card2); border: 1px solid var(--border);
                  border-radius: 12px; padding: 1.4rem; font-size: 0.84rem; line-height: 1.75; }
.letter-preview strong { color: var(--text); }
.letter-preview em { color: var(--muted2); font-style: italic; }

.ai-output { background: var(--card2); border: 1px solid rgba(59,130,246,0.25);
             border-left: 3px solid var(--blue); border-radius: 12px;
             padding: 1.4rem; font-size: 0.88rem; line-height: 1.75; color: var(--text); }

.revision-item { background: rgba(245,158,11,0.06); border: 1px solid rgba(245,158,11,0.15);
                 border-left: 3px solid var(--amber); border-radius: 8px;
                 padding: 0.6rem 1rem; margin-bottom: 6px; }
.revision-date  { font-size: 0.8rem; font-weight: 600; color: var(--amber); }
.revision-detail{ font-size: 0.82rem; color: var(--muted2); margin-top: 2px; }

h1,h2,h3,h4 { color: var(--text) !important; }
.stMarkdown p { color: var(--text) !important; }
.stDataFrame  { font-family: 'JetBrains Mono', monospace !important; }
</style>
""", unsafe_allow_html=True)


# ─── Fallback functions ───────────────────────────────────────────────────────
def _fallback_explanation(anomaly_summary: list, stats: dict, discom: str) -> str:
    lines = [
        "**Root Cause Analysis — Billing Anomaly Report**\n",
        f"Based on your 12-month billing history with {discom} (Karnataka), our analysis identified "
        f"{len(anomaly_summary)} anomalous billing period(s).\n",
    ]
    for a in anomaly_summary:
        lines.append(
            f"**{a['month']}** ({a['units']:.0f} units, ₹{a['amount']:,.0f}) — "
            f"Z-Score: {a['zscore']:.2f}. Likely cause: {a['cause']}. {a['cause_explanation']}\n"
        )
    lines.append(
        f"\nYour 12-month average is {stats['mean_units']:.0f} units. "
        "Any month exceeding this by more than 2 standard deviations warrants investigation. "
        "You have grounds to file a formal dispute under Section 26 of the Electricity Act 2003."
    )
    return "\n".join(lines)


def _fallback_explanation_short(anomaly_df, stats: dict, discom: str) -> str:
    months = ", ".join(anomaly_df["month"].tolist())
    return (
        f"Statistical analysis of your 12-month {discom} billing history identified anomalous "
        f"consumption in {months}. Average monthly consumption is {stats['mean_units']:.0f} units "
        f"(σ = {stats['std_units']:.0f}). The disputed month(s) exceed the IQR upper bound of "
        f"{stats['iqr_upper']:.0f} units and/or the ±2.0σ Z-score threshold, indicating a "
        "statistically significant billing irregularity. Possible causes include meter fault, "
        "estimated reading accumulation, tariff revision, or billing system error."
    )


# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sb-logo">
      <div class="sb-logo-title">⚡ BillSense AI</div>
      <div class="sb-logo-sub">Electricity Anomaly Detector · PS-SC7</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-section">DISCOM</div>', unsafe_allow_html=True)
    discom = st.selectbox("", ["BESCOM", "HESCOM"], label_visibility="collapsed",
                          help="Bangalore or Hubli Electricity Supply Company")

    st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-section">Consumer Details</div>', unsafe_allow_html=True)
    consumer_name    = st.text_input("Full Name",       value="Ramesh Kumar")
    consumer_number  = st.text_input("Consumer No.",    value="BLR-NE-104823")
    consumer_address = st.text_area("Service Address",
                                    value="42, 3rd Cross, Indiranagar\nBangalore – 560 038\nKarnataka",
                                    height=75)

    st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-section">Detection Sensitivity</div>', unsafe_allow_html=True)
    zscore_threshold = st.slider("Z-Score threshold", 1.5, 3.5, 2.0, 0.1,
                                 help="Lower = more sensitive")
    iqr_multiplier   = st.slider("IQR multiplier",   1.0, 3.0, 1.5, 0.25,
                                 help="Lower = more sensitive")

    st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-section">Bill History CSV</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("", type=["csv"], label_visibility="collapsed",
                                     help="Upload your 12-month bill CSV")

    st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)
    st.caption("Karnataka Hackathon 2026 · BESCOM/HESCOM tariff data")


# ─── Paths & Data Load ───────────────────────────────────────────────────────
_HERE       = os.path.dirname(os.path.abspath(__file__))
_SAMPLE_CSV = os.path.join(_HERE, "sample_bills.csv")

with open(_SAMPLE_CSV, "rb") as f:
    sample_csv_bytes = f.read()

data_source = uploaded_file if uploaded_file else _SAMPLE_CSV
data_label  = f"📂 {uploaded_file.name}" if uploaded_file else "📊 Sample data (BESCOM · March 2025 spike)"

try:
    df_raw = load_bill_data(data_source)
    df, stats = full_anomaly_analysis(df_raw, zscore_threshold, iqr_multiplier)
    data_loaded = True
except Exception as e:
    st.error(f"❌ Could not load CSV: {e}")
    data_loaded = False


# ─── Main content ─────────────────────────────────────────────────────────────
if data_loaded:

    # ── Page title ────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="margin-bottom:1.4rem;">
      <div style="font-size:1.6rem;font-weight:700;color:#E2E8F8;letter-spacing:-0.03em;line-height:1.1;">
        Electricity Bill Anomaly Detector
      </div>
      <div style="font-size:0.85rem;color:#6B7594;margin-top:4px;">
        Powered by Z-Score · IQR · Claude AI &nbsp;·&nbsp; BESCOM / HESCOM Karnataka
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Status bar ────────────────────────────────────────────────────────────
    anomaly_count = stats["anomaly_count"]
    alert_color   = "#F04545" if anomaly_count > 0 else "#10B981"
    alert_dot_css = f"background:{alert_color};box-shadow:0 0 8px {alert_color}66;"
    st.markdown(f"""
    <div class="status-bar">
      <div class="status-dot" style="{alert_dot_css}"></div>
      <span class="status-item"><strong>{data_label}</strong></span>
      <span class="status-sep">|</span>
      <span class="status-item"><strong>{len(df)}</strong> months loaded</span>
      <span class="status-sep">|</span>
      <span class="status-item">DISCOM: <strong>{discom}</strong></span>
      <span class="status-sep">|</span>
      <span class="status-item" style="color:{'#F04545' if anomaly_count>0 else '#10B981'}">
        <strong>{anomaly_count} anomal{'y' if anomaly_count==1 else 'ies'} detected</strong>
      </span>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI cards ─────────────────────────────────────────────────────────────
    kpis = [
        ("Avg Consumption",  f"{stats['mean_units']:.0f}",   "units / month",  False),
        ("Std Deviation",    f"±{stats['std_units']:.0f}",   "units",          False),
        ("Normal IQR Range", f"{stats['iqr_lower']}–{stats['iqr_upper']}", "units", False),
        ("Anomalies Found",  str(stats['anomaly_count']),    "month(s) flagged", stats['anomaly_count'] > 0),
        ("Avg Monthly Bill", f"₹{stats['mean_amount']:.0f}", "per month",      False),
    ]
    kpi_html = '<div class="kpi-grid">'
    for lbl, val, sub, is_alert in kpis:
        cls = "kpi alert" if is_alert else "kpi"
        kpi_html += f'<div class="{cls}"><div class="kpi-val">{val}</div><div class="kpi-lbl">{lbl}</div><div class="kpi-sub">{sub}</div></div>'
    kpi_html += '</div>'
    st.markdown(kpi_html, unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈  Charts",
        "🚨  Anomalies",
        "🤖  AI Explanation",
        "📊  Tariff Calculator",
        "📄  Dispute Letter",
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — CHARTS
    # ══════════════════════════════════════════════════════════════════════════
    with tab1:
        anomaly_df = df[df["anomaly"]]

        # ── Main consumption chart ────────────────────────────────────────────
        fig = make_subplots(
            rows=2, cols=1,
            row_heights=[0.62, 0.38],
            vertical_spacing=0.1,
            subplot_titles=["Units consumed — with anomaly detection bands", "Monthly bill amount (₹)"],
        )

        # IQR shaded band
        fig.add_trace(go.Scatter(
            x=list(df["month"]) + list(df["month"])[::-1],
            y=list(df["iqr_upper"]) + list(df["iqr_lower"])[::-1],
            fill="toself", fillcolor="rgba(16,185,129,0.07)",
            line=dict(color="rgba(16,185,129,0.15)", width=1),
            name="IQR normal band", hoverinfo="skip",
        ), row=1, col=1)

        # Consumption line
        fig.add_trace(go.Scatter(
            x=df["month"], y=df["units"],
            mode="lines+markers",
            line=dict(color="#3B82F6", width=2.5, shape="spline"),
            marker=dict(
                size=[12 if a else 7 for a in df["anomaly"]],
                color=["#F04545" if a else "#3B82F6" for a in df["anomaly"]],
                line=dict(width=2, color=["#FF0000" if a else "#1D4ED8" for a in df["anomaly"]]),
            ),
            name="Units consumed",
            hovertemplate="<b>%{x}</b><br>%{y} units<extra></extra>",
        ), row=1, col=1)

        # Z-score threshold lines
        mean_u, std_u = stats["mean_units"], stats["std_units"]
        for sign, lbl in [(1, f"+{zscore_threshold}σ"), (-1, f"−{zscore_threshold}σ")]:
            fig.add_hline(
                y=mean_u + sign * zscore_threshold * std_u,
                line_dash="dot", line_color="rgba(245,158,11,0.5)",
                annotation_text=lbl, annotation_font_size=11,
                annotation_font_color="rgba(245,158,11,0.8)",
                row=1, col=1,
            )
        fig.add_hline(y=mean_u, line_dash="dash", line_color="rgba(255,255,255,0.2)",
                      annotation_text="mean", annotation_font_size=11,
                      annotation_font_color="rgba(255,255,255,0.4)", row=1, col=1)

        # Anomaly markers
        if not anomaly_df.empty:
            fig.add_trace(go.Scatter(
                x=anomaly_df["month"], y=anomaly_df["units"],
                mode="markers+text",
                marker=dict(size=18, color="rgba(240,69,69,0)", symbol="circle-open",
                            line=dict(width=2.5, color="#F04545")),
                text=["⚠️"] * len(anomaly_df),
                textposition="top center", textfont=dict(size=14),
                name="Anomaly", showlegend=True,
                hovertemplate="<b>⚠️ ANOMALY: %{x}</b><br>%{y} units<extra></extra>",
            ), row=1, col=1)

        # Amount bars
        fig.add_trace(go.Bar(
            x=df["month"], y=df["amount"],
            marker=dict(
                color=["rgba(240,69,69,0.75)" if a else "rgba(59,130,246,0.5)" for a in df["anomaly"]],
                line=dict(color=["#F04545" if a else "#3B82F6" for a in df["anomaly"]], width=1),
            ),
            name="Amount (₹)",
            hovertemplate="<b>%{x}</b><br>₹%{y:,.0f}<extra></extra>",
        ), row=2, col=1)

        fig.update_layout(
            height=540, margin=dict(l=0, r=0, t=40, b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", size=12, color="#8B95BA"),
            legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="rgba(255,255,255,0.08)",
                        borderwidth=1, font=dict(size=11)),
            hoverlabel=dict(bgcolor="#131729", bordercolor="#3B82F6",
                            font=dict(family="Inter", size=12, color="#E2E8F8")),
        )
        fig.update_xaxes(tickangle=-30, gridcolor="rgba(255,255,255,0.04)",
                         tickfont=dict(size=11), linecolor="rgba(255,255,255,0.08)")
        fig.update_yaxes(gridcolor="rgba(255,255,255,0.04)", linecolor="rgba(255,255,255,0.08)")
        st.plotly_chart(fig, use_container_width=True)

        # ── Z-Score + Box plot row ────────────────────────────────────────────
        col_a, col_b = st.columns(2)
        with col_a:
            fig_z = go.Figure()
            fig_z.add_trace(go.Bar(
                x=df["month"], y=df["zscore_units"],
                marker_color=["#F04545" if abs(z) > zscore_threshold else "#3B82F6"
                              for z in df["zscore_units"]],
                hovertemplate="<b>%{x}</b><br>Z-Score: %{y:.2f}<extra></extra>",
            ))
            for sign, lbl in [(1, f"+{zscore_threshold}σ"), (-1, f"−{zscore_threshold}σ")]:
                fig_z.add_hline(y=sign * zscore_threshold, line_dash="dash",
                                line_color="rgba(245,158,11,0.6)",
                                annotation_text=lbl, annotation_font_size=10,
                                annotation_font_color="rgba(245,158,11,0.8)")
            fig_z.update_layout(
                title=dict(text="Z-Score by month", font=dict(size=13, color="#8B95BA")),
                height=260, margin=dict(l=0, r=0, t=40, b=0),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", size=11, color="#8B95BA"),
                showlegend=False,
            )
            fig_z.update_xaxes(tickangle=-30, gridcolor="rgba(255,255,255,0.04)", tickfont=dict(size=10))
            fig_z.update_yaxes(gridcolor="rgba(255,255,255,0.04)")
            st.plotly_chart(fig_z, use_container_width=True)

        with col_b:
            fig_box = go.Figure()
            fig_box.add_trace(go.Box(
                y=df["units"], name="Distribution",
                marker_color="#3B82F6", line_color="#3B82F6",
                fillcolor="rgba(59,130,246,0.12)", boxmean="sd",
                hovertemplate="<b>%{y} units</b><extra></extra>",
            ))
            if not anomaly_df.empty:
                fig_box.add_trace(go.Scatter(
                    x=["Distribution"] * len(anomaly_df), y=anomaly_df["units"],
                    mode="markers",
                    marker=dict(size=11, color="#F04545", symbol="x-thin",
                                line=dict(width=2.5, color="#F04545")),
                    name="Anomaly",
                ))
            fig_box.update_layout(
                title=dict(text="IQR distribution", font=dict(size=13, color="#8B95BA")),
                height=260, margin=dict(l=0, r=0, t=40, b=0),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", size=11, color="#8B95BA"),
                showlegend=True,
                legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
            )
            fig_box.update_yaxes(gridcolor="rgba(255,255,255,0.04)")
            st.plotly_chart(fig_box, use_container_width=True)

        # Raw table
        with st.expander("📋 Raw data table"):
            disp = df[["month","units","amount","zscore_units","anomaly_zscore","anomaly_iqr","anomaly"]].copy()
            disp.columns = ["Month","Units","Amount (₹)","Z-Score","Anomaly (Z)","Anomaly (IQR)","Flagged"]
            disp["Z-Score"] = disp["Z-Score"].round(2)
            st.dataframe(disp, use_container_width=True, hide_index=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 — ANOMALIES
    # ══════════════════════════════════════════════════════════════════════════
    with tab2:
        anomaly_rows = df[df["anomaly"]].copy()
        normal_rows  = df[~df["anomaly"]].copy()

        if anomaly_rows.empty:
            st.success("✅ No anomalies detected with current sensitivity settings.")
        else:
            st.markdown(f"""
            <div style="background:rgba(240,69,69,0.08);border:1px solid rgba(240,69,69,0.25);
                        border-radius:10px;padding:0.75rem 1rem;margin-bottom:1.2rem;font-size:0.85rem;">
              ⚠️ &nbsp;<strong style="color:#F87171">{len(anomaly_rows)} anomalous month(s)</strong>
              <span style="color:#8B95BA"> detected — Z-Score &gt; {zscore_threshold}σ and/or outside IQR ×{iqr_multiplier}</span>
            </div>
            """, unsafe_allow_html=True)

            for _, row in anomaly_rows.iterrows():
                cause = classify_anomaly_cause(row, df)
                conf_tag = "tag-red" if cause["confidence"] == "High" else "tag-amber"
                pct_above = ((row["units"] - stats["mean_units"]) / stats["mean_units"] * 100)

                st.markdown(f"""
                <div class="anomaly-card">
                  <div class="anomaly-header">
                    <div>
                      <div class="anomaly-month">⚠️ &nbsp;{row['month']}</div>
                      <div class="anomaly-stats">
                        {row['units']:.0f} units &nbsp;·&nbsp; ₹{row['amount']:,.2f}
                        &nbsp;·&nbsp; Z = {row['zscore_units']:.2f}
                        &nbsp;·&nbsp; +{pct_above:.0f}% above avg
                      </div>
                    </div>
                    <div style="text-align:right;flex-shrink:0;margin-left:1rem;">
                      <span class="tag tag-amber">{cause['cause']}</span><br>
                      <span class="tag {conf_tag}" style="margin-top:4px;display:inline-block;">
                        {cause['confidence']} confidence
                      </span>
                    </div>
                  </div>
                  <div class="anomaly-body">{cause['explanation']}</div>
                  <div class="anomaly-action">💡 <strong>Recommended action:</strong> {cause['action']}</div>
                </div>
                """, unsafe_allow_html=True)

        # Normal months grid
        st.markdown('<div class="section-header">✅ Normal months</div>', unsafe_allow_html=True)
        html_grid = '<div class="normal-grid">'
        for _, row in normal_rows.iterrows():
            html_grid += f"""
            <div class="normal-card">
              <div class="normal-month">{row['month']}</div>
              <div class="normal-data">{row['units']:.0f} u &nbsp;·&nbsp; ₹{row['amount']:,.0f}</div>
              <div class="normal-ok">✓ Normal &nbsp; Z={row['zscore_units']:.2f}</div>
            </div>"""
        html_grid += '</div>'
        st.markdown(html_grid, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3 — AI EXPLANATION
    # ══════════════════════════════════════════════════════════════════════════
    with tab3:
        anomaly_rows_ai = df[df["anomaly"]]

        if anomaly_rows_ai.empty:
            st.info("No anomalies detected. Upload data with billing spikes to see AI explanation.")
        else:
            col_l, col_r = st.columns([3, 1])
            with col_r:
                st.markdown(f"""
                <div style="background:var(--card);border:1px solid var(--border);border-radius:10px;
                            padding:1rem;font-size:0.82rem;color:var(--muted2);line-height:1.7;">
                  <div style="color:var(--text);font-weight:600;margin-bottom:0.5rem;">Analysis scope</div>
                  <div>DISCOM: <strong style="color:var(--text)">{discom}</strong></div>
                  <div>Anomalies: <strong style="color:#F04545">{len(anomaly_rows_ai)} month(s)</strong></div>
                  <div>Avg: <strong style="color:var(--text)">{stats['mean_units']:.0f} units</strong></div>
                  <div>σ: <strong style="color:var(--text)">{stats['std_units']:.0f} units</strong></div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🤖 Generate explanation"):
                    anomaly_summary = []
                    for _, r in anomaly_rows_ai.iterrows():
                        cause = classify_anomaly_cause(r, df)
                        anomaly_summary.append({
                            "month": r["month"], "units": r["units"],
                            "amount": r["amount"], "zscore": round(r["zscore_units"], 2),
                            "cause": cause["cause"], "cause_explanation": cause["explanation"],
                        })
                    prompt = f"""You are an expert electricity billing analyst for Karnataka, India.

Consumer's 12-month bill data shows anomalies:
{json.dumps(anomaly_summary, indent=2)}

Statistical context:
- 12-month average: {stats['mean_units']} units/month
- Standard deviation: {stats['std_units']} units  
- Normal IQR range: {stats['iqr_lower']} – {stats['iqr_upper']} units
- DISCOM: {discom} (Karnataka)

Provide:
1. Plain-language explanation (2–3 paragraphs) a household consumer can understand — why the bill spiked.
2. Possible causes in order of likelihood (tariff revision, estimated reading, meter fault, seasonal, billing error).
3. What the consumer should specifically ask the DISCOM.
4. Whether they have grounds for a formal dispute under Electricity Act 2003.

Use simple language, refer to BESCOM/HESCOM and Karnataka context specifically. Be empathetic but factual. Use clear headings."""

                    with st.spinner("Analysing with Claude AI..."):
                        try:
                            resp = requests.post(
                                "https://api.anthropic.com/v1/messages",
                                headers={"Content-Type": "application/json"},
                                json={"model": "claude-sonnet-4-20250514", "max_tokens": 1000,
                                      "messages": [{"role": "user", "content": prompt}]},
                                timeout=30
                            )
                            ai_text = "".join(
                                b.get("text", "") for b in resp.json().get("content", [])
                                if b.get("type") == "text"
                            )
                            st.session_state.ai_explanation = ai_text or _fallback_explanation(anomaly_summary, stats, discom)
                        except Exception:
                            st.session_state.ai_explanation = _fallback_explanation(anomaly_summary, stats, discom)

            with col_l:
                if st.session_state.get("ai_explanation"):
                    st.markdown(f"""
                    <div class="ai-output">
                    {st.session_state.ai_explanation.replace(chr(10), '<br>')}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="background:var(--card);border:1px dashed var(--border2);border-radius:12px;
                                padding:2.5rem;text-align:center;color:var(--muted);">
                      <div style="font-size:2rem;margin-bottom:0.5rem;">🤖</div>
                      <div style="font-size:0.9rem;">Click <strong style="color:var(--text)">Generate explanation</strong> to get a plain-language<br>root cause analysis powered by Claude AI.</div>
                    </div>
                    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 4 — TARIFF CALCULATOR
    # ══════════════════════════════════════════════════════════════════════════
    with tab4:
        tariff = BESCOM_TARIFF if discom == "BESCOM" else HESCOM_TARIFF

        col_l, col_r = st.columns([1, 1], gap="large")

        with col_l:
            st.markdown(f'<div class="section-header">{discom} Tariff Slabs — LT-2A Domestic</div>', unsafe_allow_html=True)
            for slab in tariff["slabs"]:
                st.markdown(f"""
                <div class="tariff-slab-row">
                  <span class="slab-label">{slab['label']}</span>
                  <span class="slab-rate">₹ {slab['rate']}/unit</span>
                </div>
                """, unsafe_allow_html=True)
            st.markdown(f"""
            <div style="font-size:0.78rem;color:var(--muted);margin-top:0.8rem;line-height:1.7;">
              Fixed charge: ₹{tariff['fixed_charge_per_month']}/month &nbsp;·&nbsp;
              Fuel surcharge: {tariff['fuel_surcharge_pct']*100:.0f}% &nbsp;·&nbsp;
              Electricity duty: {tariff['electricity_duty_pct']*100:.0f}%
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="section-header">Recent Tariff Revisions</div>', unsafe_allow_html=True)
            for _, info in TARIFF_HISTORY.items():
                st.markdown(f"""
                <div class="revision-item">
                  <div class="revision-date">{info['effective']}</div>
                  <div class="revision-detail">{info['revision']}</div>
                </div>
                """, unsafe_allow_html=True)

        with col_r:
            st.markdown('<div class="section-header">Bill Calculator</div>', unsafe_allow_html=True)
            calc_units = st.number_input("Units consumed", min_value=0, max_value=2000,
                                         value=300, step=10, label_visibility="visible")
            if st.button("Calculate expected bill"):
                st.session_state.tariff_result = compute_bescom_bill(calc_units, discom)

            if st.session_state.get("tariff_result"):
                r = st.session_state.tariff_result
                html = '<div class="bill-breakdown">'
                for slab in r["slab_breakdown"]:
                    html += f"""
                    <div class="bill-row">
                      <span class="bill-row-label">{slab['label']} — {slab['units']:.0f} u × ₹{slab['rate']}</span>
                      <span class="bill-row-val">₹ {slab['charge']:.2f}</span>
                    </div>"""
                for lbl, val in [("Energy charges", r["energy_charge"]),
                                  ("Fuel surcharge", r["fuel_surcharge"]),
                                  ("Electricity duty", r["electricity_duty"]),
                                  ("Fixed charge", r["fixed_charge"])]:
                    html += f"""
                    <div class="bill-row">
                      <span class="bill-row-label">{lbl}</span>
                      <span class="bill-row-val">₹ {val:.2f}</span>
                    </div>"""
                html += f"""
                    <div class="bill-row total">
                      <span class="bill-row-label">Total expected bill</span>
                      <span class="bill-row-val">₹ {r['total_expected']:.2f}</span>
                    </div>
                </div>"""
                st.markdown(html, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 5 — DISPUTE LETTER
    # ══════════════════════════════════════════════════════════════════════════
    with tab5:
        anomaly_rows_letter = df[df["anomaly"]].copy()

        if anomaly_rows_letter.empty:
            st.info("No anomalies detected. Dispute letter activates when anomalies are found.")
        else:
            ai_expl = st.session_state.get("ai_explanation") or \
                      _fallback_explanation_short(anomaly_rows_letter, stats, discom)

            anomaly_list = []
            for _, row in anomaly_rows_letter.iterrows():
                cause = classify_anomaly_cause(row, df)
                anomaly_list.append({"month": row["month"], "units": row["units"],
                                     "amount": row["amount"], "cause": cause["cause"]})
            months_str = ", ".join(a["month"] for a in anomaly_list)

            col_l, col_r = st.columns([3, 2], gap="large")

            with col_l:
                st.markdown('<div class="section-header">Letter preview</div>', unsafe_allow_html=True)
                st.markdown(f"""
                <div class="letter-preview">
                  <div style="font-size:0.72rem;color:var(--muted);letter-spacing:0.05em;text-transform:uppercase;margin-bottom:0.8rem;">
                    FORMAL DISPUTE / COMPLAINT LETTER
                  </div>
                  <strong>To:</strong> Executive Engineer / Consumer Grievance Cell, {discom}<br><br>
                  <strong>Subject:</strong> Complaint Against Inflated Electricity Bill — {months_str}<br>
                  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Consumer No. {consumer_number}<br><br>
                  <strong>Consumer:</strong> {consumer_name}<br>
                  <strong>Address:</strong> {consumer_address.replace(chr(10), ', ')}<br><br>
                  <em>Letter contains: Consumer details · Statistical evidence (Z-score & IQR) · 
                  Disputed bill table · AI root-cause analysis · 6 specific relief requests · 
                  Legal provisions (Electricity Act 2003, KERC) · Enclosures list</em>
                </div>
                """, unsafe_allow_html=True)

            with col_r:
                st.markdown('<div class="section-header">Anomalies cited</div>', unsafe_allow_html=True)
                for a in anomaly_list:
                    st.markdown(f"""
                    <div style="background:rgba(240,69,69,0.07);border:1px solid rgba(240,69,69,0.2);
                                border-radius:8px;padding:0.6rem 0.9rem;margin-bottom:6px;">
                      <div style="font-weight:600;font-size:0.85rem;color:#F87171;">{a['month']}</div>
                      <div style="font-size:0.78rem;color:var(--muted2);font-family:'JetBrains Mono',monospace;">
                        {a['units']:.0f} units &nbsp;·&nbsp; ₹{a['amount']:,.0f}
                      </div>
                      <div style="font-size:0.72rem;color:var(--muted);margin-top:2px;">{a['cause']}</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("📄 Generate DOCX letter"):
                    with st.spinner("Drafting letter..."):
                        try:
                            docx_bytes = generate_dispute_letter(
                                consumer_name=consumer_name,
                                consumer_number=consumer_number,
                                consumer_address=consumer_address,
                                discom=discom,
                                anomalous_months=anomaly_list,
                                stats=stats,
                                ai_explanation=ai_expl,
                            )
                            st.session_state.docx_bytes = docx_bytes
                            st.success("✅ Ready to download!")
                        except Exception as e:
                            st.error(f"Error: {e}")

                if st.session_state.get("docx_bytes"):
                    st.download_button(
                        label="⬇️ Download dispute letter (.docx)",
                        data=st.session_state.docx_bytes,
                        file_name=f"Dispute_Letter_{consumer_number}_{discom}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )

    # ── Sample CSV ────────────────────────────────────────────────────────────
    with st.expander("📥 Download sample CSV template"):
        st.download_button("⬇️ sample_bills.csv", sample_csv_bytes,
                           file_name="sample_bills.csv", mime="text/csv")
        st.code("Month,Units_Consumed,Amount_Billed,Reading_Type,Meter_Reading,Previous_Reading\nApril 2024,210,1450.50,Actual,12350,12140\n...\nMarch 2025,678,5820.00,Actual,15455,14777", language="csv")