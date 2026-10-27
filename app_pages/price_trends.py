import plotly.graph_objects as go
import streamlit as st

from core import insights as ins
from core import ui
from core.ui import money

ui.hero("Price trends", "See how Philadelphia home prices changed since 2019, and compare ZIP codes side by side.",
        compact=True)

LINE_COLORS = [ui.BLUE, "#E3A21A", "#2A9D8F", "#8E5BB5", ui.RED]
MORTGAGE = "30-year mortgage rate"

metric = st.pills("Show", list(ins.SALES_METRICS) + [MORTGAGE], default="Typical sale price", required=True,
                  selection_mode="single", label_visibility="collapsed") or "Typical sale price"

if metric == MORTGAGE:
    rates = ins.mortgage_rates()
    fig = go.Figure(go.Scatter(x=rates["month"], y=rates["mortgage_rate"], mode="lines",
                               line=dict(color=ui.BLUE, width=3), hovertemplate="%{x|%b %Y}: %{y:.2f}%<extra></extra>"))
    low, high = rates.loc[rates["mortgage_rate"].idxmin()], rates.loc[rates["mortgage_rate"].idxmax()]
    for point, label in [(low, "Lowest"), (high, "Highest")]:
        fig.add_annotation(x=point["month"], y=point["mortgage_rate"], text=f"{label}: {point['mortgage_rate']:.2f}%",
                           showarrow=True, arrowhead=0, ax=0, ay=-30, font=dict(color=ui.BLUE, size=13))
    fig.update_layout(title=dict(text="30-year mortgage rate", x=0.02, xanchor="left", font=dict(size=20)),
                      height=520, margin=dict(l=10, r=30, t=70, b=10), yaxis=dict(ticksuffix="%", gridcolor=ui.LINE),
                      plot_bgcolor="#fff", paper_bgcolor="#fff")
    with st.container(border=True):
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False, "scrollZoom": False})
        st.caption("Source: Freddie Mac weekly survey via FRED, averaged by month. Higher rates make monthly "
                   "payments bigger, which usually cools prices.")
else:
    zip_options = [str(z) for z in sorted(ins.zip_centers().index)]
    areas = st.multiselect("Compare areas (up to 5)", ["All of Philadelphia"] + zip_options,
                           default=["All of Philadelphia", "19125", "19146"], max_selections=5,
                           format_func=ins.zip_label, help="Type a neighborhood or ZIP code to find it.")
    if not areas:
        st.info("Pick at least one area to see the chart.")
    else:
        data = ins.area_trend(metric, tuple(areas))
        YEARS = sorted(int(y) for y in data["year"].unique())
        is_money = metric != "Number of sales"
        fmt = (lambda v: money(v)) if is_money else (lambda v: f"{v:,.0f}")
        fig = go.Figure()
        for color, (area, rows) in zip(LINE_COLORS, data.groupby("area", sort=False)):
            fig.add_trace(go.Scatter(
                x=rows["year"], y=rows["value"], mode="lines+markers+text", name=area,
                line=dict(color=color, width=3), marker=dict(size=8),
                text=[fmt(v) if i in (0, len(rows) - 1) else "" for i, v in enumerate(rows["value"])],
                textposition="top center", textfont=dict(color=color, size=12), cliponaxis=False,
                hovertemplate=f"{area} %{{x}}: %{{customdata}}<extra></extra>",
                customdata=[fmt(v) for v in rows["value"]]))
        fig.update_layout(title=dict(text=f"{metric} by year", x=0.02, xanchor="left", font=dict(size=20)),
                          height=540, margin=dict(l=10, r=60, t=60, b=10),
                          xaxis=dict(tickvals=YEARS, ticktext=[str(y) if y in (YEARS[0], YEARS[-1]) else f"'{y % 100}"
                                                             for y in YEARS], tickangle=0, gridcolor="#fff"),
                          yaxis=dict(tickprefix="$" if is_money else "", tickformat=",.0f", gridcolor=ui.LINE),
                          legend=dict(orientation="h", y=-0.08, yanchor="top", x=0.5, xanchor="center"),
                          plot_bgcolor="#fff", paper_bgcolor="#fff")
        with st.container(border=True):
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False, "scrollZoom": False})
            st.caption("Single-family homes only. 2026 includes sales through September. Sales where several "
                       "homes changed hands for one total price are left out.")

        if metric != "Number of sales":
            ui.section("Change since 2019")
            cards = []
            for area, rows in data.groupby("area", sort=False):
                rows = rows.sort_values("year")
                first, last = rows.iloc[0], rows.iloc[-1]
                change = (last["value"] / first["value"] - 1) * 100
                cards.append((f"{'+' if change >= 0 else ''}{change:.0f}%",
                              f"{area}: {fmt(first['value'])} in {first['year']:.0f} → {fmt(last['value'])} in {last['year']:.0f}"))
            ui.stat_cards(cards, columns=min(len(cards), 3))

ui.footer()
