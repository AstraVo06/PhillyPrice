import datetime

import requests
import streamlit as st

from core import account
from core import photos
from core import ui
from core.ui import money, money_short

ui.hero("Saved homes", "Homes you saved, with the estimate from the day you saved them.", compact=True)


def open_home(address):
    st.session_state["search_request"] = address


if not account.enabled():
    st.info("Saved homes aren't switched on for this site yet.", icon=":material/info:")
elif not account.signed_in():
    ui.section("Sign in to see your saved homes",
               "Save any home from its estimate page, then find it here on any device. "
               "We only use your Google name and email.")
    if st.button("Continue with Google", type="primary", key="saved_signin"):
        st.login()
else:
    try:
        homes = account.saved_homes(refresh=True)
    except requests.RequestException:
        homes = None
        st.error("We couldn't load your saved homes. Try again in a minute.", icon=":material/cloud_off:")
    if homes == []:
        ui.section("Nothing saved yet", "Look up a home and press Save on its estimate to keep it here.")
        st.page_link("app_pages/estimate.py", label="Look up a home", icon=":material/search:")
    elif homes:
        ui.section(f"{len(homes)} saved home{'s' if len(homes) != 1 else ''}")
        for start in range(0, len(homes), 3):
            cols = st.columns(3, gap="medium")
            for col, home in zip(cols, homes[start:start + 3]):
                saved_on = datetime.datetime.fromisoformat(home["saved_at"][:19])
                with col:
                    st.markdown(
                        f'<div class="pp-comp">{photos.picture_html(home["lat"], home["lon"], 160)}<div class="body">'
                        f'<div class="price">{money(home["estimate"])}</div>'
                        f'<div class="addr">{home["address"]}</div>'
                        f'<div class="sub">Likely range {money_short(home["low"])} – {money_short(home["high"])} · '
                        f'saved {saved_on:%b %d, %Y}</div>'
                        f'<div class="feat">{home["beds"]} bd · {home["baths"]} ba · {home["sqft"]:,} sq ft</div>'
                        '</div></div>', unsafe_allow_html=True)
                    c1, c2 = st.columns(2)
                    if c1.button("Today's estimate", key=f"open_{home['home_key']}", use_container_width=True,
                                 on_click=open_home, args=(home["address"],), type="primary"):
                        st.switch_page("app_pages/estimate.py")
                    if c2.button("Remove", key=f"remove_{home['home_key']}", use_container_width=True,
                                 icon=":material/delete:"):
                        account.remove_home(home["home_key"])
                        st.rerun()

ui.footer()
