"""
Build the small data files the website uses for comparable sales and the market map.

The cleaning steps are the same as the "Cleaning and Merging" section of
notebook/BUS_310_Group_Project_Final.ipynb (single-family, 2019-2026 sales,
$10K-$5M, valid size/rooms/year built, ACS and FRED merged), so the website
works from exactly the same 107,321 sales the model was trained on.

Usage (from the repo root):
    pip install -r scripts/requirements-build.txt
    python scripts/build_app_data.py --raw /path/to/folder/with/the/5/input/csvs

Outputs (in data/):
    recent_sales.csv.gz      one row per cleaned sale, with address and lat/lon
    homes.csv.gz             every single-family property in the city, for the address search
    tract_stats.csv          median sale price per census tract
    zip_stats.csv            median sale price per ZIP code
    philly_tracts.geojson    simplified Philadelphia census tract boundaries
    tract_names.csv          neighborhood name and main ZIP code for each census tract
"""

import argparse
import os

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely import wkt
from shapely.geometry import Point

TRACT_URL = "https://www2.census.gov/geo/tiger/TIGER2024/TRACT/tl_2024_42_tract.zip"
NEIGHBORHOODS_URL = ("https://raw.githubusercontent.com/opendataphilly/open-geo-data/master/"
                     "philadelphia-neighborhoods/philadelphia-neighborhoods.geojson")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "data")

# A sale counts as a multi-parcel (bulk) transaction when 3 or more parcels share
# the same sale date and the exact same price. The website leaves these out of
# comparable sales and the market map because the price covers the whole deal.
BULK_MIN_PARCELS = 3


def load_opa(raw):
    cols = ["sale_price", "sale_date", "total_livable_area", "number_of_bedrooms",
            "number_of_bathrooms", "interior_condition", "year_built", "zip_code",
            "census_tract", "category_code_description", "shape", "parcel_number", "location", "unit"]
    df = pd.read_csv(os.path.join(raw, "opa_properties_public (1).csv"), usecols=cols, low_memory=False)
    df = df[df["category_code_description"] == "SINGLE FAMILY"].copy()
    df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce")
    df = df[df["sale_date"].dt.year.between(2019, 2026)]
    df = df[(df["sale_price"] >= 10000) & (df["sale_price"] <= 5_000_000)]
    required = ["sale_price", "sale_date", "total_livable_area", "number_of_bedrooms",
                "number_of_bathrooms", "interior_condition", "year_built", "zip_code",
                "census_tract", "shape"]
    df = df.dropna(subset=required)
    df = df[(df["total_livable_area"] > 0)
            & df["number_of_bedrooms"].between(1, 10)
            & df["number_of_bathrooms"].between(1, 10)
            & (df["year_built"] > 0)
            & (df["year_built"] <= df["sale_date"].dt.year)].copy()
    return df


def load_census(raw):
    def acs(name, keep, rename):
        t = pd.read_csv(os.path.join(raw, name), low_memory=False)[["GEO_ID"] + keep].rename(columns=rename)
        for c in rename.values():
            t[c] = pd.to_numeric(t[c], errors="coerce")
        return t

    income = acs("ACSDT5Y2024.B19013-Data.csv", ["B19013_001E"], {"B19013_001E": "median_household_income"})
    rent = acs("ACSDT5Y2024.B25064-Data.csv", ["B25064_001E"], {"B25064_001E": "median_gross_rent"})
    tenure = acs("ACSDT5Y2024.B25003-Data.csv", ["B25003_001E", "B25003_002E"],
                 {"B25003_001E": "occupied", "B25003_002E": "owner"})
    tenure["owner_occupied_pct"] = tenure["owner"] / tenure["occupied"] * 100
    census = income.merge(rent, on="GEO_ID").merge(tenure[["GEO_ID", "owner_occupied_pct"]], on="GEO_ID")
    census = census[census["GEO_ID"].astype(str).str.startswith("1400000US42101")].copy()
    census["GEOID"] = census["GEO_ID"].str.replace("1400000US", "", regex=False)
    return census


def build_homes(raw, philly):
    """Every single-family property, so the website can fill in a home's details from its address."""
    cols = ["parcel_number", "location", "unit", "zip_code", "category_code_description", "shape",
            "number_of_bedrooms", "number_of_bathrooms", "total_livable_area", "interior_condition",
            "year_built", "sale_date", "sale_price"]
    homes = pd.read_csv(os.path.join(raw, "opa_properties_public (1).csv"), usecols=cols, low_memory=False)
    homes = homes[homes["category_code_description"] == "SINGLE FAMILY"].dropna(subset=["shape", "location", "zip_code"])
    geo = gpd.GeoDataFrame(homes, geometry=homes["shape"].apply(lambda v: wkt.loads(str(v).split(";", 1)[1])),
                           crs="EPSG:2272")
    geo = gpd.sjoin(geo, philly[["GEOID", "geometry"]], how="inner", predicate="within")
    lonlat = geo.to_crs("EPSG:4326").geometry
    geo["lon"], geo["lat"] = lonlat.x.round(6), lonlat.y.round(6)

    homes = pd.DataFrame(geo.drop(columns=["geometry", "shape", "index_right", "category_code_description"]))
    homes["street"] = homes["location"].str.strip()
    unit = homes["unit"].fillna("").astype(str).str.strip()
    homes["address"] = homes["street"] + np.where(unit != "", " #" + unit, "")
    homes["zip_code"] = homes["zip_code"].astype(str).str[:5].astype(int)
    homes["sale_date"] = pd.to_datetime(homes["sale_date"], errors="coerce").dt.tz_localize(None).dt.date
    keep = ["parcel_number", "address", "street", "zip_code", "GEOID", "lat", "lon", "number_of_bedrooms",
            "number_of_bathrooms", "total_livable_area", "interior_condition", "year_built", "sale_date", "sale_price"]
    homes[keep].to_csv(os.path.join(OUT, "homes.csv.gz"), index=False, compression="gzip")
    print("Single-family homes for address search:", len(homes))


def build_tract_names(philly):
    """Give each census tract a neighborhood name (largest overlap) and its most common ZIP code."""
    hoods = gpd.read_file(NEIGHBORHOODS_URL).to_crs("EPSG:2272")[["LISTNAME", "geometry"]]
    pieces = gpd.overlay(philly[["GEOID", "geometry"]], hoods, how="intersection")
    pieces["area"] = pieces.geometry.area
    names = pieces.sort_values("area").groupby("GEOID")["LISTNAME"].last().rename("neighborhood")
    sales = pd.read_csv(os.path.join(OUT, "recent_sales.csv.gz"), dtype={"GEOID": str})
    zips = sales.groupby("GEOID")["zip_code"].agg(lambda z: z.mode().iloc[0]).rename("zip_code")
    table = pd.DataFrame({"GEOID": philly["GEOID"].values}).set_index("GEOID").join(names).join(zips).reset_index()
    table.to_csv(os.path.join(OUT, "tract_names.csv"), index=False)
    print("Tracts named:", table["neighborhood"].notna().sum(), "of", len(table))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True, help="folder with the 5 input CSVs listed in the notebook")
    args = parser.parse_args()
    os.makedirs(OUT, exist_ok=True)

    opa = load_opa(args.raw)
    census = load_census(args.raw)

    tracts = gpd.read_file(TRACT_URL)
    philly = tracts[tracts["COUNTYFP"] == "101"].to_crs("EPSG:2272")

    geo = gpd.GeoDataFrame(opa, geometry=opa["shape"].apply(lambda v: wkt.loads(str(v).split(";", 1)[1])),
                           crs="EPSG:2272")
    geo = gpd.sjoin(geo, philly[["GEOID", "geometry"]], how="left", predicate="within")
    geo = geo.merge(census[["GEOID", "median_household_income", "median_gross_rent", "owner_occupied_pct"]],
                    on="GEOID", how="left")
    geo = geo.dropna(subset=["median_household_income", "median_gross_rent", "owner_occupied_pct"])

    city_hall = gpd.GeoSeries([Point(-75.1636, 39.9526)], crs="EPSG:4326").to_crs("EPSG:2272").iloc[0]
    geo["distance_city_hall_miles"] = geo.geometry.distance(city_hall) / 5280
    lonlat = geo.to_crs("EPSG:4326").geometry
    geo["lon"], geo["lat"] = lonlat.x.round(6), lonlat.y.round(6)

    sales = pd.DataFrame(geo.drop(columns=["geometry", "shape", "index_right"]))
    sales["sale_date"] = sales["sale_date"].dt.tz_localize(None).dt.date
    group_size = sales.groupby(["sale_date", "sale_price"])["parcel_number"].transform("count")
    sales["multi_parcel_sale"] = group_size >= BULK_MIN_PARCELS
    print("Cleaned sales:", len(sales), "(notebook final rows: 107321)")
    print("Multi-parcel sales flagged:", int(sales["multi_parcel_sale"].sum()))

    keep = ["sale_date", "sale_price", "location", "zip_code", "GEOID", "total_livable_area",
            "number_of_bedrooms", "number_of_bathrooms", "interior_condition", "year_built",
            "distance_city_hall_miles", "lat", "lon", "multi_parcel_sale"]
    unit = sales["unit"].fillna("").astype(str).str.strip()
    sales["location"] = sales["location"].str.strip() + np.where(unit != "", " #" + unit, "")
    sales = sales[keep].rename(columns={"location": "address"})
    sales["zip_code"] = sales["zip_code"].astype(int)
    sales.to_csv(os.path.join(OUT, "recent_sales.csv.gz"), index=False, compression="gzip")

    market = sales[~sales["multi_parcel_sale"]].copy()
    market["price_per_sqft"] = market["sale_price"] / market["total_livable_area"]
    for key, name in [("GEOID", "tract_stats.csv"), ("zip_code", "zip_stats.csv")]:
        stats = (market.groupby(key)
                 .agg(sales=("sale_price", "size"),
                      median_price=("sale_price", "median"),
                      median_price_per_sqft=("price_per_sqft", "median"))
                 .reset_index())
        stats["median_price_per_sqft"] = stats["median_price_per_sqft"].round(0)
        stats.to_csv(os.path.join(OUT, name), index=False)

    build_homes(args.raw, philly)
    build_tract_names(philly)

    shapes = philly.to_crs("EPSG:4326")[["GEOID", "NAME", "geometry"]].copy()
    shapes["geometry"] = shapes.geometry.simplify(0.0002, preserve_topology=True)
    shapes.to_file(os.path.join(OUT, "philly_tracts.geojson"), driver="GeoJSON", COORDINATE_PRECISION=5)
    print("Wrote:", sorted(os.listdir(OUT)))


if __name__ == "__main__":
    main()
