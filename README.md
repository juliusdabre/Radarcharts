# Suburb Scorecards (Streamlit) — with PDF Export

Upload an Excel sheet of suburb metrics and generate **client-ready scorecards + radar charts**, with a **multi-page PDF** export that includes a plain-English explanation of the visuals.

## Features
- Upload your Excel (.xlsx) file
- Auto-detects columns, even if headers contain new lines
- Filter by State and Property Type
- Select a suburb to generate:
  - KPI tiles (Median Price, Investor Score, etc.)
  - Scorecard image (downloadable PNG)
  - Radar chart (downloadable PNG)
- Optional: a heatmap of key scores across suburbs (matplotlib only)
- **Export a multi-page PDF** containing:
  1. Explanation page (what each metric means + how to read the radar)
  2. Scorecard
  3. Radar chart
  4. Heatmap (if enabled)

## Expected Columns
The app tries to resolve these fields (one or more synonyms acceptable):
- `SA2` (suburb name)
- `State`
- `Property Type`
- `List Price Median Now`
- `Yield Score (SA2)`
- `Buy Affordability Score (SA2)`
- `Rent Affordability Score (SA2)`
- `Rental Turnover Score (SA2)`
- `Socio economics`
- `Investor Score (Out Of 100)`

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Notes
- Charts use **matplotlib** only — no seaborn, single-plot per chart.
- If some columns aren't found, the app will still run but certain visuals may be limited.
