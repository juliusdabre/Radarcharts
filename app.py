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

    # Define the specific scores to include in the radar chart
    selected_scores = [
        "Yield score",
        "Buy affordability score",
        "Rent affordability score",
        "Socio economic score",
        "Investors score"
    ]

    suburb = st.selectbox("Select Suburb", df[suburb_col].unique())

    if suburb:
        row = df[df[suburb_col] == suburb].iloc[0]

        st.subheader(f"Scorecard for {suburb}")
        for score in selected_scores:
            if score in df.columns:
                st.write(f"{score}: {row[score]}")

        # Radar chart
        st.subheader("Radar Chart")

        # Filter out the selected scores
        categories = [score for score in selected_scores if score in df.columns]
        values = [row[c] for c in categories]
        values += values[:1]  # repeat the first value to close the radar chart

        N = len(categories)
        angles = [n / float(N) * 2 * pi for n in range(N)]
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
        ax.set_theta_offset(pi / 2)
        ax.set_theta_direction(-1)

        plt.xticks(angles[:-1], categories)

        ax.plot(angles, values, linewidth=2, linestyle='solid')
        ax.fill(angles, values, alpha=0.4)

        st.pyplot(fig)
