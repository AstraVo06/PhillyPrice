import streamlit as st

from core import insights as ins
from core import ui

ui.hero(f"About {ui.APP_NAME}",
        "Pricing help for Philadelphia single-family homes, built on the city's public sales records.",
        compact=True)

sales = ins.load_sales()
last_month = sales["sale_date"].max().strftime("%B %Y")

left, right = st.columns([1.2, 1], gap="large")
with left:
    ui.section("Why we built it")
    st.markdown(f"""
Pricing a home usually starts with experience and a handful of comparable listings. {ui.APP_NAME} adds a
data-driven starting point. Enter a Philadelphia address and the home's main features, and it suggests a
list price, a likely range, the reasons behind the price, and similar homes that sold nearby.

It's built to support an agent's judgment, not replace it. Things like a new kitchen, the layout, or
how quiet the street is still need a person who has seen the home.
""")
    ui.section("Who it's for")
    ui.checklist([
        "Real estate agents and brokers setting a list price or preparing for a conversation with a seller",
        "Home buyers checking whether an asking price is in a reasonable range",
        "Homeowners curious what their home might list for today",
    ])
with right:
    ui.section("By the numbers")
    facts = [
        (f"{len(sales):,}", "Single-family sales analyzed"),
        ("2019–2026", f"Sales recorded through {last_month}"),
        (f"{ins.load_tract_stats()['GEOID'].nunique()}", "Census tracts covered"),
        (f"{sales['zip_code'].nunique()}", "ZIP codes covered"),
    ]
    rows = [facts[:2], facts[2:]]
    for row in rows:
        cols = st.columns(2)
        for col, (value, label) in zip(cols, row):
            col.markdown(f'<div class="pp-stat" style="margin-bottom:12px"><div class="v">{value}</div>'
                         f'<div class="l">{label}</div></div>', unsafe_allow_html=True)
    ui.section("Good to know")
    ui.checklist([
        "Estimates are a starting point for a pricing conversation, not an appraisal.",
        "Only single-family homes in Philadelphia are covered.",
        "See How it works for the data sources, accuracy, and limits of the model.",
    ])
ui.footer()
