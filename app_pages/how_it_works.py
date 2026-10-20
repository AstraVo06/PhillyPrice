import streamlit as st

from core import insights as ins
from core import ui
from core.ui import money, money_short

ui.hero("How it works", "Simple answers about where the price comes from and how much to trust it.", compact=True)

ui.section("From address to price")
ui.steps([
    ("We find the home",
     "The U.S. Census Bureau's address lookup gives us the ZIP code, the neighborhood (census tract), and the "
     "exact spot on the map. From there we add the neighborhood's typical income, rent, and how many homes are "
     "owner-occupied, plus the distance to City Hall."),
    ("We add today's market",
     "This month's 30-year mortgage rate and the year are added automatically, because rates and the "
     "market in a given year affect what buyers pay."),
    ("The model sets a price",
     "A machine-learning model (a random forest of 100 decision trees) learned from 107,321 Philadelphia "
     "single-family sales from 2019 to 2026 how these details relate to the price."),
    ("We show our work",
     "You see a realistic range, what pushed the price up or down, and similar homes that sold nearby."),
])

ui.section("Questions people ask")
with st.expander("How accurate is the estimate?", expanded=True):
    st.markdown("We tested it the way you'd use it: the model learned from 2019–2024 sales and then priced "
                "20,282 homes that sold in 2025 and 2026, without seeing their prices.")
    ui.stat_cards([
        (money(ins.TYPICAL_ERROR), "Average miss per home on 2025–26 sales"),
        ("0.41", "Share of price differences explained (R²), 2025–26 sales"),
        ("8 in 10", "2025–26 sales that landed inside their likely range"),
    ])
    st.markdown("A few very expensive or unusual sales make the average miss larger, so many homes land closer "
                "than that. Always compare the estimate with the nearby sales shown next to it.")

with st.expander("What does the realistic price range mean?"):
    if ins.RANGE_METHOD == "price_band":
        st.markdown("It's where **8 in 10 similar homes actually sold**. We priced the 2025–26 sales with a copy "
                    "of the model that only learned from 2019–2024, then measured how far the real sale prices "
                    "landed from the estimate. Cheaper homes have wider ranges because their sale prices vary "
                    "more: some sell well below value to family members or as-is.")
        rows = []
        previous = 0
        for top, low_x, high_x in ins.RANGE_BANDS:
            level = f"Over {money_short(previous)}" if top == float("inf") else (
                f"Under {money_short(top)}" if previous == 0 else f"{money_short(previous)} – {money_short(top)}")
            rows.append(f"| {level} | {(low_x - 1) * 100:+.0f}% | {(high_x - 1) * 100:+.0f}% |")
            previous = top
        table = "| Estimate | Low end | High end |\n|---|---|---|\n" + "\n".join(rows)
        st.markdown(table.replace("$", "\\$"))
        low, high = ins.price_range(None, 300_000)
        st.caption(f"For example, a $300K estimate has a likely range of about {money_short(low)} to "
                   f"{money_short(high)}.".replace("$", "\\$"))
    elif ins.RANGE_METHOD == "typical_error":
        st.markdown(f"It's the suggested price plus or minus **{money(ins.TYPICAL_ERROR)}**, the model's average "
                    "miss on recent sales. A home rarely sells for exactly one number, so the range is a better "
                    "way to talk about price with a buyer or seller.")
    else:
        st.markdown("The model is 100 decision trees that each make their own guess. The range covers the middle "
                    "80% of those guesses. A wide range means the trees disagree about this home.")

with st.expander("How do you know what pushed the price up or down?"):
    st.markdown("Each decision tree asks a series of yes/no questions, like *is the home within 2 miles of City "
                "Hall?* Every answer moves the guess up or down. We add up how much each detail moved it across "
                "all 100 trees. The amounts start from the average Philadelphia sale and add up exactly to the "
                "suggested price.")

with st.expander("Which homes count as similar homes nearby?"):
    st.markdown("Single-family homes that sold recently, close by (first within half a mile, widening if needed), "
                "with 75–125% of the home's living area and one bedroom more or less. Sales where several homes "
                "changed hands for one total price are left out, because that price covers the whole deal.")

with st.expander("Where does the data come from?"):
    sources = [
        ("City of Philadelphia property records (OpenDataPhilly)",
         "Every sale's price, date, size, bedrooms, bathrooms, condition, year built, and location.",
         "https://opendataphilly.org/datasets/philadelphia-properties-and-assessment-history/"),
        ("U.S. Census Bureau, American Community Survey 2024",
         "Typical household income, rent, and homeownership for each neighborhood.", "https://data.census.gov/"),
        ("U.S. Census Bureau, TIGER/Line 2024",
         "Neighborhood (census tract) boundaries.", "https://www2.census.gov/geo/tiger/TIGER2024/TRACT/"),
        ("Freddie Mac via FRED", "Weekly 30-year fixed mortgage rates.",
         "https://fred.stlouisfed.org/series/MORTGAGE30US"),
    ]
    for title, text, link in sources:
        st.markdown(f"**{title}** · {text} [View source]({link})")

with st.expander("What can't the estimate see?"):
    ui.checklist([
        "Anything inside the home beyond the condition you pick: a new kitchen, the layout, natural light.",
        "Street-level details like noise, parking, or a great view.",
        "School quality. Philadelphia is a single school district, and school-by-school data isn't included yet.",
        "Exact build year for many older homes. The city's records estimate it, so the home's age is approximate.",
        "Multi-family buildings, commercial properties, and homes outside Philadelphia.",
    ])

with st.expander("Is this an appraisal?"):
    st.markdown("No. It's a free, data-driven starting point for a pricing conversation. For a buying or selling "
                "decision, talk to a licensed real estate agent or appraiser.")

ui.footer()
