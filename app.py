
import streamlit as st
import pandas as pd
import numpy as np
import io
import math
import re
from io import BytesIO
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

st.set_page_config(page_title="Suburb Scorecards", layout="wide")

st.title("🏡 Suburb Scorecards — Upload Excel and Generate Client-Ready Cards")

with st.sidebar:
    st.header("1) Upload your Excel file")
    uploaded = st.file_uploader("Excel (.xlsx)", type=["xlsx"])
    show_heatmap = st.checkbox("Show heatmap for all suburbs (optional)", value=False)
    st.markdown("---")
    st.caption("Tip: Download PNGs or a combined PDF report for your client.")

@st.cache_data
def _read_excel(file):
    try:
        df = pd.read_excel(file, sheet_name=0, engine="openpyxl")
        return df
    except Exception as e:
        st.error(f"Failed to read Excel: {e}")
        return None

def _clean_header(name: str) -> str:
    # Normalize header names: lower, spaces, remove punctuation/newlines
    if name is None:
        return ""
    s = str(name).strip()
    s = s.replace("\\n", " ").replace("\n", " ")
    s = re.sub(r"\\s+", " ", s)
    s = s.lower()
    # remove extra spaces around punctuation
    s = re.sub(r"[^a-z0-9\\s()/%.-]+", "", s)
    s = re.sub(r"\\s+", " ", s).strip()
    return s

# Canonical columns we try to find (mapped to list of possible aliases after cleaning)
CANDIDATES = {
    "suburb": [
        "sa2", "suburb", "locality"
    ],
    "state": [
        "state"
    ],
    "property_type": [
        "property type", "type"
    ],
    "median_price": [
        "list price median now", "price median now", "median price now", "median price"
    ],
    "yield_score": [
        "yield score (sa2)", "yield score", "yield (score)"
    ],
    "buy_afford": [
        "buy affordability score (sa2)", "buy affordability", "buy affordability score"
    ],
    "rent_afford": [
        "rent affordability score (sa2)", "rent affordability", "rent affordability score"
    ],
    "rental_turnover": [
        "rental turnover score (sa2)", "rental turnover", "rental turnover score"
    ],
    "socio_econ": [
        "socio economics", "socioeconomic", "socio-economics"
    ],
    "investor_score": [
        "investor score (out of 100)", "investor score", "investor score out of 100"
    ],
}

def resolve_columns(df: pd.DataFrame):
    cleaned_map = {_clean_header(c): c for c in df.columns}
    resolved = {}
    for canon, options in CANDIDATES.items():
        found = None
        for opt in options:
            if opt in cleaned_map:
                found = cleaned_map[opt]
                break
        resolved[canon] = found
    return resolved

def friendly_money(x):
    try:
        if pd.isna(x):
            return "—"
        n = float(x)
        return f"${int(n):,}"
    except Exception:
        return "—"

def friendly_int(x):
    try:
        if pd.isna(x):
            return "—"
        return f"{int(round(float(x)))}"
    except Exception:
        return "—"

def safe_num(x, default=0):
    try:
        return float(x)
    except Exception:
        return default

def make_scorecard_figure(row, suburb_name="Suburb"):
    # Build a compact table-like image using matplotlib
    metrics = [
        ("Median Price (Now)", friendly_money(row["median_price"])),
        ("Yield Score", friendly_int(row["yield_score"])),
        ("Buy Affordability", friendly_int(row["buy_afford"])),
        ("Rent Affordability", friendly_int(row["rent_afford"])),
        ("Rental Turnover", friendly_int(row["rental_turnover"])),
        ("Socio-economics", friendly_int(row["socio_econ"])),
        ("Investor Score", friendly_int(row["investor_score"])),
    ]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.axis("off")
    table_data = [[m, v] for m, v in metrics]
    table = ax.table(cellText=table_data, colLabels=["Metric", suburb_name], cellLoc="center", loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.2, 1.2)
    plt.tight_layout()
    return fig

def make_radar_chart(row, suburb_name="Suburb"):
    # Radar of key scores (0-100 expected); use matplotlib only, no custom colors
    labels = [
        "Yield", "Buy Afford", "Rent Afford", "Turnover", "Socio Econ", "Investor"
    ]
    values = [
        safe_num(row["yield_score"]), safe_num(row["buy_afford"]), safe_num(row["rent_afford"]),
        safe_num(row["rental_turnover"]), safe_num(row["socio_econ"]), safe_num(row["investor_score"])
    ]
    # close the loop
    values += values[:1]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]
    fig = plt.figure(figsize=(5, 5))
    ax = plt.subplot(111, polar=True)
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    ax.set_rlabel_position(0)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(["20","40","60","80","100"])
    ax.set_ylim(0, 100)
    ax.plot(angles, values)
    ax.fill(angles, values, alpha=0.1)
    ax.set_title(f"{suburb_name} — Score Radar")
    fig.tight_layout()
    return fig

def make_explanation_page(suburb_name, row):
    # Create a text-only page using matplotlib with explanation of metrics
    fig, ax = plt.subplots(figsize=(8.27, 11.69))  # A4 portrait in inches
    ax.axis("off")
    lines = []
    lines.append(f"Suburb Scorecard & Radar — {suburb_name}")
    lines.append("")
    lines.append("What the Scorecard shows:")
    lines.append("• Median Price (Now): Current median listing price — a guide to entry budget.")
    lines.append("• Yield Score: Rental returns potential relative to price (0–100).")
    lines.append("• Buy Affordability: Ease of purchase for buyers (lower price-to-income, better finance access).")
    lines.append("• Rent Affordability: Tenant capacity to pay rent sustainably (lower rent-to-income).")
    lines.append("• Rental Turnover: Leasing fluidity — higher can mean faster letting, but shorter leases.")
    lines.append("• Socio-economics: Community stability & incomes; higher = lower mortgage stress risk.")
    lines.append("• Investor Score: Composite investment attractiveness from multiple indicators.")
    lines.append("")
    lines.append("How to read the Radar:")
    lines.append("• Each spoke is a 0–100 score. Larger filled area = stronger, more balanced metrics.")
    lines.append("• A suburb with high Yield and Affordability but low Socio-economics may favour cash flow, not stability.")
    lines.append("• A suburb with evenly high scores suggests balanced long-term investment potential.")
    lines.append("")
    lines.append("Notes:")
    lines.append("• Scores are comparative guides; validate with on-the-ground checks and rental appraisals.")
    lines.append("• For trust-held properties, confirm land tax implications and net yield after costs.")
    txt = "\\n".join(lines)
    ax.text(0.02, 0.98, txt, va="top", ha="left", wrap=True, fontsize=11)
    fig.tight_layout()
    return fig

def build_heatmap(dfv):
    hm_cols = ["yield_score", "buy_afford", "rent_afford", "rental_turnover", "socio_econ", "investor_score"]
    hm = dfv[["suburb"] + hm_cols].dropna(subset=["suburb"]).copy()
    hm.set_index("suburb", inplace=True)
    # ensure numeric
    for c in hm_cols:
        hm[c] = pd.to_numeric(hm[c], errors="coerce").fillna(0).round(0).astype(int)

    fig, ax = plt.subplots(figsize=(12, 0.35 * len(hm.index) + 2))
    im = ax.imshow(hm.values, aspect="auto")
    ax.set_yticks(range(len(hm.index)))
    ax.set_yticklabels(hm.index)
    ax.set_xticks(range(len(hm_cols)))
    ax.set_xticklabels(["Yield","Buy Afford","Rent Afford","Turnover","Socio Econ","Investor"], rotation=0)
    ax.set_title("Suburb Investment Score Heatmap")
    fig.colorbar(im, ax=ax, fraction=0.02, pad=0.02)
    fig.tight_layout()
    return fig

if uploaded is None:
    st.info("Upload your Excel file to begin. The app will auto-detect columns (even if your headers use new lines).")
    st.stop()

df_raw = _read_excel(uploaded)
if df_raw is None or df_raw.empty:
    st.error("No data found in the uploaded file.")
    st.stop()

# Normalize headers and resolve columns
df = df_raw.copy()
df.columns = [c.replace("\\n", " ").replace("\n", " ") for c in df.columns]
resolved = resolve_columns(df)

missing = [k for k,v in resolved.items() if v is None]
if missing:
    with st.expander("Missing required columns — click to see details"):
        st.write("I couldn't find these fields:", missing)
        st.write("Detected columns:", list(df.columns))
    st.warning("Some required columns were not found. The app may be limited until you upload a sheet with the expected fields.")
    
# Build a compact dataframe with only the resolved columns
def _col(df, key):
    colname = resolved.get(key)
    if colname is None:
        return pd.Series([None] * len(df))
    return df[colname]

dfv = pd.DataFrame({
    "suburb": _col(df, "suburb"),
    "state": _col(df, "state"),
    "property_type": _col(df, "property_type"),
    "median_price": _col(df, "median_price"),
    "yield_score": _col(df, "yield_score"),
    "buy_afford": _col(df, "buy_afford"),
    "rent_afford": _col(df, "rent_afford"),
    "rental_turnover": _col(df, "rental_turnover"),
    "socio_econ": _col(df, "socio_econ"),
    "investor_score": _col(df, "investor_score"),
}).copy()

# Drop rows with no suburb name
dfv = dfv[~dfv["suburb"].isna()].reset_index(drop=True)

left, right = st.columns([1, 2])
with left:
    st.subheader("2) Select filters")
    states = sorted([s for s in dfv["state"].dropna().unique().tolist() if str(s).strip() != ""])
    ptypes = sorted([s for s in dfv["property_type"].dropna().unique().tolist() if str(s).strip() != ""])
    sel_state = st.selectbox("State", options=["All"] + states, index=0)
    sel_ptype = st.selectbox("Property Type", options=["All"] + ptypes, index=0)
    df_filtered = dfv.copy()
    if sel_state != "All":
        df_filtered = df_filtered[df_filtered["state"] == sel_state]
    if sel_ptype != "All":
        df_filtered = df_filtered[df_filtered["property_type"] == sel_ptype]

    # Suburb selector
    suburbs = df_filtered["suburb"].dropna().astype(str).sort_values().unique().tolist()
    suburb = st.selectbox("Suburb", options=suburbs)

with right:
    st.subheader("3) Suburb Scorecard")
    row = df_filtered[df_filtered["suburb"].astype(str) == str(suburb)].head(1)
    if row.empty:
        st.warning("No data found for the selected suburb.")
        st.stop()
    r = row.iloc[0]

    # KPI row
    c1, c2, c3 = st.columns(3)
    c1.metric("Median Price (Now)", friendly_money(r["median_price"]))
    c2.metric("Investor Score", friendly_int(r["investor_score"]))
    c3.metric("Yield Score", friendly_int(r["yield_score"]))

    c4, c5, c6 = st.columns(3)
    c4.metric("Buy Affordability", friendly_int(r["buy_afford"]))
    c5.metric("Rent Affordability", friendly_int(r["rent_afford"]))
    c6.metric("Rental Turnover", friendly_int(r["rental_turnover"]))

    c7, = st.columns(1)
    c7.metric("Socio-economics", friendly_int(r["socio_econ"]))

    # Visuals
    sc_fig = make_scorecard_figure(r, suburb_name=str(r["suburb"]))
    st.pyplot(sc_fig, use_container_width=True)

    radar_fig = make_radar_chart(r, suburb_name=str(r["suburb"]))
    st.pyplot(radar_fig, use_container_width=True)

    # Explanations (client-ready text)
    with st.expander("What these visuals mean (client-ready explanation)"):
        st.markdown("""
**Scorecard (table):**  
- **Median Price (Now):** Current entry price guide for the suburb.  
- **Yield Score:** Rental return potential relative to price (higher = stronger cash flow).  
- **Buy Affordability:** How attainable the suburb is for buyers (price-to-income and finance readiness).  
- **Rent Affordability:** Tenants' ability to sustainably pay rent (lower rent-to-income).  
- **Rental Turnover:** Leasing fluidity; higher can mean quicker tenant replacement (but shorter leases).  
- **Socio-economics:** Community stability & relative incomes — a proxy for long-term resilience.  
- **Investor Score:** Composite attractiveness based on multiple indicators.

**Radar chart:**  
Each spoke is a score from 0–100. A larger, more balanced area indicates a suburb with strength across multiple dimensions (yield, affordability, stability). Use it to quickly compare overall balance vs. single-factor strength.
        """)

    # Downloads (PNGs)
    buf = BytesIO()
    sc_fig.savefig(buf, format="png", dpi=200, bbox_inches="tight")
    st.download_button("⬇️ Download Scorecard PNG", data=buf.getvalue(), file_name=f"{str(r['suburb']).replace(' ', '_')}_scorecard.png", mime="image/png")

    buf2 = BytesIO()
    radar_fig.savefig(buf2, format="png", dpi=200, bbox_inches="tight")
    st.download_button("⬇️ Download Radar PNG", data=buf2.getvalue(), file_name=f"{str(r['suburb']).replace(' ', '_')}_radar.png", mime="image/png")

    # Optional: Heatmap
    heatmap_fig = None
    if show_heatmap:
        st.markdown("---")
        st.subheader("Heatmap — Key Scores Across Suburbs")
        heatmap_fig = build_heatmap(dfv)
        st.pyplot(heatmap_fig, use_container_width=True)

    # PDF export (multi-page: explanation, scorecard, radar, optional heatmap)
    pdf_buf = BytesIO()
    with PdfPages(pdf_buf) as pdf:
        # Page 1: Explanation
        exp_fig = make_explanation_page(str(r["suburb"]), r)
        pdf.savefig(exp_fig, bbox_inches="tight")
        plt.close(exp_fig)
        # Page 2: Scorecard
        pdf.savefig(sc_fig, bbox_inches="tight")
        # Page 3: Radar
        pdf.savefig(radar_fig, bbox_inches="tight")
        # Page 4: Heatmap if produced
        if heatmap_fig is not None:
            pdf.savefig(heatmap_fig, bbox_inches="tight")

    st.download_button(
        "📄 Download Full PDF (Explanation + Scorecard + Radar)",
        data=pdf_buf.getvalue(),
        file_name=f"{str(r['suburb']).replace(' ', '_')}_scorecard_pack.pdf",
        mime="application/pdf"
    )

if show_heatmap:
    st.caption("Heatmap is also included as an extra page when exporting the PDF.")
