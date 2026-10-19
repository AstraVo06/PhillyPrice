"""PhillyPrice: Philadelphia home list price estimator (BUSA 310 Group Project 1)."""

import streamlit as st

from core import account, ui

st.set_page_config(page_title=f"{ui.APP_NAME} · Philadelphia home price estimator",
                   page_icon="🏠", layout="wide", initial_sidebar_state="collapsed")
ui.setup()

estimate = st.Page("app_pages/estimate.py", title="Estimate", default=True)
find_homes = st.Page("app_pages/find_homes.py", title="Find homes")
market_map = st.Page("app_pages/market_map.py", title="Market map")
price_trends = st.Page("app_pages/price_trends.py", title="Price trends")
how_it_works = st.Page("app_pages/how_it_works.py", title="How it works")
about = st.Page("app_pages/about.py", title="About")
saved = st.Page("app_pages/saved.py", title="Saved homes", url_path="saved")
privacy = st.Page("app_pages/privacy.py", title="Privacy", url_path="privacy")
terms = st.Page("app_pages/terms.py", title="Terms", url_path="terms")

current = st.navigation([estimate, find_homes, market_map, price_trends, how_it_works, about, saved, privacy, terms], position="hidden")

# Back from Google sign-in with a home the visitor wanted to save: open it and save it.
pending = account.take_pending()
if pending:
    st.session_state["entered"] = True
    st.session_state["search_request"] = pending
    st.session_state["save_after_search"] = True
    if current.title != "Estimate":
        st.switch_page(estimate)

# Intro screen the first time a visitor lands on the home page.
# It's skipped for shared links to a home (?q=...), so they open straight to the estimate.
if (not st.session_state.get("entered") and not account.signed_in() and current.title == "Estimate"
        and not st.query_params.get("q")):
    from core import insights as ins
    sales = ins.load_sales()
    if ui.splash(len(ins.load_homes()), len(sales), sales["sale_date"].max()):
        st.session_state["entered"] = True
        st.rerun()
    st.stop()
st.session_state["entered"] = True

ui.navbar(estimate, [find_homes, market_map, price_trends, how_it_works, about], saved)
current.run()
