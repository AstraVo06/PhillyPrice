# PhillyPrice: Philadelphia home price estimator

A Streamlit website where a real estate agent or home buyer searches any Philadelphia single-family address.
The site fills in the home's details from the city's property records (or the visitor enters them), and shows:

- a suggested list price from a tuned Random Forest model
- a likely price range
- how each feature moved the estimate up or down
- live what-if sliders that re-price the home instantly and show where it ranks in its ZIP code
- recent similar sales nearby, and neighborhood facts
- a Find homes page to filter recent sales by ZIP, price, bedrooms, bathrooms, size, and condition
- a market map of prices, incomes, and rents by neighborhood, with a 3D city view
- price trends since 2019 by ZIP code, and mortgage rates

**Live website:** _add the Streamlit Community Cloud link here_

## Course project

BUSA 310 Business Analytics III, DePauw University. Group Project 1: Real Estate Price Prediction Tool.

**Team:** _add names here_

**Scenario.** A regional real estate brokerage wants a tool that helps its agents price homes for sale. A realtor
enters a home's features and the tool suggests the price it should list at.

**Deliverables in this repository**

| Requirement | Where |
|---|---|
| Prediction model notebook (cleaning, EDA, modeling, evaluation, AI Use Log) | `notebook/BUS_310_Group_Project_Final.ipynb` |
| Hosted prediction tool | This repository, deployed on Streamlit Community Cloud (link above) |
| Dataset links and run instructions | [Run the notebook](#run-the-notebook) below |

**Model comparison** (from the notebook)

| Model | Random split R² | Random split MAE | Time-based R² | Time-based MAE |
|---|---|---|---|---|
| Linear regression | 0.386 | $110,936 | 0.323 | $135,692 |
| Random forest | 0.656 | $76,421 | 0.392 | $104,939 |
| Tuned random forest (deployed) | 0.656 | $77,290 | 0.411 | $104,456 |

The time-based test trains on 2019–2024 sales and predicts 2025–2026 sales. The deployed model is the tuned
random forest refit on all 107,321 sales.

## Project folder

| Path | What it is |
|---|---|
| `app.py` | Website entry point (page navigation) |
| `app_pages/` | The six pages: Estimate, Find homes, Market map, Price trends, How it works, About |
| `core/model_backend.py` | The group's backend from the notebook (address lookup, mortgage rate, prediction) |
| `core/insights.py` | Price range, per-house explanation, comparable sales, neighborhood facts |
| `core/ui.py` | Colors, styles, top bar, and shared page sections |
| `model/` | Files exported by the notebook: trained model, tract lookup, mortgage rate lookup |
| `data/` | Address lookup (`homes.csv.gz`), comparable sales, and market map data, built by `scripts/build_app_data.py` |
| `notebook/BUS_310_Group_Project_Final.ipynb` | The model notebook (Google Colab) |

## Run the notebook

Open `notebook/BUS_310_Group_Project_Final.ipynb` in Google Colab, upload the five input files listed in its
first cell, and run all cells. The last section exports the files that go in `model/`.

Input data (not stored in this repository because of file size):

- [Philadelphia Properties and Assessment History, OpenDataPhilly](https://opendataphilly.org/datasets/philadelphia-properties-and-assessment-history/)
- [Census ACS 2024 5-year B19013](https://data.census.gov/table/ACSDT5Y2024.B19013), [B25064](https://data.census.gov/table/ACSDT5Y2024.B25064), [B25003](https://data.census.gov/table/ACSDT5Y2024.B25003)
- [FRED MORTGAGE30US](https://fred.stlouisfed.org/series/MORTGAGE30US)
- [Census TIGER/Line 2024 tracts](https://www2.census.gov/geo/tiger/TIGER2024/TRACT/) (downloaded by the notebook)

## Run the website on your computer

Needs Python 3.9 to 3.12.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The site opens at http://localhost:8501.

## Rebuild the comparable sales and map data

Only needed if the input data changes. Put the five input CSVs in one folder, then:

```bash
pip install -r scripts/requirements-build.txt
python scripts/build_app_data.py --raw /path/to/input/folder
```

It repeats the notebook's cleaning steps (same 107,321 sales) and writes the files in `data/`.

## Deploy

1. Push this folder to a GitHub repository.
2. Sign in to [Streamlit Community Cloud](https://share.streamlit.io) with GitHub and choose **Create app**.
3. Pick the repository, branch `main`, and main file `app.py`. Under **Advanced settings**, choose Python 3.12.

## Home photos (optional)

Without setup, each estimate links to Google Street View and the City's property record. To show a Street View
photo on the page, create a Google Maps Platform API key with the **Street View Static API** enabled, then add it
as a secret named `GOOGLE_MAPS_API_KEY`:

- on your computer: in `.streamlit/secrets.toml` (never commit this file)
- on Streamlit Community Cloud: app **Settings → Secrets**

## Settings the group can change

In `core/insights.py`:

- `RANGE_METHOD`: `"typical_error"` (estimate ± the model's 2025–26 average error) or `"tree_spread"`
  (10th to 90th percentile of the 100 trees)
- `TYPICAL_ERROR`: update it if the model is retrained
- `CONDITION_LABELS`: the interior condition names shown in the form

In `core/ui.py`: `APP_NAME`, `TAGLINE`, colors, and the cover photo.

## Changes to the notebook's backend

`core/model_backend.py` is the notebook's `model_backend.py` with one change: file paths point to the `model/`
folder so the site runs from any working folder. The price on the website always comes from its
`predict_house_price` function.

## Credits

Cover photo by [@bryanangelo](https://unsplash.com/@bryanangelo) on [Unsplash](https://unsplash.com). Map tiles © CARTO, © OpenStreetMap contributors.
