import datetime
import string

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
import streamlit.components.v1 as components

from core import account
from core import insights as ins
from core import photos
from core import ui
from core.ui import money, money_short

# Friendly names for the city's interior condition codes, from worst to best.
CONDITION_CHOICES = {
    7: "Not livable",
    6: "Needs major repairs",
    5: "Needs some work",
    4: "Average",
    3: "Better than average",
    2: "Updated or renovated",
    1: "Brand new",
}
EXAMPLE_ADDRESS = "2618 Jasper St, Philadelphia, PA 19125"
PICK_PAGE = 12
DETAIL_DEFAULTS = {"beds": 3, "baths": 1, "sqft": 1200, "year": 1925, "condition": 4}

# Each search is kept in the address bar as ?q=..., so the browser's Back and Forward buttons step
# through searches. Another page can also start one with "search_request" or the q parameter.
if "search_request" in st.session_state:
    st.session_state["query"] = st.session_state.pop("search_request")
    st.session_state["pending_search"] = True
elif st.query_params.get("q") != st.session_state.get("shown_q"):
    url_query = st.query_params.get("q")
    if url_query:
        st.session_state["query"] = url_query
        st.session_state["pending_search"] = True
    else:
        for key in ["result", "home", "matches", "typed_address", "streets", "lookup", "shown_q"]:
            st.session_state.pop(key, None)
        st.session_state["query"] = ""


def nice_address(address, zip_code=None):
    text = string.capwords(address.lower())
    return f"{text}, Philadelphia, PA {zip_code}" if zip_code else text


def fill_example():
    st.session_state["query"] = EXAMPLE_ADDRESS
    st.session_state["pending_search"] = True


@st.cache_data(show_spinner=False, ttl=3600)
def estimate_known_home(home, sqft, beds, baths, condition, year):
    return ins.estimate_home(home, sqft, beds, baths, condition, year)


@st.cache_data(show_spinner=False, ttl=3600)
def estimate_typed_address(address, sqft, beds, baths, condition, year):
    return ins.estimate(address, sqft, beds, baths, condition, year)


def details_now():
    return {k: int(st.session_state.get(k, v) or v) for k, v in DETAIL_DEFAULTS.items()}


def run_estimate():
    d = details_now()
    try:
        with st.spinner("Working out a price…"):
            if st.session_state.get("home"):
                result = estimate_known_home(st.session_state["home"], d["sqft"], d["beds"], d["baths"],
                                             d["condition"], d["year"])
            else:
                result = estimate_typed_address(st.session_state["typed_address"], d["sqft"], d["beds"],
                                                d["baths"], d["condition"], d["year"])
        st.session_state["result"] = result
        st.session_state["used_details"] = d
    except ValueError as error:
        st.session_state.pop("result", None)
        message = str(error)
        if "could not be found" in message:
            message = "We couldn't find that address. Check the house number and street name, and add the ZIP code."
        st.error(message, icon=":material/error:")
    except requests.RequestException:
        st.session_state.pop("result", None)
        st.error("The address lookup service didn't answer. Try again in a minute.", icon=":material/wifi_off:")


def select_home(home):
    st.session_state["home"] = home
    st.session_state["lookup"] = "found"
    for key, value in ins.home_details(home).items():
        st.session_state[key] = value
    run_estimate()


def note(message, kind="info"):
    """A short message that stays readable on top of the hero photo."""
    st.markdown(f'<div class="pp-note {kind}">{message}</div>', unsafe_allow_html=True)


def run_search(query):
    query = query.strip()
    for key in ["result", "home", "matches", "typed_address", "streets", "pick_filter", "ask_signin"]:
        st.session_state.pop(key, None)
    if not query:
        st.session_state["lookup"] = None
        note("Type a street address, like <b>2618 Jasper St</b>, or just a street name, like <b>Jasper St</b>.")
        return
    st.session_state["shown_q"] = query
    if st.query_params.get("q") != query:
        st.query_params["q"] = query
    with st.spinner("Looking up the home…"):
        matches = ins.find_homes(query)
        if matches.empty:
            streets, matches = ins.suggest_homes(query)
            st.session_state["streets"] = streets
    st.session_state["typed_address"] = query
    exact = matches[matches["gap"] == 0] if "gap" in matches else matches.iloc[0:0]
    if len(exact) == 1:
        select_home(exact.iloc[0].to_dict())
    elif st.session_state.get("streets"):
        st.session_state["lookup"] = "pick"
        st.session_state["matches"] = matches.to_dict("records")
    elif len(matches) == 1:
        select_home(matches.iloc[0].to_dict())
    elif len(matches) > 1:
        st.session_state["lookup"] = "units"
        st.session_state["matches"] = matches.to_dict("records")
    else:
        enter_details_myself()


def enter_details_myself():
    st.session_state["lookup"] = "notfound"
    st.session_state.pop("result", None)
    for key, value in DETAIL_DEFAULTS.items():
        st.session_state[key] = value


def open_comp(address, zip_code):
    """Clicking a nearby sale estimates that home instead."""
    st.session_state["query"] = nice_address(address, zip_code)
    st.session_state["pending_search"] = True
    st.session_state["scroll_to_price"] = True


def home_cards(rows, records, prefix):
    """Clickable cards, four to a row. `records` holds the full home dicts by the rows' index."""
    for row_start in range(0, len(rows), 4):
        cols = st.columns(4, gap="small")
        for col, (i, m) in zip(cols, rows.iloc[row_start:row_start + 4].iterrows()):
            has_sale = m["sale_price"] >= 1000 and pd.notna(m["sale_date"])
            sold = f"Sold {money(m['sale_price'])}" if has_sale else "No recent sale on record"
            when = f"{m['sale_date']:%b %Y} · " if has_sale else ""
            zip_text = f"ZIP {m['zip_code']:.0f}"
            beds = f"{m['number_of_bedrooms']:.0f} bd · " if m["number_of_bedrooms"] >= 1 else ""
            baths = f"{m['number_of_bathrooms']:.0f} ba · " if m["number_of_bathrooms"] >= 1 else ""
            size = f"{m['total_livable_area']:,.0f} sq ft" if m["total_livable_area"] > 0 else "size unknown"
            place = ins.tract_label(m["GEOID"]).split(" · ")[0] if isinstance(m["GEOID"], str) else ""
            with col, st.container(key=f"compcard_{prefix}_{i}"):
                st.markdown(
                    f'<div class="pp-comp">{photos.picture_html(m["lat"], m["lon"], 150)}<div class="body">'
                    f'<div class="price">{sold}</div>'
                    f'<div class="addr">{nice_address(m["address"])}</div>'
                    f'<div class="sub">{when}{place or zip_text}</div>'
                    f'<div class="feat">{beds}{baths}{size}</div></div></div>', unsafe_allow_html=True)
                st.button(f"Estimate {nice_address(m['address'])}", key=f"{prefix}_open_{i}", on_click=pick_home,
                          args=(records[i],))


def saved_record(result, home, title, d):
    location = result["location"]
    key = home["parcel_number"] if home else "addr:" + title.lower()
    return {"home_key": key, "address": title, "lat": location["latitude"], "lon": location["longitude"],
            "estimate": round(result["price"]), "low": round(result["low"]), "high": round(result["high"]),
            "beds": d["beds"], "baths": d["baths"], "sqft": d["sqft"]}


def save_button(result, home, title, d):
    """Heart button: saves the home for signed-in visitors, or asks them to sign in first."""
    record = saved_record(result, home, title, d)
    try:
        if st.session_state.pop("save_after_search", False) and account.signed_in():
            account.save_home(record)
            st.toast("Saved to your homes", icon=":material/favorite:")
        already = account.signed_in() and account.is_saved(record["home_key"])
    except requests.RequestException:
        st.toast("Saved homes are unavailable right now. Try again in a minute.", icon=":material/cloud_off:")
        return
    if already:
        if st.button("Saved to your homes", icon=":material/favorite:", width="stretch", key="unsave_home",
                     help="Click to remove it from your saved homes"):
            account.remove_home(record["home_key"])
            st.rerun()
    elif st.button("Save this home", icon=":material/favorite_border:", width="stretch", key="save_home"):
        if account.signed_in():
            account.save_home(record)
            st.toast("Saved to your homes", icon=":material/favorite:")
            st.rerun()
        else:
            st.session_state["ask_signin"] = True
            st.rerun()


def signin_prompt(home, title):
    if not st.session_state.get("ask_signin") or account.signed_in():
        return
    with st.container(key="signin_card"):
        st.markdown("**Sign in to save this home.** Your saved homes stay in your account, so you can come back "
                    "to them on any device. We only use your Google name and email.")
        if home:
            account.remember_pending(title)
        c1, c2 = st.columns([1, 3], vertical_alignment="center")
        if c1.button("Continue with Google", type="primary", key="google_signin"):
            st.login()
        if c2.button("Not now", type="tertiary", key="signin_later"):
            st.session_state.pop("ask_signin", None)
            st.rerun()


def pick_home(home):
    """Clicking a home card searches its exact address, so it gets its own step in the browser history."""
    st.session_state["query"] = nice_address(home["address"], f"{home['zip_code']:.0f}")
    st.session_state["pending_search"] = True
    st.session_state["scroll_to_price"] = True


def counter_html(start, end, base, pct, zip_code, sales_count):
    """Animated what-if price, change versus the estimate, and where the price sits in the ZIP code."""
    delta = end - base
    if abs(delta) < 500:
        delta_text, delta_color = "Same as your estimate", "#C9D4E8"
    else:
        delta_text = f"{'+' if delta > 0 else '−'}${abs(delta):,.0f} vs. your estimate"
        delta_color = "#7EE2AE" if delta > 0 else "#FFA594"
    pct_block = ""
    if pct is not None:
        pct_block = (f'<div class="lbl" style="margin-top:22px">Compared with ZIP {zip_code}</div>'
                     '<div class="track"><div class="dot" id="dot"></div></div>'
                     f'<div class="cap">Higher than <b id="pct">0</b>% of the {sales_count:,} homes sold there since 2024</div>')
    return f"""
<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..900&family=Public+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
body {{ margin: 0; font-family: 'Public Sans', sans-serif; }}
.box {{ background: {ui.DEEP}; border-radius: 20px; padding: 22px 26px; color: #fff; }}
.lbl {{ font-size: 12px; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; color: {ui.GOLD}; }}
.num {{ font-family: 'Archivo', sans-serif; font-stretch: 112%; font-weight: 800; letter-spacing: -0.04em; font-size: 54px; line-height: 1.05; margin: 6px 0 4px; }}
.delta {{ font-weight: 700; font-size: 15px; }}
.track {{ position: relative; height: 10px; border-radius: 99px; background: linear-gradient(90deg, #A9C0E0, {ui.GOLD}); margin: 14px 0 10px; }}
.dot {{ position: absolute; top: 50%; left: 0; width: 20px; height: 20px; border-radius: 50%; background: #fff;
        border: 3px solid {ui.GOLD}; transform: translate(-50%, -50%); transition: left .9s cubic-bezier(.2,.7,.2,1); }}
.cap {{ font-size: 14px; color: #C9D4E8; }} .cap b {{ color: #fff; }}
</style>
<div class="box"><div class="lbl">What-if price</div><div class="num" id="num">${start:,.0f}</div>
<div class="delta" style="color:{delta_color}">{delta_text}</div>{pct_block}</div>
<script>
const a = {start}, b = {end}, p = {pct if pct is not None else "null"};
const el = document.getElementById("num"); const t0 = performance.now();
function step(t) {{ const k = Math.min(1, (t - t0) / 700); const e = 1 - Math.pow(1 - k, 3);
  el.textContent = "$" + Math.round(a + (b - a) * e).toLocaleString("en-US"); if (k < 1) requestAnimationFrame(step); }}
requestAnimationFrame(step);
if (p !== null) {{
  setTimeout(() => {{ document.getElementById("dot").style.left = p + "%"; }}, 60);
  const pe = document.getElementById("pct"); const t1 = performance.now();
  function s2(t) {{ const k = Math.min(1, (t - t1) / 900); pe.textContent = Math.round(p * (1 - Math.pow(1 - k, 3)));
    if (k < 1) requestAnimationFrame(s2); }}
  requestAnimationFrame(s2);
}}
</script>"""


@st.fragment
def what_if(result):
    """Live sliders: only this section reruns, so the price updates almost instantly."""
    location = result["location"]
    base = st.session_state.get("used_details", details_now())
    marker = (round(result["price"]), tuple(sorted(base.items())))
    if (st.session_state.get("whatif_for") != marker
            or any(f"wi_{key}" not in st.session_state for key in base)):
        st.session_state["whatif_for"] = marker
        st.session_state["wi_beds"], st.session_state["wi_baths"] = base["beds"], base["baths"]
        st.session_state["wi_sqft"] = min(max(int(round(base["sqft"] / 50) * 50), 400), 5000)
        st.session_state["wi_condition"] = base["condition"]
        st.session_state["wi_year"] = min(max(base["year"], 1800), datetime.date.today().year)
        st.session_state["wi_last"] = result["price"]

    ui.section("What if?", "Drag the sliders to see how a change would move the estimate. "
               "Nothing is saved, so explore freely.", anchor="whatif")
    with st.container(key="whatif"):
        sliders, readout = st.columns([1.15, 1], gap="large")
        with sliders:
            st.select_slider("Bedrooms", options=[1, 2, 3, 4, 5, 6], key="wi_beds",
                             format_func=lambda n: "6+" if n == 6 else str(n))
            st.select_slider("Bathrooms", options=[1, 2, 3, 4], key="wi_baths",
                             format_func=lambda n: "4+" if n == 4 else str(n))
            st.slider("Living area (sq ft)", 400, 5000, step=50, key="wi_sqft")
            st.select_slider("Condition inside", options=list(CONDITION_CHOICES), key="wi_condition",
                             format_func=lambda c: CONDITION_CHOICES[c])
            st.slider("Year built", 1800, datetime.date.today().year, key="wi_year")
        new_price = ins.quick_price(location, st.session_state["wi_sqft"], st.session_state["wi_beds"],
                                    st.session_state["wi_baths"], st.session_state["wi_condition"],
                                    st.session_state["wi_year"])
        pct, count = ins.zip_percentile(location["zip_code"], new_price)
        with readout:
            components.html(counter_html(st.session_state.get("wi_last", result["price"]), new_price,
                                         result["price"], pct, location["zip_code"], count), height=270)
        st.session_state["wi_last"] = new_price


def reason(feature, f, amount):
    """One factor as a plain-language sentence."""
    subject = {
        "distance_city_hall_miles": f"Being {f['distance_city_hall_miles']:.1f} miles from City Hall",
        "median_household_income": f"Neighborhood incomes (typical household {money(f['median_household_income'])})",
        "median_gross_rent": f"Neighborhood rents (typical {money(f['median_gross_rent'])} a month)",
        "owner_occupied_pct": f"How many neighbors own their home ({f['owner_occupied_pct']:.0f}%)",
        "total_livable_area": f"The size of the home ({f['total_livable_area']:,.0f} sq ft)",
        "number_of_bedrooms": f"{f['number_of_bedrooms']:.0f} bedroom{'s' if f['number_of_bedrooms'] != 1 else ''}",
        "number_of_bathrooms": f"{f['number_of_bathrooms']:.0f} bathroom{'s' if f['number_of_bathrooms'] != 1 else ''}",
        "house_age": f"The home's age ({f['house_age']:.0f} years)",
        "interior_condition": f"Condition: {CONDITION_CHOICES.get(int(f['interior_condition']), 'unknown').lower()}",
        "zip_code": f"Being in ZIP code {f['zip_code']:.0f}",
        "market_timing": f"Today's market and a {f['mortgage_rate']:.2f}% mortgage rate",
    }.get(feature, feature)
    size = money(round(abs(amount), -3)) if abs(amount) >= 1000 else "less than $1,000"
    verb = "adds about" if amount >= 0 else "lowers the price by about"
    return f"{subject} <b>{verb} {size}</b>"


def details_inputs():
    """The beginner-friendly detail fields, bound to session state keys."""
    this_year = datetime.date.today().year
    c1, c2 = st.columns(2)
    c1.segmented_control("Bedrooms", options=[1, 2, 3, 4, 5, 6], key="beds",
                         format_func=lambda n: "6+" if n == 6 else str(n))
    c2.segmented_control("Bathrooms", options=[1, 2, 3, 4], key="baths",
                         format_func=lambda n: "4+" if n == 4 else str(n))
    c3, c4 = st.columns(2)
    c3.number_input("Living area (square feet)", min_value=300, max_value=10000, step=50, key="sqft",
                    help="Not sure? Most Philadelphia rowhomes are between 1,000 and 1,500 sq ft.")
    c4.number_input("Year built", min_value=1750, max_value=this_year, step=1, key="year",
                    help="Not sure? Many Philadelphia rowhomes were built around 1920 to 1925.")
    st.select_slider("Condition inside the home", options=list(CONDITION_CHOICES), key="condition",
                     format_func=lambda c: CONDITION_CHOICES[c])


# --------------------------------------------------
# Hero and search
# --------------------------------------------------

ui.hero("What's this Philly home <em>worth today?</em>",
        "For Philadelphia agents pricing a listing, and buyers or homeowners checking a price. Search any address "
        "to see a suggested list price, a realistic range, and similar homes that sold nearby.",
        home=True)

with st.container(key="search_card"):
    with st.form("search_form", border=False):
        col_input, col_button = st.columns([4, 1.35], vertical_alignment="center")
        query = col_input.text_input("Search an address", key="query", label_visibility="collapsed",
                                     placeholder="Enter a Philadelphia address, like 2618 Jasper St")
        searched = col_button.form_submit_button("Search", type="primary", icon=":material/search:", width="stretch")
with st.container(key="hero_extras"):
    st.markdown(f'<div class="pp-trust">Free · No account needed · <b>{len(ins.load_homes()):,}</b> Philadelphia homes '
                "in our search</div>", unsafe_allow_html=True)
    st.button("Just looking? Try an example home", type="tertiary", on_click=fill_example)
    if not st.session_state.get("shown_q") and not st.session_state.get("pending_search"):
        st.markdown('<div class="pp-trust"><a href="#pp-details">No address? Price a home by its details</a></div>',
                    unsafe_allow_html=True)

if searched or st.session_state.pop("pending_search", False):
    run_search(st.session_state.get("query", ""))

lookup = st.session_state.get("lookup")

if lookup in ("units", "pick"):
    matches = pd.DataFrame(st.session_state["matches"])
    typed = st.session_state.get("typed_address", "")
    if lookup == "units":
        title, intro = "Which unit?", f"We found {len(matches)} homes at this address. "
    else:
        names = " and ".join(string.capwords(s.lower()) for s in st.session_state["streets"][:2])
        exact = int((matches.get("gap") == 0).sum()) if "gap" in matches else 0
        title = f"Homes on {names}"
        if exact:
            intro = f"{exact} homes match that address. "
        elif typed[:1].isdigit():
            intro = "We couldn't find that exact house number, so the closest ones come first. "
        else:
            intro = f"We found {len(matches):,} homes. "
    ui.section(title, intro + "Click a home to see its estimate.", anchor="picks")

    filter_col, other_col = st.columns([1, 2], vertical_alignment="bottom")
    number = filter_col.text_input("Filter by house number", key="pick_filter", placeholder="e.g. 2618",
                                   max_chars=6).strip()
    if lookup == "pick":
        other_col.button("Not on the list? Enter the details yourself", type="tertiary", on_click=enter_details_myself)
    if number:
        matches = matches[matches["address"].str.startswith(number)]
    if st.session_state.get("pick_for") != (typed, number):
        st.session_state["pick_for"], st.session_state["pick_shown"] = (typed, number), PICK_PAGE
    shown = matches.head(st.session_state["pick_shown"])

    if shown.empty:
        note(f"No house number starting with <b>{number}</b> on this street.")
    else:
        with st.spinner("Loading home photos…"):
            photos.has_photos(list(zip(shown["lat"], shown["lon"])))  # fetch in parallel, cached for the cards
        home_cards(shown, st.session_state["matches"], "pick")
        left = len(matches) - len(shown)
        if left > 0 and st.button(f"Show more homes ({left:,} left)", width="stretch"):
            st.session_state["pick_shown"] += PICK_PAGE
            st.rerun()

if lookup == "notfound" and not st.session_state.get("result"):
    ui.section("Tell us about the home",
               f"We couldn't find {st.session_state.get('typed_address', 'that address')} in the city's "
               "single-family records. "
               "It may be a condo building, an apartment, or a small typo. Add a few details and we'll still "
               "estimate it.")
    with st.container(key="details_card"), st.form("manual_form", border=False):
        details_inputs()
        if st.form_submit_button("Get my estimate", type="primary", icon=":material/search:"):
            run_estimate()

# --------------------------------------------------
# Results
# --------------------------------------------------

result = st.session_state.get("result")
if result:
    # Detail widgets lose their values when the visitor opens another page, so restore them.
    for key, value in st.session_state.get("used_details", {}).items():
        st.session_state.setdefault(key, value)
    home = st.session_state.get("home")
    location, f, hood, comps = result["location"], result["features"], result["neighborhood"], result["comps"]
    zip_code = location["zip_code"]
    title = nice_address(home["street"] if home else st.session_state.get("typed_address", ""),
                         zip_code if home else None)
    if home and "#" in home["address"]:
        title = nice_address(home["address"], zip_code)

    tabs = [("price", "Overview"), ("whatif", "What if"), ("why", "Why this price"), ("map", "Map")]
    tabs += ([("nearby", "Nearby sales")] if len(comps) else []) + [("area", "Neighborhood")]
    st.markdown(f'<div id="pp-price"></div><div class="pp-addr"><h2>{title}</h2>'
                f'<div class="hood">{ins.tract_label(location["GEOID"])}</div></div>'
                '<nav class="pp-tabs">' + "".join(f'<a href="#pp-{k}">{v}</a>' for k, v in tabs) + "</nav>",
                unsafe_allow_html=True)
    if st.session_state.pop("scroll_to_price", False):
        # Try twice: a slow connection can still be drawing the page the first time.
        st.html("<script>const goTo = () => { const el = document.getElementById('pp-price');"
                " if (el && Math.abs(el.getBoundingClientRect().top) > 120)"
                " el.scrollIntoView({behavior: 'smooth', block: 'start'}); };"
                " setTimeout(goTo, 300); setTimeout(goTo, 1200);</script>", unsafe_allow_javascript=True)

    d = st.session_state.get("used_details", details_now())
    sold = result.get("last_sale")
    price, low, high = result["price"], result["low"], result["high"]
    nearby = comps["sale_price"].median() if len(comps) else None
    axis_low = min([low] + ([nearby] if nearby else [])) * 0.92
    axis_high = max([high] + ([nearby] if nearby else [])) * 1.04

    def at(value):
        return f"{100 * (value - axis_low) / (axis_high - axis_low):.1f}%"

    tick = ""
    if nearby:
        spot = float(at(nearby)[:-1])
        shift = "0" if spot < 18 else ("-100%" if spot > 82 else "-50%")
        tick = (f'<span class="tick" style="left:{at(nearby)}"></span>'
                f'<span class="tick-lbl" style="left:{at(nearby)};transform:translateX({shift})">'
                f'Nearby sales {money_short(nearby)}</span>')
    facts = [(d["beds"], "beds"), (d["baths"], "baths"), (f"{d['sqft']:,}", "sq ft"), (d["year"], "built")]
    meta = [f"Condition: {CONDITION_CHOICES[d['condition']].lower()}"]
    if sold:
        meta.append(f"Last sold {money(sold['sale_price'])} in {sold['sale_date']:%b %Y}")

    range_note = ("8 in 10 similar homes sold within this range in 2025–26."
                  if ins.RANGE_METHOD == "price_band" else "")
    photo_col, est_col = st.columns([1.25, 1], gap="large")
    with photo_col:
        st.markdown(f'<div class="pp-hero-pic">{photos.picture_html(location["latitude"], location["longitude"], 360)}</div>',
                    unsafe_allow_html=True)
    with est_col:
        st.markdown(f"""
<div class="pp-est">
  <div class="k">PhillyPrice estimate</div>
  <div class="v">{money(price)}</div>
  <div class="bar"><span class="fill" style="left:{at(low)};width:calc({at(high)} - {at(low)})"></span>
    <span class="pin" style="left:{at(price)}"></span>{tick}</div>
  <div class="ends"><span>{money_short(low)}</span><span>Likely range</span><span>{money_short(high)}</span></div>
  <div class="range-note">{range_note}</div>
  <div class="facts">{"".join(f"<div><b>{v}</b><span>{k}</span></div>" for v, k in facts)}</div>
  <div class="meta">{" · ".join(meta)}<br><span>{"From the city's property records" if home else "From the details you entered"}</span></div>
</div>""", unsafe_allow_html=True)
        if account.enabled():
            save_button(result, home, title, d)
        b1, b2 = st.columns(2)
        b1.link_button("Street View", ins.street_view_url(location["latitude"], location["longitude"]),
                       icon=":material/streetview:", width="stretch")
        if home:
            b2.link_button("City record", ins.city_record_url(home["parcel_number"]),
                           icon=":material/description:", width="stretch")
    signin_prompt(home, title)

    if len(comps):
        line = (f"<b>Similar homes nearby sold for about {money_short(nearby)}.</b> That's the middle of {len(comps)} "
                f"recent sales within {comps['distance_miles'].max():.1f} miles, from "
                f"{money_short(comps['sale_price'].min())} to {money_short(comps['sale_price'].max())}.")
    else:
        line = "<b>No similar sales close by.</b> Compare with the neighborhood prices below."
    if hood["zip_median_price"] == hood["zip_median_price"]:
        line += f" The typical single-family home in ZIP {zip_code} sold for {money(hood['zip_median_price'])}."
    st.markdown(f'<div class="pp-compline">{line}</div>', unsafe_allow_html=True)

    with st.expander("Renovated, or something looks off? Update the details"):
        with st.form("adjust_form", border=False):
            details_inputs()
            if st.form_submit_button("Update my estimate", type="primary", icon=":material/refresh:"):
                run_estimate()
                st.rerun()

    what_if(result)

    left, right = st.columns([1.05, 1], gap="large")
    with left:
        ui.section("Why this price", "What pushed this estimate up, and what pulled it down.", anchor="why")
        factors = result["factors"]
        ups = factors[factors["amount"] > 0].head(3)
        downs = factors[factors["amount"] < 0].head(3)
        items = [f'<li><span class="dot up">arrow_upward</span><span>{reason(r.feature, f, r.amount)}</span></li>'
                 for r in ups.itertuples()]
        items += [f'<li><span class="dot down">arrow_downward</span><span>{reason(r.feature, f, r.amount)}</span></li>'
                  for r in downs.itertuples()]
        st.markdown('<ul class="pp-reasons">' + "".join(items) + "</ul>", unsafe_allow_html=True)
        with st.expander("See every factor"):
            st.caption(f"The estimate starts from the average Philadelphia sale ({money(result['baseline'])}). "
                       "Each bar is how much one detail moved it. Together they add up to the suggested price.")
            bars_data = factors.iloc[::-1]
            bars = go.Figure(go.Bar(
                x=bars_data["amount"], y=bars_data["label"], orientation="h",
                marker_color=[ui.GREEN if a >= 0 else ui.RED for a in bars_data["amount"]],
                text=[("+" if a >= 0 else "−") + money(abs(a)) for a in bars_data["amount"]],
                textposition="outside", cliponaxis=False, hoverinfo="skip"))
            low, high = min(bars_data["amount"].min(), 0), max(bars_data["amount"].max(), 0)
            pad = 0.32 * (high - low)
            bars.update_layout(height=36 * len(bars_data) + 30, margin=dict(l=0, r=10, t=6, b=6),
                               xaxis=dict(visible=False, range=[low - (pad if low < 0 else 0), high + pad]),
                               yaxis=dict(tickfont=dict(size=12)),
                               plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(bars, width="stretch", config={"displayModeBar": False, "scrollZoom": False})
    with right:
        ui.section("On the map", "The home in gold, similar sales in blue.", anchor="map")
        fig = go.Figure()
        if len(comps):
            fig.add_trace(go.Scattermap(
                lat=comps["lat"], lon=comps["lon"], mode="markers", name="Similar sales",
                marker=dict(size=13, color=ui.BLUE),
                text=[f"{nice_address(a)}<br>{money(p)} · {d:%b %Y}" for a, p, d in
                      zip(comps["address"], comps["sale_price"], comps["sale_date"])],
                hoverinfo="text"))
        fig.add_trace(go.Scattermap(
            lat=[location["latitude"]], lon=[location["longitude"]], mode="markers", name="This home",
            marker=dict(size=24, color=ui.GOLD), text=["This home"], hoverinfo="text"))
        fig.update_layout(map=dict(style="carto-positron", zoom=14.4,
                                   center=dict(lat=location["latitude"], lon=location["longitude"])),
                          margin=dict(l=0, r=0, t=0, b=0), height=380, showlegend=False)
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False, "scrollZoom": False})

    if len(comps):
        ui.section("Homes like this that sold nearby",
                   "Recent sales close by with about the same size. A few recorded sales can be transfers "
                   "between family members, so look twice at any price that seems out of line.", anchor="nearby")
        columns = st.columns(len(comps), gap="small")
        for i, (col, c) in enumerate(zip(columns, comps.itertuples())):
            with col, st.container(key=f"compcard_{i}"):
                st.markdown(
                    f'<div class="pp-comp">{photos.picture_html(c.lat, c.lon, 140)}'
                    f'<div class="body"><div class="price">Sold {money(c.sale_price)}</div>'
                    f'<div class="addr">{nice_address(c.address)}</div>'
                    f'<div class="sub">{c.sale_date:%b %Y} · {c.distance_miles:.2f} mi away</div>'
                    f'<div class="feat">{c.number_of_bedrooms:.0f} bd · {c.number_of_bathrooms:.0f} ba · '
                    f'{c.total_livable_area:,.0f} sq ft · built {c.year_built:.0f}</div>'
                    '</div></div>', unsafe_allow_html=True)
                st.button(f"Estimate {nice_address(c.address)}", key=f"comp_open_{i}", on_click=open_comp,
                          args=(c.address, int(c.zip_code) if c.zip_code == c.zip_code else None))
        with st.container(key="browse_more"):
            st.page_link("app_pages/find_homes.py", label="Browse more sold homes", icon=":material/arrow_forward:")

    ui.section("The neighborhood", ins.tract_label(location["GEOID"]), anchor="area")
    ui.stat_cards([
        (money(hood["tract_median_price"]) if hood["tract_median_price"] == hood["tract_median_price"] else "n/a",
         f"Typical sale on these blocks, 2019–26 ({int(hood['tract_sales'] or 0)} sales)"),
        (money(hood["median_household_income"]), "Typical household income"),
        (f"{money(hood['median_gross_rent'])}/mo", "Typical rent"),
        (f"{hood['owner_occupied_pct']:.0f}%", "Homes lived in by their owners"),
    ])
    st.caption("The estimate can't see a new kitchen, the layout, natural light, or street noise. Use the "
               "nearby sales and what you know about the home to adjust it.")

# --------------------------------------------------
# Below the fold
# --------------------------------------------------

if not result and lookup not in ("units", "pick", "notfound"):
    ui.section("Price a home by its details",
               "No address yet? Pick a neighborhood and describe the home, and get the model's predicted price.",
               anchor="details")
    with st.container(key="bydetails_card"), st.form("by_details_form", border=False):
        hood_col, size_col = st.columns([1.4, 1])
        hood = hood_col.selectbox("Neighborhood", list(ins.neighborhood_locations()), index=None,
                                  placeholder="Type or pick a neighborhood, like Fishtown", key="bd_hood")
        size_col.number_input("Living area (square feet)", 300, 10000, 1200, step=50, key="bd_sqft")
        c1, c2, c3 = st.columns([1, 1, 1])
        c1.segmented_control("Bedrooms", [1, 2, 3, 4, 5, 6], default=3, key="bd_beds",
                             format_func=lambda n: "6+" if n == 6 else str(n))
        c2.segmented_control("Bathrooms", [1, 2, 3, 4], default=1, key="bd_baths",
                             format_func=lambda n: "4+" if n == 4 else str(n))
        c3.number_input("Year built", 1750, datetime.date.today().year, 1925, key="bd_year")
        st.select_slider("Condition inside the home", options=list(CONDITION_CHOICES), value=4, key="bd_condition",
                         format_func=lambda c: CONDITION_CHOICES[c])
        if st.form_submit_button("Get predicted price", type="primary", icon=":material/calculate:"):
            if not hood:
                note("Pick a neighborhood first.")
                st.session_state.pop("by_details", None)
            else:
                details = {k: st.session_state[f"bd_{k}"] or v for k, v in
                           {"sqft": 1200, "beds": 3, "baths": 1, "year": 1925, "condition": 4}.items()}
                st.session_state["by_details"] = (hood, details, ins.price_by_details(
                    hood, details["sqft"], details["beds"], details["baths"], details["condition"], details["year"]))
    if st.session_state.get("by_details"):
        hood, d, est = st.session_state["by_details"]
        spread = (f"Across the {est['areas']} parts of {hood} we price, the same home ranges from "
                  f"{money_short(est['cheapest_area'])} to {money_short(est['priciest_area'])}. "
                  if est["areas"] > 1 else "")
        st.markdown(f"""
<div class="pp-detail-result">
  <div class="k">Predicted price · {d['beds']} bd · {d['baths']} ba · {d['sqft']:,} sq ft · built {d['year']} ·
    {CONDITION_CHOICES[d['condition']].lower()} · {hood}</div>
  <div class="v">{money(est['price'])}</div>
  <div class="r">Likely range <b>{money_short(est['low'])} – {money_short(est['high'])}</b>.
    8 in 10 similar homes sold within this range in 2025–26.</div>
  <div class="n">{spread}For a specific home, search its address above: the estimate then uses its exact location
    and adds nearby sales.</div>
</div>""", unsafe_allow_html=True)

    ui.section("Just looking? Start with one of these",
               "Homes that sold recently around Philadelphia. Click one to see what it would list for today.",
               anchor="explore")
    featured = ins.featured_homes()
    with st.spinner("Loading home photos…"):
        photos.has_photos(list(zip(featured["lat"], featured["lon"])))
    home_cards(featured, featured.to_dict("records"), "featured")

ui.footer()
