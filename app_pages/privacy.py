import streamlit as st

from core import ui

ui.hero("Privacy policy", "What PhillyPrice collects, why, and how to remove it.", compact=True)

st.markdown("""
*Last updated: October 18, 2026*

PhillyPrice is a free tool that estimates list prices for Philadelphia single-family homes. You can use every
part of it without an account. This page explains what happens to your information when you do sign in.

#### What we collect
- **If you sign in with Google:** your name and email address, which Google shares when you choose to sign in.
  We use them only to show who is signed in and to keep your saved homes in your account. We never see or
  store your Google password.
- **Homes you save:** the address, the estimate and range on the day you saved it, and the home's basic
  details (bedrooms, bathrooms, size), linked to your email address.
- **Searches:** the addresses you type are used to look up the home and produce the estimate. They are not
  stored in your account unless you save the home.

#### Cookies
- A sign-in cookie keeps you signed in for up to 30 days, or until you sign out.
- If you press Save before signing in, a short-lived cookie (15 minutes) remembers which home to save after
  Google sends you back.
- We don't use advertising or tracking cookies.

#### Where it is stored
- Saved homes are stored in a Supabase database that only the website's server can read.
- The site runs on Streamlit Community Cloud, which keeps standard server logs.
- Home photos are loaded from Mapillary, and maps from OpenStreetMap and CARTO, which may log normal web
  requests. Address lookups may be sent to the U.S. Census Bureau's public geocoder.

#### What we don't do
We don't sell or share your information, show ads, or send marketing email.

#### Removing your information
- Remove any saved home from the **Saved homes** page at any time.
- To delete everything linked to your email, open an issue on
  [the PhillyPrice GitHub page](https://github.com/AstraVo06/PhillyPrice/issues) and we'll remove it.
- You can also disconnect PhillyPrice from your Google account at
  [myaccount.google.com/connections](https://myaccount.google.com/connections).

#### Changes
If this policy changes, we'll update the date at the top of this page.
""")
ui.footer()
