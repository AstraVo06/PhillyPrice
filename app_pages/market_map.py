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
        view = st.segmented_control("Map view", ["3D city", "Flat map"], default="3D city",
                                    label_visibility="collapsed") or "3D city"
        st.markdown("**Show on the map**")
        metric = st.radio("Show on the map", list(ins.SALES_METRICS) + list(CENSUS_METRICS),
                          label_visibility="collapsed")
        is_sales = metric in ins.SALES_METRICS
        st.markdown("**Years of sales**")
        first_year, last_year = st.select_slider("Years of sales", options=list(range(2019, 2027)),
                                                 value=(2019, 2026), label_visibility="collapsed",
                                                 disabled=not is_sales)
        st.markdown("**Jump to a ZIP code**")
        centers = ins.zip_centers()
        zoom_zip = st.selectbox("Jump to a ZIP code", ["All of Philadelphia"] + [str(z) for z in centers.index],
                                label_visibility="collapsed")
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

center, zoom = {"lat": 40.0, "lon": -75.13}, 10.15
if zoom_zip != "All of Philadelphia":
    point = centers.loc[int(zoom_zip)]
    center, zoom = {"lat": float(point["lat"]), "lon": float(point["lon"])}, 12.6

BLUE_STOPS = np.array([[234, 240, 248], [169, 192, 224], [91, 130, 190], [27, 58, 107], [10, 24, 48]])


def ramp(t):
    """Blue color for a 0-1 value."""
    position = t * (len(BLUE_STOPS) - 1)
    i = min(int(position), len(BLUE_STOPS) - 2)
    mix = position - i
    return [int(v) for v in BLUE_STOPS[i] * (1 - mix) + BLUE_STOPS[i + 1] * mix] + [215]


low, high = shown["value"].quantile(0.05), shown["value"].quantile(0.95)
with map_col:
    what = metric.lower() if metric != "Number of sales" else "how many homes sold"
    st.markdown(f"""<div class="pp-howto"><span class="material-symbols-rounded">lightbulb</span><div>
<b>How to read this map.</b> Each shape is a small neighborhood area. Darker {"and taller " if view == "3D city" else ""}means
a higher {what}. Point at an area to see its neighborhood, ZIP code, and the number behind the color.
{"Use the years slider to compare different periods." if is_sales else ""}</div></div>""", unsafe_allow_html=True)
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
                             "elevation": 40 + t * 1700, "color": ramp(t)})
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
        st.pydeck_chart(deck, height=640)
        st.caption("Taller and darker means higher. Drag to move, scroll to zoom, and hold right-click "
                   "(or Ctrl) while dragging to tilt and spin the city.")
    else:
        fig = px.choropleth_map(
            shown, geojson=ins.load_tract_shapes(), locations="GEOID", featureidkey="properties.GEOID", color="value",
            color_continuous_scale=["#EAF0F8", "#A9C0E0", "#5B82BE", "#1B3A6B", "#0A1830"],
            range_color=(low, high), map_style="carto-positron", zoom=zoom, center=center, opacity=0.78,
            custom_data=["place", "value_text", "detail"],
        )
        fig.update_traces(hovertemplate=f"<b>%{{customdata[0]}}</b><br>{metric}: <b>%{{customdata[1]}}</b><br>%{{customdata[2]}}<extra></extra>")
        fig.update_layout(height=640, margin=dict(l=0, r=0, t=0, b=0),
                          coloraxis_colorbar=dict(title="", len=0.5, thickness=14, x=0.99, xanchor="right",
                                                  bgcolor="rgba(255,255,255,0.85)",
                                                  tickprefix="$" if unit == "$" else "",
                                                  ticksuffix="%" if unit == "%" else "", tickformat=",.0f"))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "scrollZoom": False})
    if is_sales:
        st.caption(f"Blank areas had fewer than {MIN_SALES} sales in the years picked. Sales where several homes "
                   "changed hands for one total price are left out.")

ui.section("Most and least expensive ZIP codes", "Typical single-family sale price, 2019–2026.")
zips = ins.load_zip_stats()
ranked = zips[zips["sales"] >= 100].sort_values("median_price")
left, right = st.columns(2, gap="large")
for col, title, rows, color in [(left, "Most expensive", ranked.tail(10).iloc[::-1], ui.BLUE),
                                (right, "Most affordable", ranked.head(10), ui.GOLD)]:
    bar = go.Figure(go.Bar(
        x=rows["median_price"], y=rows["zip_code"].astype(str), orientation="h", marker_color=color,
        text=rows["median_price"].map(money), textposition="outside", cliponaxis=False,
        hovertemplate="ZIP %{y}<br>%{text}<extra></extra>"))
    bar.update_layout(title=dict(text=title, x=0), height=430, margin=dict(l=0, r=80, t=40, b=0),
                      yaxis=dict(autorange="reversed", type="category"), xaxis=dict(visible=False),
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    col.plotly_chart(bar, use_container_width=True, config={"displayModeBar": False, "scrollZoom": False})

ui.footer()
