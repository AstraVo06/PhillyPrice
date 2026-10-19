"""PhillyPrice: Philadelphia home list price estimator (BUSA 310 Group Project 1)."""

import streamlit as st

from core import ui

st.set_page_config(page_title=f"{ui.APP_NAME} · Philadelphia home price estimator",
                   page_icon="🏠", layout="wide", initial_sidebar_state="collapsed")
ui.setup()

estimate = st.Page("app_pages/estimate.py", title="Estimate", default=True)
find_homes = st.Page("app_pages/find_homes.py", title="Find homes")
market_map = st.Page("app_pages/market_map.py", title="Market map")
price_trends = st.Page("app_pages/price_trends.py", title="Price trends")
how_it_works = st.Page("app_pages/how_it_works.py", title="How it works")
about = st.Page("app_pages/about.py", title="About")

current = st.navigation([estimate, find_homes, market_map, price_trends, how_it_works, about], position="hidden")

# Intro screen the first time a visitor lands on the home page.
if not st.session_state.get("entered") and current.title == "Estimate":
    from core import insights as ins
    if ui.splash(len(ins.load_homes())):
        st.session_state["entered"] = True
        st.rerun()
    st.stop()
st.session_state["entered"] = True

ui.navbar(estimate, [find_homes, market_map, price_trends, how_it_works, about])
current.run()
