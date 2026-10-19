import string

import plotly.graph_objects as go
import streamlit as st

from core import insights as ins
from core import photos
from core import ui
from core.ui import money, money_short

CONDITIONS = {1: "Brand new", 2: "Updated", 3: "Better than average", 4: "Average",
              5: "Needs some work", 6: "Needs major repairs", 7: "Not livable"}
PRICE_STEPS = [10_000, 50_000, 100_000, 150_000, 200_000, 250_000, 300_000, 400_000, 500_000,
               750_000, 1_000_000, 1_500_000, 2_000_000, 5_000_000]
SIZE_STEPS = [300, 600, 800, 1000, 1200, 1500, 2000, 2500, 3000, 4000, 10000]
PAGE = 12
SORTS = {"Newest first": ("sale_date", False), "Price: low to high": ("sale_price", True),
         "Price: high to low": ("sale_price", False), "Biggest first": ("total_livable_area", False)}

ui.hero("Find homes", "Browse Philadelphia homes that sold recently. Filter by price, size, bedrooms, and condition, "
        "then get an estimate for any of them.", compact=True)

sales = ins.market_sales()
filters, results = st.columns([1, 2.7], gap="medium")
with filters:
    with st.container(border=True):
        st.markdown("**ZIP codes**")
        zips = st.multiselect("ZIP codes", sorted(sales["zip_code"].unique()), placeholder="Any ZIP code",
                              label_visibility="collapsed")
        st.markdown("**Sale price**")
        low_price, high_price = st.select_slider("Sale price", PRICE_STEPS, value=(PRICE_STEPS[0], PRICE_STEPS[-1]),
                                                 format_func=money_short, label_visibility="collapsed")
        st.markdown("**Bedrooms**")
        beds = st.segmented_control("Bedrooms", ["Any", "1+", "2+", "3+", "4+", "5+"], default="Any",
                                    label_visibility="collapsed") or "Any"
        st.markdown("**Bathrooms**")
        baths = st.segmented_control("Bathrooms", ["Any", "1+", "2+", "3+"], default="Any",
                                     label_visibility="collapsed") or "Any"
        st.markdown("**Size (sq ft)**")
        low_size, high_size = st.select_slider("Size", SIZE_STEPS, value=(SIZE_STEPS[0], SIZE_STEPS[-1]),
                                               format_func=lambda v: f"{v:,}", label_visibility="collapsed")
        st.markdown("**Condition inside**")
        conditions = st.pills("Condition", list(CONDITIONS), format_func=lambda c: CONDITIONS[c],
                              selection_mode="multi", label_visibility="collapsed")
        st.markdown("**Sold between**")
        first_year, last_year = st.select_slider("Sold between", list(range(2019, 2027)), value=(2024, 2026),
                                                 label_visibility="collapsed")
        sort = st.selectbox("Sort by", list(SORTS))

found = sales[sales["sale_price"].between(low_price, high_price)
              & sales["total_livable_area"].between(low_size, high_size)
              & sales["year"].between(first_year, last_year)]
if zips:
    found = found[found["zip_code"].isin(zips)]
if beds != "Any":
    found = found[found["number_of_bedrooms"] >= int(beds[0])]
if baths != "Any":
    found = found[found["number_of_bathrooms"] >= int(baths[0])]
if conditions:
    found = found[found["interior_condition"].isin(conditions)]
column, ascending = SORTS[sort]
found = found.sort_values(column, ascending=ascending)

filter_key = (tuple(zips), low_price, high_price, beds, baths, low_size, high_size, tuple(conditions or []),
              first_year, last_year, sort)
if st.session_state.get("find_filters") != filter_key:
    st.session_state["find_filters"] = filter_key
    st.session_state["find_shown"] = PAGE

with results:
    if found.empty:
        st.info("No homes match these filters. Try a wider price range or fewer filters.", icon=":material/search_off:")
    else:
        st.markdown(f'<div class="pp-section-title" style="margin-top:0">{len(found):,} homes sold</div>'
                    f'<div class="pp-section-sub">Typical price {money(found["sale_price"].median())} · '
                    f'typical size {found["total_livable_area"].median():,.0f} sq ft</div>', unsafe_allow_html=True)
        on_map = found.head(3000)
        fig = go.Figure(go.Scattermap(
            lat=on_map["lat"], lon=on_map["lon"], mode="markers",
            marker=dict(size=8, color=on_map["sale_price"], opacity=0.85, cmin=found["sale_price"].quantile(0.05),
                        cmax=found["sale_price"].quantile(0.95), showscale=False,
                        colorscale=[[0, "#A9C0E0"], [0.5, "#3F6AAE"], [1, ui.DEEP]]),
            text=[f"{string.capwords(a.lower())}<br>{money(p)} · {d:%b %Y}" for a, p, d in
                  zip(on_map["address"], on_map["sale_price"], on_map["sale_date"])],
            hoverinfo="text"))
        fig.update_layout(map=dict(style="carto-positron", zoom=10.4 if not zips else 12.4,
                                   center=dict(lat=float(on_map["lat"].median()), lon=float(on_map["lon"].median()))),
                          margin=dict(l=0, r=0, t=0, b=0), height=360)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "scrollZoom": False})
        if len(found) > len(on_map):
            st.caption(f"The map shows the first {len(on_map):,} homes in this order.")

        # Look a little further down the list and show homes that have a street photo first.
        wanted = st.session_state["find_shown"]
        pool = found.head(wanted * 3).copy()
        with st.spinner("Loading home photos…"):
            pool["has_photo"] = photos.has_photos(list(zip(pool["lat"], pool["lon"])))
        shown = pool.sort_values("has_photo", ascending=False, kind="stable").head(wanted)
        for start in range(0, len(shown), 3):
            cols = st.columns(3)
            for col, home in zip(cols, shown.iloc[start:start + 3].itertuples()):
                with col:
                    st.markdown(
                        f'<div class="pp-comp">{photos.picture_html(home.lat, home.lon, 150)}'
                        f'<div class="top">Sold {money(home.sale_price)}</div><div class="body">'
                        f'<div class="addr">{string.capwords(home.address.lower())}</div>'
                        f'<div class="sub">{home.sale_date:%b %Y} · ZIP {home.zip_code}</div>'
                        f'<div class="feat">{home.number_of_bedrooms:.0f} bd · {home.number_of_bathrooms:.0f} ba · '
                        f'{home.total_livable_area:,.0f} sq ft · built {home.year_built:.0f}</div></div></div>',
                        unsafe_allow_html=True)
                    if st.button("Estimate this home", key=f"estimate_{home.Index}", icon=":material/sell:",
                                 use_container_width=True):
                        st.session_state["search_request"] = f"{string.capwords(home.address.lower())}, Philadelphia, PA {home.zip_code}"
                        st.switch_page("app_pages/estimate.py")
        if len(found) > len(shown):
            if st.button(f"Show more homes ({len(found) - len(shown):,} left)", use_container_width=True):
                st.session_state["find_shown"] += PAGE
                st.rerun()

ui.footer()
