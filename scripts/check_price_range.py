"""
Where the price range on the site comes from.

Retrains a copy of the deployed tuned Random Forest on 2019-2024 sales only (the notebook's time-based
validation), prices the 2025-2026 sales it never saw, and reports, for each level of estimated price,
the 10th and 90th percentile of (actual sale price / estimate). 8 in 10 of those sales landed between
the two, so the site shows estimate x low to estimate x high as the range.

Run from the repository folder (takes about a minute):
    python scripts/check_price_range.py
Then copy the printed RANGE_BANDS into core/insights.py.
"""

import os

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import mean_absolute_error

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAND_TOPS = [150_000, 250_000, 400_000, 700_000, float("inf")]
FEATURES = ["total_livable_area", "number_of_bedrooms", "number_of_bathrooms", "interior_condition", "house_age",
            "zip_code", "median_household_income", "median_gross_rent", "owner_occupied_pct", "mortgage_rate",
            "distance_city_hall_miles", "sale_year", "sale_month", "sale_year_fe"]

sales = pd.read_csv(os.path.join(REPO, "data", "recent_sales.csv.gz"), parse_dates=["sale_date"], dtype={"GEOID": str})
tracts = pd.read_csv(os.path.join(REPO, "model", "philadelphia_census_tract_lookup_complete.csv"), dtype={"GEOID": str})
rates = pd.read_csv(os.path.join(REPO, "model", "mortgage_rate_monthly_lookup.csv"))
rates["period"] = pd.PeriodIndex(rates.pop("sale_month"), freq="M")

df = sales.merge(tracts[["GEOID", "median_household_income", "median_gross_rent", "owner_occupied_pct"]], on="GEOID")
df["period"] = df["sale_date"].dt.to_period("M")
df = df.merge(rates, on="period")
df["sale_year"], df["sale_month"] = df["sale_date"].dt.year, df["sale_date"].dt.month
df["house_age"] = df["sale_year"] - df["year_built"]
df["sale_year_fe"] = df["sale_year"].astype(str)

train, test = df[df["sale_year"] <= 2024], df[df["sale_year"] >= 2025].copy()
model = clone(joblib.load(os.path.join(REPO, "model", "philadelphia_house_price_model_compressed.joblib")))
model.fit(train[FEATURES], train["sale_price"])
test["estimate"] = model.predict(test[FEATURES])
print(f"Trained on {len(train):,} sales (2019-2024), tested on {len(test):,} (2025-2026). "
      f"MAE ${mean_absolute_error(test['sale_price'], test['estimate']):,.0f}")

# Sales where several homes changed hands for one total price aren't a single home's price.
test = test[~test["multi_parcel_sale"]]
test["ratio"] = test["sale_price"] / test["estimate"]
test["band"] = np.searchsorted(BAND_TOPS, test["estimate"], side="right")

bands = []
for i, top in enumerate(BAND_TOPS):
    ratios = test.loc[test["band"] == i, "ratio"]
    low, high = ratios.quantile([0.1, 0.9])
    bands.append((top, round(low, 3), round(high, 3)))
    print(f"estimate under {top:>12,.0f}: {len(ratios):>6,} sales, 8 in 10 sold at {low:.2f}x to {high:.2f}x")

covered = np.mean([low <= r <= high for (_, low, high), r in
                   zip([bands[b] for b in test["band"]], test["ratio"])])
print(f"Share of 2025-2026 sales inside their range: {covered:.1%}")
print("RANGE_BANDS =", [(b if b != float("inf") else "inf", lo, hi) for b, lo, hi in bands])
