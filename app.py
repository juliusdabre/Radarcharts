
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from math import pi

st.set_page_config(page_title="Suburb Scorecard & Radar", layout="wide")

st.title("Suburb Scorecard & Radar Charts")

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Clean headers
    df.columns = df.columns.astype(str).str.strip().str.replace("\n", " ", regex=True)

    suburb_col = df.columns[0]  # assume first col is suburb
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    suburb = st.selectbox("Select Suburb", df[suburb_col].unique())

    if suburb:
        row = df[df[suburb_col] == suburb].iloc[0]

        st.subheader(f"Scorecard for {suburb}")
        for col in numeric_cols:
            st.write(f"{col}: {row[col]}")

        # Radar chart
        st.subheader("Radar Chart")
        categories = numeric_cols
        values = [row[c] for c in categories]
        values += values[:1]
        N = len(categories)

        angles = [n / float(N) * 2 * pi for n in range(N)]
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=(6,6), subplot_kw=dict(polar=True))
        ax.set_theta_offset(pi / 2)
        ax.set_theta_direction(-1)

        plt.xticks(angles[:-1], categories)

        ax.plot(angles, values, linewidth=2, linestyle='solid')
        ax.fill(angles, values, alpha=0.4)
        st.pyplot(fig)
