
import math
import os
import joblib
import requests
import pandas as pd

from pyproj import Transformer


# --------------------------------------------------
# Files
# (website change: paths point to the model/ folder of the repo,
#  so the app works no matter which folder it is started from)
# --------------------------------------------------

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "model")

MODEL_FILE = os.path.join(MODEL_DIR, "philadelphia_house_price_model_compressed.joblib")
TRACT_FILE = os.path.join(MODEL_DIR, "philadelphia_census_tract_lookup_complete.csv")
MORTGAGE_FILE = os.path.join(MODEL_DIR, "mortgage_rate_monthly_lookup.csv")


# --------------------------------------------------
# Load model and lookup tables
# --------------------------------------------------

model = joblib.load(MODEL_FILE)

tract_lookup = pd.read_csv(
    TRACT_FILE,
    dtype={"GEOID": str}
)

mortgage_lookup = pd.read_csv(
    MORTGAGE_FILE
)

mortgage_lookup["sale_month"] = pd.PeriodIndex(
    mortgage_lookup["sale_month"],
    freq="M"
)


# --------------------------------------------------
# Model features
# --------------------------------------------------

MODEL_FEATURES = [
    "total_livable_area",
    "number_of_bedrooms",
    "number_of_bathrooms",
    "interior_condition",
    "house_age",
    "zip_code",
    "median_household_income",
    "median_gross_rent",
    "owner_occupied_pct",
    "mortgage_rate",
    "distance_city_hall_miles",
    "sale_year",
    "sale_month"
]


# --------------------------------------------------
# City Hall coordinates
# --------------------------------------------------

CITY_HALL_LONGITUDE = -75.1636
CITY_HALL_LATITUDE = 39.9526

transformer_to_2272 = Transformer.from_crs(
    "EPSG:4326",
    "EPSG:2272",
    always_xy=True
)


# --------------------------------------------------
# Mortgage Rate
# --------------------------------------------------

def get_mortgage_rate_for_date(prediction_date):

    prediction_date = pd.to_datetime(prediction_date)

    if prediction_date.tzinfo is not None:
        prediction_date = prediction_date.tz_localize(None)

    prediction_month = prediction_date.to_period("M")

    available_rates = mortgage_lookup[
        mortgage_lookup["sale_month"] <= prediction_month
    ].sort_values("sale_month")

    if available_rates.empty:
        raise ValueError(
            "No mortgage rate available for this date."
        )

    return available_rates.iloc[-1]["mortgage_rate"]


# --------------------------------------------------
# Address → location
# --------------------------------------------------

def get_location_info(address):

    url = (
        "https://geocoding.geo.census.gov/"
        "geocoder/geographies/onelineaddress"
    )

    params = {
        "address": address,
        "benchmark": "Public_AR_Current",
        "vintage": "Current_Current",
        "format": "json"
    }

    response = requests.get(
        url,
        params=params,
        timeout=20
    )

    response.raise_for_status()

    data = response.json()

    matches = data["result"]["addressMatches"]

    if len(matches) == 0:
        raise ValueError(
            "Address could not be found."
        )

    match = matches[0]

    latitude = match["coordinates"]["y"]
    longitude = match["coordinates"]["x"]

    zip_code = match["addressComponents"]["zip"]

    geographies = match["geographies"]

    census_tract = geographies[
        "Census Tracts"
    ][0]

    geoid = census_tract["GEOID"]

    return {
        "latitude": latitude,
        "longitude": longitude,
        "zip_code": zip_code,
        "GEOID": geoid
    }


# --------------------------------------------------
# City Hall distance
# --------------------------------------------------

def calculate_city_hall_distance(
    latitude,
    longitude
):

    property_x, property_y = transformer_to_2272.transform(
        longitude,
        latitude
    )

    city_hall_x, city_hall_y = transformer_to_2272.transform(
        CITY_HALL_LONGITUDE,
        CITY_HALL_LATITUDE
    )

    distance_feet = math.sqrt(
        (property_x - city_hall_x) ** 2
        +
        (property_y - city_hall_y) ** 2
    )

    return distance_feet / 5280


# --------------------------------------------------
# Model prediction
# --------------------------------------------------

def predict_house_price(
    living_area,
    bedrooms,
    bathrooms,
    interior_condition,
    year_built,
    zip_code,
    geoid,
    distance_city_hall_miles,
    prediction_date=None
):

    if prediction_date is None:
        prediction_date = pd.Timestamp.today()
    else:
        prediction_date = pd.to_datetime(
            prediction_date
        )

    sale_year = prediction_date.year
    sale_month = prediction_date.month

    if year_built > sale_year:
        raise ValueError(
            "Year built cannot be after the prediction year."
        )

    house_age = sale_year - year_built

    mortgage_rate = get_mortgage_rate_for_date(
        prediction_date
    )

    tract_row = tract_lookup[
        tract_lookup["GEOID"] == str(geoid)
    ]

    if tract_row.empty:
        raise ValueError(
            "Census tract is not available in the Philadelphia lookup."
        )

    tract_row = tract_row.iloc[0]

    house = pd.DataFrame([{
        "total_livable_area":
            living_area,

        "number_of_bedrooms":
            bedrooms,

        "number_of_bathrooms":
            bathrooms,

        "interior_condition":
            interior_condition,

        "house_age":
            house_age,

        "zip_code":
            float(zip_code),

        "median_household_income":
            tract_row["median_household_income"],

        "median_gross_rent":
            tract_row["median_gross_rent"],

        "owner_occupied_pct":
            tract_row["owner_occupied_pct"],

        "mortgage_rate":
            mortgage_rate,

        "distance_city_hall_miles":
            distance_city_hall_miles,

        "sale_year":
            sale_year,

        "sale_month":
            sale_month
    }])

    house = house[MODEL_FEATURES]

    prediction = model.predict(house)[0]

    return float(prediction)


# --------------------------------------------------
# Complete website prediction
# --------------------------------------------------

def predict_price_from_address(
    address,
    living_area,
    bedrooms,
    bathrooms,
    interior_condition,
    year_built,
    prediction_date=None
):

    location = get_location_info(
        address
    )

    geoid = str(
        location["GEOID"]
    )

    if not geoid.startswith("42101"):
        raise ValueError(
            "This model is designed for Philadelphia properties only."
        )

    distance = calculate_city_hall_distance(
        latitude=location["latitude"],
        longitude=location["longitude"]
    )

    predicted_price = predict_house_price(
        living_area=living_area,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        interior_condition=interior_condition,
        year_built=year_built,
        zip_code=location["zip_code"],
        geoid=geoid,
        distance_city_hall_miles=distance,
        prediction_date=prediction_date
    )

    return {
        "predicted_price":
            float(predicted_price),

        "zip_code":
            location["zip_code"],

        "GEOID":
            geoid,

        "distance_city_hall_miles":
            float(distance)
    }
