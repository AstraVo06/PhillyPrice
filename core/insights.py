"""
Website helpers built on top of the team's model_backend.py:
the price range, the per-house explanation, comparable sales and
neighborhood facts. The price itself always comes from model_backend.
"""

import os
import re
from functools import lru_cache

import numpy as np
import pandas as pd

from core import model_backend as mb

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO, "data")

# --------------------------------------------------
# Settings the group can change
# --------------------------------------------------

# Mean absolute error of the tuned Random Forest on 2025-2026 sales
# (notebook: "Tuned Random Forest - Time-Based Validation").
TYPICAL_ERROR = 104_456

# How the likely price range is built:
#   "price_band"    -> 8 in 10 range for the home's price level (RANGE_BANDS below)
#   "typical_error" -> estimate +/- TYPICAL_ERROR
#   "tree_spread"   -> 10th to 90th percentile of the 100 trees' predictions
RANGE_METHOD = "price_band"

# For each level of estimated price: (top of the level, low multiplier, high multiplier).
# 8 in 10 of the 2025-2026 sales, priced by a copy of the tuned model trained on 2019-2024 only,
# sold between estimate x low and estimate x high. Recompute with scripts/check_price_range.py.
RANGE_BANDS = [
    (150_000, 0.309, 1.450),
    (250_000, 0.422, 1.313),
    (400_000, 0.514, 1.271),
    (700_000, 0.633, 1.300),
    (float("inf"), 0.725, 1.435),
]

# Lowest sale price kept in the training data.
MIN_PRICE = 10_000

# OPA interior condition codes offered in the form.
CONDITION_LABELS = {
    1: "New construction",
    2: "Updated",
    3: "Above average",
    4: "Average",
    5: "Below average",
    6: "Substantial damage",
    7: "Uninhabitable",
}

TIMING_FEATURES = ["mortgage_rate", "sale_year", "sale_month"]


# --------------------------------------------------
# Data files
# --------------------------------------------------

@lru_cache(maxsize=1)
def load_sales():
    sales = pd.read_csv(os.path.join(DATA_DIR, "recent_sales.csv.gz"), parse_dates=["sale_date"])
    return sales


@lru_cache(maxsize=1)
def load_tract_stats():
    return pd.read_csv(os.path.join(DATA_DIR, "tract_stats.csv"), dtype={"GEOID": str})


@lru_cache(maxsize=1)
def load_tract_names():
    names = pd.read_csv(os.path.join(DATA_DIR, "tract_names.csv"), dtype={"GEOID": str})
    names["zip_code"] = names["zip_code"].astype("Int64").astype(str).replace("<NA>", "")
    return names.set_index("GEOID")


def tract_label(geoid):
    """'Fishtown - Lower Kensington · ZIP 19125' instead of a census tract number."""
    names = load_tract_names()
    if geoid not in names.index:
        return "This area"
    row = names.loc[geoid]
    zip_part = f" · ZIP {row['zip_code']}" if row["zip_code"] else ""
    return f"{row['neighborhood']}{zip_part}"


@lru_cache(maxsize=1)
def load_zip_stats():
    return pd.read_csv(os.path.join(DATA_DIR, "zip_stats.csv"))


@lru_cache(maxsize=1)
def market_sales():
    """Single-parcel sales with year and price per square foot, for maps and trends."""
    sales = load_sales()
    sales = sales[~sales["multi_parcel_sale"]].copy()
    sales["year"] = sales["sale_date"].dt.year
    sales["price_per_sqft"] = sales["sale_price"] / sales["total_livable_area"]
    return sales


SALES_METRICS = {
    "Typical sale price": ("sale_price", "median"),
    "Price per square foot": ("price_per_sqft", "median"),
    "Number of sales": ("sale_price", "size"),
}


@lru_cache(maxsize=64)
def tract_sales_metric(metric, first_year, last_year):
    column, how = SALES_METRICS[metric]
    sales = market_sales()
    sales = sales[sales["year"].between(first_year, last_year)]
    grouped = sales.groupby("GEOID")
    out = pd.DataFrame({"value": grouped[column].agg(how), "sales": grouped.size()}).reset_index()
    out["GEOID"] = out["GEOID"].astype(str)
    return out


@lru_cache(maxsize=64)
def area_trend(metric, areas):
    """Yearly values of a sales metric for 'All of Philadelphia' and/or ZIP codes."""
    column, how = SALES_METRICS[metric]
    sales = market_sales()
    rows = []
    for area in areas:
        subset = sales if area == "All of Philadelphia" else sales[sales["zip_code"] == int(area)]
        yearly = subset.groupby("year")[column].agg(how)
        rows += [{"area": area if area == "All of Philadelphia" else f"ZIP {area}", "year": year, "value": value}
                 for year, value in yearly.items()]
    return pd.DataFrame(rows)


def mortgage_rates(first_year=2019):
    rates = mb.mortgage_lookup.copy()
    rates["month"] = rates["sale_month"].dt.to_timestamp()
    return rates[rates["month"].dt.year >= first_year][["month", "mortgage_rate"]]


@lru_cache(maxsize=1)
def zip_centers():
    sales = market_sales()
    return sales.groupby("zip_code")[["lat", "lon"]].median()


@lru_cache(maxsize=1)
def load_tract_shapes():
    import json
    with open(os.path.join(DATA_DIR, "philly_tracts.geojson")) as f:
        return json.load(f)


# --------------------------------------------------
# Address search in the city's records
# --------------------------------------------------

@lru_cache(maxsize=1)
def load_homes():
    homes = pd.read_csv(os.path.join(DATA_DIR, "homes.csv.gz"), dtype={"GEOID": str, "parcel_number": str},
                        parse_dates=["sale_date"])
    return homes


@lru_cache(maxsize=1)
def _home_index():
    homes = load_homes()
    return {"address": homes.groupby("address").indices, "street": homes.groupby("street").indices}


def find_homes(address):
    """Homes in the city's records matching a typed address. A building with several units returns all of them."""
    key = opa_address(address)
    index = _home_index()
    rows = index["address"].get(key) if "#" in key else index["street"].get(key)
    if rows is None:
        return load_homes().iloc[0:0]
    return load_homes().iloc[rows].sort_values("address").reset_index(drop=True)


HOUSE_NUMBER = r"^(\d+)[A-Z]?(?:-\d+)?\s+"


@lru_cache(maxsize=1)
def _street_index():
    """Street name ('JASPER ST') -> row positions, and the house number of every home."""
    homes = load_homes()
    names = homes["street"].str.replace(HOUSE_NUMBER, "", regex=True)
    numbers = pd.to_numeric(homes["street"].str.extract(HOUSE_NUMBER)[0], errors="coerce")
    return names.groupby(names).indices, numbers.to_numpy(), names.to_numpy()


def suggest_homes(text, limit=1500):
    """Homes for a partial search like 'Jasper St', 'jasper', or '2618 Jaspr St'.
    Returns (street names matched, homes), nearest house numbers first when a number was typed."""
    import difflib

    key = opa_address(text).split(" #")[0]
    number = re.match(HOUSE_NUMBER, key + " ")
    name = re.sub(HOUSE_NUMBER, "", key + " ").strip()
    if not name:
        return [], load_homes().iloc[0:0]
    streets, numbers, names = _street_index()
    padded = f" {name} "
    found = [s for s in streets if s == name]
    found = found or [s for s in streets if s.startswith(name + " ") or f" {s} ".find(padded) >= 0]
    found = found or difflib.get_close_matches(name, list(streets), n=4, cutoff=0.8)
    if not found:
        return [], load_homes().iloc[0:0]
    rows = np.concatenate([streets[s] for s in found])
    homes = load_homes().iloc[rows].copy()
    homes["house_number"], homes["street_name"] = numbers[rows], names[rows]
    if number:
        homes["gap"] = (homes["house_number"] - int(number.group(1))).abs()
        homes = homes.sort_values(["gap", "address"])
    else:
        homes = homes.sort_values(["street_name", "house_number", "address"])
    return found, homes.head(limit).reset_index(drop=True)


def featured_homes():
    """A few recently sold homes with good street photos, for visitors who just want to look around."""
    picks = pd.read_csv(os.path.join(DATA_DIR, "featured_homes.csv"), dtype={"parcel_number": str})
    homes = load_homes().set_index("parcel_number")
    return homes.loc[picks["parcel_number"]].reset_index()


def home_details(home):
    """The home's details from the city's records, with sensible fill-ins where a record is blank or zero."""
    def pick(value, low, high, fallback):
        try:
            value = int(round(float(value)))
        except (TypeError, ValueError):
            return fallback
        return value if low <= value <= high else fallback

    return {
        "beds": pick(home["number_of_bedrooms"], 1, 6, 3),
        "baths": pick(home["number_of_bathrooms"], 1, 4, 1),
        "sqft": pick(home["total_livable_area"], 300, 10000, 1200),
        "year": pick(home["year_built"], 1750, pd.Timestamp.today().year, 1925),
        "condition": pick(home["interior_condition"], 1, 7, 4),
    }


def street_view_url(lat, lon):
    return f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat},{lon}"


def city_record_url(parcel_number):
    return f"https://property.phila.gov/?p={parcel_number}"


# --------------------------------------------------
# Location
# --------------------------------------------------

def locate(address):
    """Geocode an address with the backend and add the City Hall distance."""
    location = mb.get_location_info(address)
    geoid = str(location["GEOID"])
    if not geoid.startswith("42101"):
        raise ValueError("This tool only covers homes in Philadelphia.")
    location["GEOID"] = geoid
    location["distance_city_hall_miles"] = mb.calculate_city_hall_distance(
        latitude=location["latitude"], longitude=location["longitude"]
    )
    return location


# --------------------------------------------------
# Estimate
# --------------------------------------------------

def build_features(location, living_area, bedrooms, bathrooms, interior_condition, year_built,
                   prediction_date=None):
    """The same model input row that model_backend.predict_house_price builds."""
    prediction_date = pd.Timestamp.today() if prediction_date is None else pd.to_datetime(prediction_date)
    tract = mb.tract_lookup[mb.tract_lookup["GEOID"] == location["GEOID"]]
    if tract.empty:
        raise ValueError("This census tract is not in the Philadelphia lookup.")
    tract = tract.iloc[0]
    row = pd.DataFrame([{
        "total_livable_area": living_area,
        "number_of_bedrooms": bedrooms,
        "number_of_bathrooms": bathrooms,
        "interior_condition": interior_condition,
        "house_age": prediction_date.year - year_built,
        "zip_code": float(location["zip_code"]),
        "median_household_income": tract["median_household_income"],
        "median_gross_rent": tract["median_gross_rent"],
        "owner_occupied_pct": tract["owner_occupied_pct"],
        "mortgage_rate": mb.get_mortgage_rate_for_date(prediction_date),
        "distance_city_hall_miles": location["distance_city_hall_miles"],
        "sale_year": prediction_date.year,
        "sale_month": prediction_date.month,
    }])
    return row[mb.MODEL_FEATURES]


def estimate(address, living_area, bedrooms, bathrooms, interior_condition, year_built):
    """Estimate for a typed address: the Census geocoder finds the location."""
    return estimate_at(locate(address), address, living_area, bedrooms, bathrooms, interior_condition, year_built)


def estimate_home(home, living_area, bedrooms, bathrooms, interior_condition, year_built):
    """Estimate for a home found in the city's records, which already have its location."""
    location = {
        "latitude": float(home["lat"]),
        "longitude": float(home["lon"]),
        "zip_code": str(int(home["zip_code"])),
        "GEOID": str(home["GEOID"]),
    }
    location["distance_city_hall_miles"] = mb.calculate_city_hall_distance(
        latitude=location["latitude"], longitude=location["longitude"]
    )
    return estimate_at(location, home["address"], living_area, bedrooms, bathrooms, interior_condition, year_built)


def quick_price(location, living_area, bedrooms, bathrooms, interior_condition, year_built):
    """Just the model's price for a known location, for the what-if sliders."""
    return mb.predict_house_price(
        living_area=living_area, bedrooms=bedrooms, bathrooms=bathrooms,
        interior_condition=interior_condition, year_built=year_built,
        zip_code=location["zip_code"], geoid=location["GEOID"],
        distance_city_hall_miles=location["distance_city_hall_miles"],
    )


def zip_percentile(zip_code, price, since_year=2024):
    """Share of single-family homes in the ZIP code that sold for less than this price since `since_year`."""
    sales = market_sales()
    prices = sales[(sales["zip_code"] == int(zip_code)) & (sales["year"] >= since_year)]["sale_price"]
    if len(prices) < 20:
        return None, len(prices)
    return float((prices < price).mean() * 100), len(prices)


def estimate_at(location, address, living_area, bedrooms, bathrooms, interior_condition, year_built):
    price = mb.predict_house_price(
        living_area=living_area,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        interior_condition=interior_condition,
        year_built=year_built,
        zip_code=location["zip_code"],
        geoid=location["GEOID"],
        distance_city_hall_miles=location["distance_city_hall_miles"],
    )
    row = build_features(location, living_area, bedrooms, bathrooms, interior_condition, year_built)
    low, high = price_range(row, price)
    baseline, factors = explain(row)
    return {
        "price": price,
        "low": low,
        "high": high,
        "location": location,
        "features": row.iloc[0].to_dict(),
        "baseline": baseline,
        "factors": factors,
        "comps": comparable_sales(location["latitude"], location["longitude"], living_area, bedrooms,
                                  exclude_address=address),
        "last_sale": last_sale(address),
        "neighborhood": neighborhood(location),
    }


def _transform(row):
    Xt = mb.model.named_steps["preprocessor"].transform(row)
    return Xt.toarray() if hasattr(Xt, "toarray") else np.asarray(Xt)


def price_range(row, price):
    if RANGE_METHOD == "tree_spread":
        Xt = _transform(row).astype(np.float32)
        trees = np.array([tree.predict(Xt)[0] for tree in mb.model.named_steps["model"].estimators_])
        low, high = np.percentile(trees, [10, 90])
    elif RANGE_METHOD == "price_band":
        _, low_x, high_x = next(band for band in RANGE_BANDS if price < band[0])
        low, high = price * low_x, price * high_x
    else:
        low, high = price - TYPICAL_ERROR, price + TYPICAL_ERROR
    return float(max(low, MIN_PRICE)), float(high)


def _original_feature(name):
    """Map a transformed column name (num__x, cat__zip_code_19107.0) back to its input column."""
    kind, column = name.split("__", 1)
    if kind == "num":
        return column
    for feature in mb.MODEL_FEATURES:
        if column.startswith(feature + "_"):
            return feature
    return column


def explain(row):
    """
    Split one prediction into a starting value plus one amount per input, by following
    each tree's decision path and crediting every split's change in predicted value to
    the feature it split on, then averaging over the trees. Starting value plus all
    amounts equals the model's prediction.
    """
    preprocessor = mb.model.named_steps["preprocessor"]
    forest = mb.model.named_steps["model"]
    Xt = _transform(row).astype(np.float32)

    contributions = np.zeros(Xt.shape[1])
    baseline = 0.0
    for tree in forest.estimators_:
        structure = tree.tree_
        values = structure.value[:, 0, 0]
        path = np.sort(tree.decision_path(Xt).indices)
        baseline += values[path[0]]
        for parent, child in zip(path[:-1], path[1:]):
            contributions[structure.feature[parent]] += values[child] - values[parent]
    baseline /= len(forest.estimators_)
    contributions /= len(forest.estimators_)

    by_feature = (pd.Series(contributions, index=[_original_feature(n) for n in preprocessor.get_feature_names_out()])
                  .groupby(level=0).sum())
    timing = by_feature.reindex(TIMING_FEATURES).fillna(0).sum()
    by_feature = by_feature.drop(TIMING_FEATURES, errors="ignore")
    by_feature["market_timing"] = timing

    features = row.iloc[0]
    factors = pd.DataFrame({
        "feature": by_feature.index,
        "label": [_label(f, features) for f in by_feature.index],
        "amount": by_feature.values,
    })
    factors = factors.reindex(factors["amount"].abs().sort_values(ascending=False).index).reset_index(drop=True)
    return float(baseline), factors


def _label(feature, f):
    month = pd.Timestamp(year=int(f["sale_year"]), month=int(f["sale_month"]), day=1).strftime("%b %Y")
    labels = {
        "total_livable_area": f"Living area · {f['total_livable_area']:,.0f} sq ft",
        "number_of_bedrooms": f"Bedrooms · {f['number_of_bedrooms']:.0f}",
        "number_of_bathrooms": f"Bathrooms · {f['number_of_bathrooms']:.0f}",
        "interior_condition": f"Interior condition · {CONDITION_LABELS.get(int(f['interior_condition']), f['interior_condition'])}",
        "house_age": f"House age · {f['house_age']:.0f} years",
        "zip_code": f"ZIP code · {f['zip_code']:.0f}",
        "median_household_income": f"Area income · ${f['median_household_income']:,.0f}",
        "median_gross_rent": f"Area rent · ${f['median_gross_rent']:,.0f}/mo",
        "owner_occupied_pct": f"Area homeownership · {f['owner_occupied_pct']:.0f}%",
        "distance_city_hall_miles": f"Distance to City Hall · {f['distance_city_hall_miles']:.1f} mi",
        "market_timing": f"Market timing · {month}, {f['mortgage_rate']:.2f}% mortgage rate",
    }
    return labels.get(feature, feature)


# --------------------------------------------------
# Comparable sales and neighborhood facts
# --------------------------------------------------

def _miles(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 3958.8 * 2 * np.arcsin(np.sqrt(a))


STREET_WORDS = {"STREET": "ST", "AVENUE": "AVE", "ROAD": "RD", "BOULEVARD": "BLVD", "DRIVE": "DR",
                "LANE": "LN", "PLACE": "PL", "TERRACE": "TER", "COURT": "CT", "SQUARE": "SQ",
                "PARKWAY": "PKWY", "NORTH": "N", "SOUTH": "S", "EAST": "E", "WEST": "W"}


UNIT_PATTERN = r"(?:#|\bUNIT\b|\bAPT\b|\bAPARTMENT\b|\bSTE\b)\s*([A-Z0-9-]+)"


def opa_address(address):
    """Turn a typed address like '2618 Jasper Street, Philadelphia' into the city's format '2618 JASPER ST'.
    A unit anywhere in the text ('#3B', 'Unit 3B', 'Apt 3B') becomes ' #3B'."""
    text = address.upper().replace(".", " ")
    unit = re.search(UNIT_PATTERN, text)
    street = re.sub(UNIT_PATTERN, "", text.split(",")[0])
    words = [STREET_WORDS.get(word, word) for word in street.split()]
    return " ".join(words) + (f" #{unit.group(1)}" if unit else "")


def last_sale(address):
    """The most recent recorded sale of this exact address in the cleaned data, if any."""
    sales = load_sales()
    match = sales[sales["address"] == opa_address(address)]
    if match.empty:
        return None
    return match.sort_values("sale_date").iloc[-1].to_dict()


def comparable_sales(latitude, longitude, living_area, bedrooms, count=5, exclude_address=None):
    """Recent single-parcel sales nearby with a similar size and bedroom count."""
    sales = load_sales()
    sales = sales[~sales["multi_parcel_sale"]]
    if exclude_address:
        sales = sales[sales["address"] != opa_address(exclude_address)]
    similar = sales[sales["total_livable_area"].between(0.75 * living_area, 1.25 * living_area)
                    & ((sales["number_of_bedrooms"] - bedrooms).abs() <= 1)].copy()
    similar["distance_miles"] = _miles(latitude, longitude, similar["lat"], similar["lon"])

    newest = sales["sale_date"].max()
    comps = similar.iloc[0:0]
    for radius, years in [(0.5, 2), (1.0, 3), (2.0, 8)]:
        comps = similar[(similar["distance_miles"] <= radius)
                        & (similar["sale_date"] >= newest - pd.DateOffset(years=years))]
        if len(comps) >= 3:
            break
    closest = comps.nsmallest(count * 3, "distance_miles")
    return closest.sort_values("sale_date", ascending=False).head(count).reset_index(drop=True)


def neighborhood(location):
    tract = mb.tract_lookup[mb.tract_lookup["GEOID"] == location["GEOID"]].iloc[0]
    tract_stats = load_tract_stats().set_index("GEOID")
    zip_stats = load_zip_stats().set_index("zip_code")
    zip_code = int(location["zip_code"])
    return {
        "median_household_income": tract["median_household_income"],
        "median_gross_rent": tract["median_gross_rent"],
        "owner_occupied_pct": tract["owner_occupied_pct"],
        "tract_median_price": tract_stats["median_price"].get(location["GEOID"]),
        "tract_sales": tract_stats["sales"].get(location["GEOID"]),
        "zip_median_price": zip_stats["median_price"].get(zip_code),
    }


# --------------------------------------------------
# Price a home by its details and neighborhood (no address)
# --------------------------------------------------

@lru_cache(maxsize=1)
def neighborhood_locations():
    """Neighborhood name -> one location per census tract in it (most common ZIP, middle of its homes)."""
    homes = load_homes()
    homes = homes[homes["GEOID"].isin(set(mb.tract_lookup["GEOID"]))]
    tracts = homes.groupby("GEOID").agg(zip_code=("zip_code", lambda z: z.mode().iat[0]),
                                        lat=("lat", "median"), lon=("lon", "median"), homes=("lat", "size"))
    tracts = tracts[tracts["homes"] >= 25].join(load_tract_names()["neighborhood"], how="inner")
    places = {}
    for geoid, t in tracts.iterrows():
        places.setdefault(t["neighborhood"], []).append({
            "GEOID": geoid, "zip_code": str(int(t["zip_code"])), "latitude": t["lat"], "longitude": t["lon"],
            "distance_city_hall_miles": mb.calculate_city_hall_distance(latitude=t["lat"], longitude=t["lon"]),
        })
    return dict(sorted(places.items()))


def price_by_details(neighborhood, living_area, bedrooms, bathrooms, interior_condition, year_built):
    """The model's price for this home in each part of the neighborhood; the middle one is the estimate."""
    locations = neighborhood_locations()[neighborhood]
    prices = sorted(quick_price(loc, living_area, bedrooms, bathrooms, interior_condition, year_built)
                    for loc in locations)
    price = float(np.median(prices))
    low, high = price_range(None, price)
    return {"price": price, "low": low, "high": high, "areas": len(prices), "cheapest_area": prices[0],
            "priciest_area": prices[-1], "zips": sorted({loc["zip_code"] for loc in locations})}


# --------------------------------------------------
# Insights for agents
# --------------------------------------------------

DRIVER_GROUPS = {
    "Location": ["distance_city_hall_miles", "zip_code", "median_household_income", "median_gross_rent",
                 "owner_occupied_pct"],
    "Size (living area)": ["total_livable_area"],
    "Market timing": ["mortgage_rate", "sale_month", "sale_year"],
    "Age of the home": ["house_age"],
    "Bathrooms": ["number_of_bathrooms"],
    "Condition inside": ["interior_condition"],
    "Bedrooms": ["number_of_bedrooms"],
}
DRIVER_NAMES = {
    "total_livable_area": "Living area", "distance_city_hall_miles": "Distance from City Hall",
    "zip_code": "ZIP code", "median_household_income": "Neighborhood income", "mortgage_rate": "Mortgage rate",
    "sale_month": "Month of sale", "house_age": "Age of the home", "median_gross_rent": "Neighborhood rent",
    "number_of_bathrooms": "Bathrooms", "sale_year": "Year of sale", "interior_condition": "Condition inside",
    "owner_occupied_pct": "Share of owners in the area", "number_of_bedrooms": "Bedrooms",
}


@lru_cache(maxsize=1)
def price_drivers():
    """Share of the model's decisions that use each input (Random Forest importance), by input and by group."""
    preprocessor, forest = mb.model.named_steps["preprocessor"], mb.model.named_steps["model"]
    names = [_original_feature(n) for n in preprocessor.get_feature_names_out()]
    by_input = pd.Series(forest.feature_importances_, index=names).groupby(level=0).sum() * 100
    by_group = pd.Series({group: by_input.reindex(cols).sum() for group, cols in DRIVER_GROUPS.items()})
    return by_group.sort_values(ascending=False), by_input.rename(DRIVER_NAMES).sort_values(ascending=False)


@lru_cache(maxsize=4)
def neighborhood_ranking(since_year=2024, min_sales=40):
    """Median sale price and price per square foot by neighborhood, for neighborhoods with enough sales."""
    sales = market_sales()
    sales = sales[sales["year"] >= since_year].copy()
    sales["neighborhood"] = sales["GEOID"].astype(str).map(load_tract_names()["neighborhood"])
    ranked = sales.groupby("neighborhood").agg(sales=("sale_price", "size"), median_price=("sale_price", "median"),
                                               price_per_sqft=("price_per_sqft", "median"))
    return ranked[ranked["sales"] >= min_sales].sort_values("median_price", ascending=False)


@lru_cache(maxsize=1)
def price_gaps(since_year=2024):
    """Typical prices across distance, neighborhood income, and condition, plus the yearly city median."""
    sales = market_sales()
    recent = sales[sales["year"] >= since_year].copy()
    income = mb.tract_lookup.set_index("GEOID")["median_household_income"]
    recent["income"] = recent["GEOID"].astype(str).map(income)
    distance = pd.cut(recent["distance_city_hall_miles"], [0, 2, 4, 6, 9, 30],
                      labels=["Under 2 mi", "2–4 mi", "4–6 mi", "6–9 mi", "Over 9 mi"])
    income_q = pd.qcut(recent["income"], 4, labels=["Lowest-income 25%", "Second 25%", "Third 25%",
                                                    "Highest-income 25%"])
    conditions = {1: "New", 2: "Updated", 3: "Above average", 4: "Average", 5: "Below average",
                  6: "Major damage", 7: "Not livable"}
    by_condition = (recent[recent["interior_condition"].isin(conditions)]
                    .groupby("interior_condition")["price_per_sqft"].median().rename(index=conditions))
    return {
        "city_median": float(recent["sale_price"].median()),
        "city_ppsf": float(recent["price_per_sqft"].median()),
        "distance": recent.groupby(distance, observed=True)["sale_price"].median(),
        "income": recent.groupby(income_q, observed=True)["sale_price"].median(),
        "condition": by_condition,
        "yearly": sales.groupby("year")["sale_price"].median(),
    }
