import datetime
import string

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
import streamlit.components.v1 as components

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

# A search can be started from another page (Find homes) by setting "search_request".
if "search_request" in st.session_state:
    st.session_state["query"] = st.session_state.pop("search_request")
    st.session_state["pending_search"] = True


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
    for key in ["result", "home", "matches", "typed_address", "streets", "pick_filter"]:
        st.session_state.pop(key, None)
    if not query:
        st.session_state["lookup"] = None
        note("Type a street address, like <b>2618 Jasper St</b>, or just a street name, like <b>Jasper St</b>.")
        return
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


def pick_home(home):
    st.session_state["picked_home"] = home
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

    ui.section("Play with the price", "Drag the sliders to see how a change would move the estimate. "
               "Nothing is saved, so explore freely.", eyebrow="What if", anchor="whatif")
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
        "Search any address to see a suggested list price, a realistic range, and similar homes that sold nearby.",
        home=True)

with st.container(key="search_card"):
    with st.form("search_form", border=False):
        col_input, col_button = st.columns([4.2, 1.2], vertical_alignment="center")
        query = col_input.text_input("Search an address", key="query", label_visibility="collapsed",
                                     placeholder="Enter a Philadelphia address, like 2618 Jasper St")
        searched = col_button.form_submit_button("Search", type="primary", icon=":material/search:")
with st.container(key="hero_extras"):
    st.markdown(f'<div class="pp-trust">Free · No sign-up · <b>{len(ins.load_homes()):,}</b> Philadelphia homes '
                "in our search</div>", unsafe_allow_html=True)
    st.button("Just looking? Try an example home", type="tertiary", on_click=fill_example)

if searched or st.session_state.pop("pending_search", False):
    run_search(st.session_state.get("query", ""))

lookup = st.session_state.get("lookup")

if st.session_state.get("picked_home"):
    select_home(st.session_state.pop("picked_home"))
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
        for row_start in range(0, len(shown), 4):
            cols = st.columns(4, gap="small")
            for col, (i, m) in zip(cols, shown.iloc[row_start:row_start + 4].iterrows()):
                sold = (f"Last sold {money_short(m['sale_price'])} · {m['sale_date']:%Y}"
                        if m["sale_price"] >= 1000 and pd.notna(m["sale_date"]) else "No recent sale on record")
                beds = f"{m['number_of_bedrooms']:.0f} bd · " if m["number_of_bedrooms"] >= 1 else ""
                baths = f"{m['number_of_bathrooms']:.0f} ba · " if m["number_of_bathrooms"] >= 1 else ""
                size = f"{m['total_livable_area']:,.0f} sq ft" if m["total_livable_area"] > 0 else "size unknown"
                built = f" · built {m['year_built']:.0f}" if m["year_built"] > 0 else ""
                with col, st.container(key=f"compcard_pick_{i}"):
                    st.markdown(
                        f'<div class="pp-comp">{photos.picture_html(m["lat"], m["lon"], 140)}'
                        f'<div class="top light">{sold}</div><div class="body">'
                        f'<div class="addr">{nice_address(m["address"])}</div>'
                        f'<div class="sub">ZIP {m["zip_code"]:.0f}</div>'
                        f'<div class="feat">{beds}{baths}{size}{built}</div>'
                        f'<div class="go">See the estimate →</div></div></div>', unsafe_allow_html=True)
                    st.button(f"Estimate {nice_address(m['address'])}", key=f"pick_open_{i}", on_click=pick_home,
                              args=(st.session_state["matches"][i],))
        left = len(matches) - len(shown)
        if left > 0 and st.button(f"Show more homes ({left:,} left)", use_container_width=True):
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

    ui.section(title, eyebrow="Your estimate", anchor="price")
    if st.session_state.pop("scroll_to_price", False):
        components.html("<script>setTimeout(() => window.parent.document.getElementById('pp-price')"
                        "?.scrollIntoView({behavior: 'smooth'}), 250);</script>", height=0)
    photo_col, facts_col = st.columns([1.1, 1], gap="large")
    with photo_col:
        st.markdown(f'<div class="pp-hero-pic">{photos.picture_html(location["latitude"], location["longitude"], 250)}</div>',
                    unsafe_allow_html=True)
        b1, b2 = st.columns(2)
        b1.link_button("Street View", ins.street_view_url(location["latitude"], location["longitude"]),
                       icon=":material/streetview:", use_container_width=True)
        if home:
            b2.link_button("City property record", ins.city_record_url(home["parcel_number"]),
                           icon=":material/description:", use_container_width=True)
    with facts_col:
        d = st.session_state.get("used_details", details_now())
        facts = [
            ("bed", f"{d['beds']} bedroom{'s' if d['beds'] != 1 else ''}"),
            ("bathtub", f"{d['baths']} bathroom{'s' if d['baths'] != 1 else ''}"),
            ("square_foot", f"{d['sqft']:,} sq ft"),
            ("calendar_month", f"Built {d['year']}"),
            ("handyman", f"Condition: {CONDITION_CHOICES[d['condition']].lower()}"),
        ]
        sold = result.get("last_sale")
        if sold:
            facts.append(("sell", f"Last sold {money(sold['sale_price'])} in {sold['sale_date']:%b %Y}"))
        source = "From the city's property records" if home else "From the details you entered"
        st.markdown(f'<div class="pp-facts"><div class="pp-label">Home facts</div>'
                    + "".join(f'<div class="f"><span class="material-symbols-rounded">{i}</span>{t}</div>'
                              for i, t in facts)
                    + f'<div class="src">{source}</div></div>', unsafe_allow_html=True)

    st.markdown(f"""
<div class="pp-pair" style="margin-top:18px">
  <div class="pp-pcard"><div class="pp-label">Suggested list price</div><div class="pp-big">{money(result["price"])}</div></div>
  <div class="pp-arrow">→</div>
  <div class="pp-pcard coral"><div class="pp-label coral">Realistic price range</div>
    <div class="pp-big coral">{money_short(result["low"])} – {money_short(result["high"])}</div></div>
</div>""", unsafe_allow_html=True)

    notes = []
    if len(comps):
        headline = f"Similar homes nearby sold for about {money_short(comps['sale_price'].median())}"
        notes.append(f"That's the middle of {len(comps)} recent sales within {comps['distance_miles'].max():.1f} miles "
                     f"with about the same size, which ranged from {money_short(comps['sale_price'].min())} to "
                     f"{money_short(comps['sale_price'].max())}.")
    else:
        headline = "No similar sales close by"
        notes.append("Compare with the neighborhood prices below instead.")
    if hood["zip_median_price"] == hood["zip_median_price"]:
        notes.append(f"The typical single-family home in ZIP {zip_code} sold for {money(hood['zip_median_price'])}.")
    st.markdown(f'<div class="pp-callout"><div class="t">{headline}</div><div class="s">{" ".join(notes)}</div></div>',
                unsafe_allow_html=True)

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
            st.plotly_chart(bars, use_container_width=True, config={"displayModeBar": False, "scrollZoom": False})
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
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "scrollZoom": False})

    if len(comps):
        ui.section("Homes like this that sold nearby",
                   "Recent sales close by with about the same size. A few recorded sales can be transfers "
                   "between family members, so look twice at any price that seems out of line.", anchor="nearby")
        columns = st.columns(len(comps), gap="small")
        for i, (col, c) in enumerate(zip(columns, comps.itertuples())):
            with col, st.container(key=f"compcard_{i}"):
                st.markdown(
                    f'<div class="pp-comp">{photos.picture_html(c.lat, c.lon, 140)}'
                    f'<div class="top">Sold {money(c.sale_price)}</div><div class="body">'
                    f'<div class="addr">{nice_address(c.address)}</div>'
                    f'<div class="sub">{c.sale_date:%b %Y} · {c.distance_miles:.2f} mi away</div>'
                    f'<div class="feat">{c.number_of_bedrooms:.0f} bd · {c.number_of_bathrooms:.0f} ba · '
                    f'{c.total_livable_area:,.0f} sq ft · built {c.year_built:.0f}</div>'
                    f'<div class="go">Estimate this home →</div></div></div>', unsafe_allow_html=True)
                st.button(f"Estimate {nice_address(c.address)}", key=f"comp_open_{i}", on_click=open_comp,
                          args=(c.address, int(c.zip_code) if c.zip_code == c.zip_code else None))
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
    ui.floating_nav([("price", "Price"), ("whatif", "What if"), ("why", "Why"), ("map", "Map")]
                    + ([("nearby", "Nearby sales")] if len(comps) else []) + [("area", "Area")])

# --------------------------------------------------
# Below the fold
# --------------------------------------------------

ui.feature_band()
ui.section("How it works", eyebrow="Three simple steps")
ui.steps([
    ("Search the address", "We find the home in the city's records and fill in its details for you."),
    ("Check the details", "Renovated or something's off? Update bedrooms, size, or condition in one click."),
    ("Get a price you can explain", "A suggested price, a realistic range, the reasons behind it, and nearby sales."),
])
ui.footer()
