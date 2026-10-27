import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
import streamlit as st

from core import insights as ins
from core import model_backend as mb
from core import ui
from core.ui import money

MIN_SALES = 10
MAP_HEIGHT = 640
CENSUS_METRICS = {
    "Typical household income": ("median_household_income", "$"),
    "Typical rent": ("median_gross_rent", "$"),
    "Homeownership rate": ("owner_occupied_pct", "%"),
}

ui.hero("Market map", "See which Philadelphia neighborhoods cost the most, and how incomes and rents compare.",
        compact=True)

panel, map_col = st.columns([1, 2.7], gap="medium")
with panel:
    with st.container(border=True):
        view = st.segmented_control("Map view", ["Flat map", "3D city"], default="Flat map", required=True,
                                    label_visibility="collapsed") or "Flat map"
        st.markdown("**Show on the map**")
        metric = st.radio("Show on the map", list(ins.SALES_METRICS) + list(CENSUS_METRICS),
                          label_visibility="collapsed")
        is_sales = metric in ins.SALES_METRICS
        if is_sales:
            st.markdown("**Years of sales**")
            first_year, last_year = st.select_slider("Years of sales", options=list(range(2019, 2027)),
                                                     value=(2019, 2026), label_visibility="collapsed")
        else:
            first_year, last_year = 2019, 2026
            st.caption("Income, rent, and homeownership come from the Census Bureau's 2020–2024 survey, so there "
                       "are no years to pick. Choose a sales measure to compare years.")
        st.markdown("**Jump to an area**")
        centers = ins.zip_centers()
        zoom_zip = st.selectbox("Jump to an area", ["All of Philadelphia"] + [str(z) for z in centers.index],
                                label_visibility="collapsed", format_func=ins.zip_label)
        st.caption("Data: city sales records for single-family homes, and the Census Bureau's 2024 "
                   "American Community Survey for income, rent, and homeownership.")

if is_sales:
    shown = ins.tract_sales_metric(metric, first_year, last_year)
    shown = shown[shown["sales"] >= MIN_SALES].copy()
else:
    column, _ = CENSUS_METRICS[metric]
    shown = mb.tract_lookup[["GEOID", column]].rename(columns={column: "value"}).copy()
    shown["sales"] = None

unit = "count" if metric == "Number of sales" else ("%" if metric == "Homeownership rate" else "$")
fmt = {"$": lambda v: money(v), "%": lambda v: f"{v:.0f}%", "count": lambda v: f"{v:,.0f}"}[unit]
shown["place"] = shown["GEOID"].map(ins.tract_label)
shown["value_text"] = shown["value"].map(fmt)
period = f"{first_year}" if first_year == last_year else f"{first_year}–{last_year}"
if is_sales:
    shown["detail"] = shown["sales"].map(lambda n: f"Based on {int(n):,} sales, {period}")
else:
    shown["detail"] = "Census Bureau, 2020–2024 average"

# The area picked in the panel is shown in color; the rest of the city fades to gray.
selected = None if zoom_zip == "All of Philadelphia" else zoom_zip
shown["zip"] = shown["GEOID"].map(ins.load_tract_names()["zip_code"])
shown["in_area"] = True if selected is None else shown["zip"] == selected
center, zoom = {"lat": 40.0, "lon": -75.13}, 10.15
if selected:
    point = centers.loc[int(selected)]
    center, zoom = {"lat": float(point["lat"]), "lon": float(point["lon"])}, 12.4

BLUE_STOPS = np.array([[234, 240, 248], [169, 192, 224], [91, 130, 190], [27, 58, 107], [10, 24, 48]])


def ramp(t):
    """Blue color for a 0-1 value."""
    position = t * (len(BLUE_STOPS) - 1)
    i = min(int(position), len(BLUE_STOPS) - 2)
    mix = position - i
    return [int(v) for v in BLUE_STOPS[i] * (1 - mix) + BLUE_STOPS[i + 1] * mix] + [215]


def area_summary(zip_code):
    """Headline numbers for one ZIP code: sales measures for the years picked, census measures, and price rank."""
    sales = ins.market_sales()
    sales = sales[sales["year"].between(first_year, last_year)]
    here = sales[sales["zip_code"] == int(zip_code)]
    by_zip = sales.groupby("zip_code")["sale_price"].agg(["median", "size"])
    by_zip = by_zip[by_zip["size"] >= 30].sort_values("median", ascending=False)
    rank = list(by_zip.index).index(int(zip_code)) + 1 if int(zip_code) in by_zip.index else None
    tracts = ins.load_tract_names()
    geoids = tracts.index[tracts["zip_code"] == str(zip_code)]
    census = mb.tract_lookup[mb.tract_lookup["GEOID"].isin(geoids)]
    cards = [
        (money(here["sale_price"].median()) if len(here) else "n/a",
         f"Typical sale price, {period}" + (f" · #{rank} of {len(by_zip)} areas" if rank else "")),
        (f"${here['price_per_sqft'].median():,.0f}" if len(here) else "n/a", "Price per square foot"),
        (f"{len(here):,}", f"Single-family sales, {period}"),
        (money(census["median_household_income"].median()), "Typical household income"),
        (f"{money(census['median_gross_rent'].median())}/mo", "Typical rent"),
        (f"{census['owner_occupied_pct'].median():.0f}%", "Homes lived in by their owners"),
    ]
    return cards


low, high = shown["value"].quantile(0.05), shown["value"].quantile(0.95)
with map_col:
    what = metric.lower() if metric != "Number of sales" else "how many homes sold"
    st.markdown(f"""<div class="pp-howto"><span class="material-symbols-rounded">lightbulb</span><div>
<b>How to read this map.</b> Each shape is a small neighborhood area. Darker {"and taller " if view == "3D city" else ""}means
a higher {what}. {"Click or point at" if view == "Flat map" else "Point at"} an area to see its neighborhood, ZIP code,
and the number behind the color. Pick an area on the left to highlight it.
{"Use the years slider to compare different periods." if is_sales else ""}</div></div>""", unsafe_allow_html=True)
    if selected:
        st.markdown(f"**{ins.zip_label(selected)}**")
        ui.stat_cards(area_summary(selected), columns=3)
    if view == "3D city":
        values = shown.set_index("GEOID")
        rows = []
        for feature in ins.load_tract_shapes()["features"]:
            geoid = feature["properties"]["GEOID"]
            if geoid not in values.index:
                continue
            item = values.loc[geoid]
            t = float(np.clip((item["value"] - low) / (high - low), 0, 1)) if high > low else 0.5
            geometry = feature["geometry"]
            polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
            for polygon in polygons:
                rows.append({"polygon": polygon[0], "place": item["place"], "value_text": item["value_text"],
                             "detail": item["detail"],
                             "elevation": 40 + t * 1700 if item["in_area"] else 30,
                             "color": ramp(t) if item["in_area"] else [205, 210, 218, 110]})
        layer = pdk.Layer("PolygonLayer", rows, get_polygon="polygon", extruded=True, get_elevation="elevation",
                          get_fill_color="color", get_line_color=[255, 255, 255, 90], line_width_min_pixels=0.5,
                          pickable=True, auto_highlight=True, highlight_color=[242, 178, 51, 235])
        deck = pdk.Deck(
            layers=[layer], map_provider="carto", map_style="light",
            initial_view_state=pdk.ViewState(latitude=center["lat"] + (0.012 if zoom < 11 else 0.002),
                                             longitude=center["lon"], zoom=zoom + 0.25,
                                             pitch=52, bearing=-18),
            tooltip={"html": f"<b>{{place}}</b><br/>{metric}: <b>{{value_text}}</b><br/><span style='opacity:.75'>{{detail}}</span>",
                     "style": {"backgroundColor": ui.DEEP, "color": "white", "fontFamily": "Public Sans",
                               "borderRadius": "10px", "padding": "8px 12px"}},
        )
        st.pydeck_chart(deck, height=MAP_HEIGHT)
        st.caption("Taller and darker means higher. Drag to move, scroll to zoom, and hold right-click "
                   "(or Ctrl) while dragging to tilt and spin the city.")
    else:
        colored, faded = shown[shown["in_area"]], shown[~shown["in_area"]]
        fig = px.choropleth_map(
            colored, geojson=ins.load_tract_shapes(), locations="GEOID", featureidkey="properties.GEOID",
            color="value", color_continuous_scale=["#EAF0F8", "#A9C0E0", "#5B82BE", "#1B3A6B", "#0A1830"],
            range_color=(low, high), map_style="carto-positron", zoom=zoom, center=center, opacity=0.8,
            custom_data=["place", "value_text", "detail"],
        )
        fig.update_traces(hovertemplate=f"<b>%{{customdata[0]}}</b><br>{metric}: <b>%{{customdata[1]}}</b><br>%{{customdata[2]}}<extra></extra>")
        if len(faded):
            fig.add_trace(go.Choroplethmap(
                geojson=ins.load_tract_shapes(), locations=faded["GEOID"], featureidkey="properties.GEOID",
                z=[0] * len(faded), colorscale=[[0, "#CDD2DA"], [1, "#CDD2DA"]], showscale=False,
                marker=dict(opacity=0.45, line=dict(width=0.3, color="#ffffff")),
                customdata=faded[["place", "value_text", "detail"]].values,
                hovertemplate=f"<b>%{{customdata[0]}}</b><br>{metric}: <b>%{{customdata[1]}}</b><br>%{{customdata[2]}}<extra></extra>"))
        fig.update_layout(height=MAP_HEIGHT, margin=dict(l=0, r=0, t=0, b=0),
                          hoverlabel=dict(bgcolor=ui.DEEP, font=dict(color="white", family="Public Sans")),
                          coloraxis_colorbar=dict(title="", orientation="h", len=0.7, thickness=10, x=0.5,
                                                  xanchor="center", y=0.03, yanchor="bottom", ypad=6, xpad=10,
                                                  tickfont=dict(size=11, color=ui.INK),
                                                  bgcolor="rgba(255,255,255,0.85)",
                                                  tickprefix="$" if unit == "$" else "", nticks=4,
                                                  ticksuffix="%" if unit == "%" else "",
                                                  tickformat="~s" if unit == "$" else ",.0f"))
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False, "scrollZoom": False})
    if is_sales:
        st.caption(f"Blank areas had fewer than {MIN_SALES} sales in the years picked. Sales where several homes "
                   "changed hands for one total price are left out.")

ui.section("Most and least expensive areas", "Typical single-family sale price by ZIP code, 2019–2026. "
           "Each ZIP is named for its main neighborhoods.")
zips = ins.load_zip_stats()
ranked = zips[zips["sales"] >= 100].sort_values("median_price")


def short_zip_label(zip_code):
    """Main neighborhood only, so the names fit beside the bars on a phone: 'Washington Square West · 19107'."""
    name, _, code = ins.zip_label(zip_code).rpartition(" · ")
    return f"{name.split(' & ')[0]} · {code}" if name else code
left, right = st.columns(2, gap="large")
for col, title, rows, color in [(left, "Most expensive", ranked.tail(10).iloc[::-1], ui.BLUE),
                                (right, "Most affordable", ranked.head(10), ui.GOLD)]:
    bar = go.Figure(go.Bar(
        x=rows["median_price"], y=rows["zip_code"].map(short_zip_label), orientation="h", marker_color=color,
        text=rows["median_price"].map(money), textposition="outside", cliponaxis=False,
        hovertemplate="%{y}<br>%{text}<extra></extra>"))
    bar.update_layout(title=dict(text=title, x=0), height=430, margin=dict(l=0, r=80, t=40, b=0),
                      yaxis=dict(autorange="reversed", type="category", automargin=True), xaxis=dict(visible=False),
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    col.plotly_chart(bar, width="stretch", config={"displayModeBar": False, "scrollZoom": False})

ui.footer()
