import plotly.graph_objects as go
import streamlit as st

from core import insights as ins
from core import ui
from core.ui import money, money_short

ui.hero("Insights for agents", "What our model learned from 107,321 Philadelphia home sales, and what it means "
        "when you price a listing.", compact=True)

drivers, by_input = ins.price_drivers()
ranking = ins.neighborhood_ranking()
gaps = ins.price_gaps()
PLOT = dict(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
CONFIG = {"displayModeBar": False, "scrollZoom": False}


def caption(text):
    """st.caption without Streamlit reading text between two $ signs as math."""
    st.caption(text.replace("$", "\\$"))


def bars(labels, values, text, color=ui.BLUE, height=None, highlight=None):
    """Horizontal bar chart, largest at the top."""
    colors = [ui.GOLD if highlight and label in highlight else color for label in labels]
    fig = go.Figure(go.Bar(x=values, y=labels, orientation="h", marker_color=colors, text=text,
                           textposition="outside", cliponaxis=False, hoverinfo="skip"))
    fig.update_layout(height=height or 46 * len(labels) + 30, margin=dict(l=0, r=90, t=6, b=6),
                      yaxis=dict(autorange="reversed", tickfont=dict(size=14)), xaxis=dict(visible=False), **PLOT)
    st.plotly_chart(fig, width="stretch", config=CONFIG)


# --------------------------------------------------
# 1. What drives prices
# --------------------------------------------------
location, size = drivers["Location"], drivers["Size (living area)"]
ui.section("1. Which features drive prices?",
           f"Location adds up to {location:.0f}% of the model's decisions and size to {size:.0f}%. "
           "Together they explain most of what a home is worth.", anchor="drivers")
left, right = st.columns([1.15, 1], gap="large")
with left:
    bars(list(drivers.index), list(drivers.values), [f"{v:.0f}%" for v in drivers.values],
         highlight={"Location", "Size (living area)"})
    with st.expander("See every model input"):
        bars(list(by_input.index), list(by_input.values), [f"{v:.1f}%" for v in by_input.values], height=520)
        caption("Share of the Random Forest's splits, weighted by how much each one improved the prediction "
                   "(feature importance). Location combines distance from City Hall, ZIP code, and the census "
                   "tract's income, rent, and share of owners. Market timing combines the mortgage rate, month, "
                   "and year of sale.")
with right:
    ui.checklist([
        f"<b>Location comes first.</b> Distance from City Hall alone is {by_input['Distance from City Hall']:.0f}% "
        "of the model, more than any single feature except size.",
        f"<b>Square footage is the biggest single feature</b> ({size:.0f}%). Quote price per square foot "
        "with the neighborhood, not one city-wide number.",
        f"<b>Bedroom count barely matters</b> ({by_input['Bedrooms']:.1f}%) once size is known. A fourth "
        "bedroom carved out of the same space doesn't raise the price; bathrooms "
        f"({by_input['Bathrooms']:.0f}%) do more.",
        f"<b>Timing matters</b> ({drivers['Market timing']:.0f}%): mortgage rates and the season move "
        "what buyers pay for the same home.",
    ])

# --------------------------------------------------
# 2. Most expensive neighborhoods
# --------------------------------------------------
top, bottom = ranking.head(10), ranking.tail(10).iloc[::-1]
ui.section("2. Which neighborhoods are most expensive?",
           f"Typical sale price, 2024–2026, for neighborhoods with at least 40 single-family sales. "
           f"The typical Philadelphia home sold for {money(gaps['city_median'])} "
           f"({money(gaps['city_ppsf'])} per sq ft).", anchor="neighborhoods")
left, right = st.columns(2, gap="large")
with left:
    st.markdown("**Most expensive**")
    bars(list(top.index), list(top["median_price"]),
         [f"{money_short(p)} · ${f:,.0f}/sq ft" for p, f in zip(top["median_price"], top["price_per_sqft"])])
with right:
    st.markdown("**Most affordable**")
    bars(list(bottom.index), list(bottom["median_price"]),
         [f"{money_short(p)} · ${f:,.0f}/sq ft" for p, f in zip(bottom["median_price"], bottom["price_per_sqft"])],
         color=ui.GOLD)
leader = top.iloc[0]
by_ppsf = ranking.sort_values("price_per_sqft", ascending=False).index[0]
st.markdown(f"The priciest neighborhood, **{top.index[0]}**, is about "
            f"**{leader['median_price'] / gaps['city_median']:.1f}×** the city's typical home. By price per square "
            f"foot the top spot is **{by_ppsf}**: homes in big-lot areas like Chestnut Hill cost a lot mainly because "
            "they're large. See every area on the **Market map**.")
st.page_link("app_pages/market_map.py", label="Open the market map", icon=":material/map:")

# --------------------------------------------------
# 3. What causes price differences
# --------------------------------------------------
ui.section("3. What factors cause price differences?",
           "The same home can be worth very different amounts depending on where it is, the neighborhood "
           "around it, and its condition. Typical sale prices, 2024–2026.", anchor="differences")
distance, income, condition, yearly = gaps["distance"], gaps["income"], gaps["condition"], gaps["yearly"]
c1, c2 = st.columns(2, gap="large")
with c1:
    st.markdown("**Distance from City Hall**")
    bars(list(distance.index), list(distance.values), [money_short(v) for v in distance.values])
    caption(f"Homes within 2 miles sell for {money_short(distance.iloc[0])}, then prices drop to about "
               f"{money_short(distance.min())} and climb again past 9 miles ({money_short(distance.iloc[-1])}), "
               "where the Northeast and Chestnut Hill have bigger homes.")
with c2:
    st.markdown("**Neighborhood household income**")
    bars(list(income.index), list(income.values), [money_short(v) for v in income.values])
    caption(f"Homes in the highest-income quarter of neighborhoods sell for "
               f"{income.iloc[-1] / income.iloc[0]:.1f}× those in the lowest-income quarter.")
c3, c4 = st.columns(2, gap="large")
with c3:
    st.markdown("**Condition inside (price per square foot)**")
    bars(list(condition.index), list(condition.values), [f"${v:,.0f}" for v in condition.values])
    caption(f"Renovated and new homes sell for about ${condition.get('Updated', 0):,.0f}–"
               f"${condition.get('New', 0):,.0f} per sq ft versus ${condition.get('Average', 0):,.0f} for "
               "average condition. The city's condition codes are rough, so the model gives condition little "
               "weight: adjust for a recent renovation yourself.")
with c4:
    st.markdown("**Timing: typical sale price by year**")
    fig = go.Figure(go.Bar(x=[str(y) for y in yearly.index], y=yearly.values, marker_color=ui.BLUE,
                           text=[money_short(v) for v in yearly.values], textposition="outside",
                           cliponaxis=False, hoverinfo="skip"))
    fig.update_layout(height=300, margin=dict(l=0, r=0, t=20, b=0), yaxis=dict(visible=False), **PLOT)
    st.plotly_chart(fig, width="stretch", config=CONFIG)
    peak = yearly.loc[2019:2025]
    caption(f"The typical sale rose from {money_short(yearly.iloc[0])} in 2019 to {money_short(peak.max())} "
               f"(+{(peak.max() / yearly.iloc[0] - 1) * 100:.0f}%) and has been flat since mortgage rates rose.")

# --------------------------------------------------
# What it means for agents
# --------------------------------------------------
ui.section("What this means when you price a listing")
ui.cards([
    ("location_on", "Start from location", "Pull comps from the same blocks. A mile can change the price more "
     "than a bedroom."),
    ("square_foot", "Price the square footage", "Compare price per square foot within the neighborhood, and "
     "don't sell bedroom count on its own."),
    ("handyman", "Adjust for condition", "The model can't see a new kitchen. Add for a recent renovation and "
     "subtract for work needed."),
    ("swap_vert", "Show a range", "Quote where 8 in 10 similar homes sold, then use nearby sales to pick "
     "the spot in that range."),
])
caption("These are patterns in past sales, not proof of cause. On sales it hadn't seen (2025–26), the model "
           "explained about 41% of price differences and missed by $104,456 on average. Full details on "
           "How it works.")
ui.footer()
