import streamlit as st

from core import ui

ui.hero("Terms of use", "The short version: estimates are a starting point, not an appraisal.", compact=True)

st.markdown("""
*Last updated: October 18, 2026*

By using PhillyPrice you agree to these terms.

#### Estimates are informational
PhillyPrice estimates come from a statistical model trained on past public sales. They can be wrong, sometimes
by a lot, and they can't see a home's interior, layout, or recent work. They are not an appraisal, a
broker price opinion, or financial, legal, or investment advice. Talk to a licensed real estate professional
before buying, selling, or pricing a home.

#### No warranty
The site is provided "as is", without warranties of any kind. We aren't liable for decisions made using it.

#### Data and images
Sales and property data come from the City of Philadelphia (OpenDataPhilly), the U.S. Census Bureau, and FRED.
Street photos come from Mapillary contributors (CC BY-SA) and maps from OpenStreetMap contributors and CARTO.
These sources keep their own licenses and terms.

#### Accounts
Sign-in is optional and uses your Google account. Don't misuse the site, for example by trying to access
other people's saved homes or overloading the service. We may remove saved data or end accounts that do.

#### Changes
We may update these terms. The date at the top shows the latest version.

See also our [privacy policy](/privacy).
""")
ui.footer()
