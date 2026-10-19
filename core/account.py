"""
Accounts: Sign in with Google (Streamlit's built-in st.login) and saved homes stored in Supabase.

Secrets this needs (Streamlit Cloud: app settings -> Secrets; locally: .streamlit/secrets.toml):
    SUPABASE_URL = "https://xxxx.supabase.co"
    SUPABASE_KEY = "sb_secret_..."        # server-side secret key, never shown in the page
    [auth]
    redirect_uri = "https://<your app>.streamlit.app/oauth2callback"
    cookie_secret = "<long random string>"
    client_id = "<Google OAuth client id>"
    client_secret = "<Google OAuth client secret>"
    server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
Without them the site still works, just without sign-in.
"""

from urllib.parse import quote, unquote

import requests
import streamlit as st
import streamlit.components.v1 as components

from core.photos import secret

TABLE = "saved_homes"
PENDING_COOKIE = "pp_pending_save"


def enabled():
    """True when both Google sign-in and the saved-homes database are set up."""
    try:
        has_auth = "auth" in st.secrets
    except Exception:
        has_auth = False
    return has_auth and bool(secret("SUPABASE_URL")) and bool(secret("SUPABASE_KEY"))


def signed_in():
    return enabled() and bool(getattr(st.user, "is_logged_in", False))


def email():
    return (st.user.get("email") or "").lower() if signed_in() else None


def first_name():
    if not signed_in():
        return None
    name = st.user.get("given_name") or st.user.get("name") or email().split("@")[0]
    return name.split()[0]


# --------------------------------------------------
# Saved homes in Supabase (REST API, server side only)
# --------------------------------------------------

def _endpoint():
    return f"{secret('SUPABASE_URL').rstrip('/')}/rest/v1/{TABLE}"


def _headers(extra=None):
    key = secret("SUPABASE_KEY")
    headers = {"apikey": key, "Content-Type": "application/json"}
    if key.startswith("eyJ"):  # older service_role keys are JWTs and also go in Authorization
        headers["Authorization"] = f"Bearer {key}"
    return {**headers, **(extra or {})}


def saved_homes(refresh=False):
    """The signed-in visitor's saved homes, newest first. Cached for the session."""
    if not signed_in():
        return []
    if refresh or "saved_homes" not in st.session_state:
        response = requests.get(_endpoint(), headers=_headers(), timeout=10, params={
            "user_email": f"eq.{email()}", "order": "saved_at.desc", "select": "*"})
        response.raise_for_status()
        st.session_state["saved_homes"] = response.json()
    return st.session_state["saved_homes"]


def is_saved(home_key):
    return any(row["home_key"] == home_key for row in saved_homes())


def save_home(home):
    """Save or update a home. `home` has home_key, address, lat, lon, estimate, low, high, beds, baths, sqft."""
    response = requests.post(_endpoint(), json={**home, "user_email": email()}, timeout=10,
                             params={"on_conflict": "user_email,home_key"},
                             headers=_headers({"Prefer": "resolution=merge-duplicates,return=minimal"}))
    response.raise_for_status()
    saved_homes(refresh=True)


def remove_home(home_key):
    response = requests.delete(_endpoint(), headers=_headers(), timeout=10,
                               params={"user_email": f"eq.{email()}", "home_key": f"eq.{home_key}"})
    response.raise_for_status()
    saved_homes(refresh=True)


# --------------------------------------------------
# Save a home across the Google sign-in round trip
# --------------------------------------------------
# Google sends the visitor back to the home page in a new session, so the home they wanted to save
# is kept in a short-lived browser cookie and saved once they are back and signed in.

def remember_pending(search_text):
    components.html(f"<script>window.parent.document.cookie = '{PENDING_COOKIE}={quote(search_text)}; "
                    "path=/; max-age=900; SameSite=Lax';</script>", height=0)


def take_pending():
    """The search text saved before sign-in, once, and clears the cookie."""
    value = st.context.cookies.get(PENDING_COOKIE)
    if not value or not signed_in() or st.session_state.get("pending_taken"):
        return None
    st.session_state["pending_taken"] = True
    components.html(f"<script>window.parent.document.cookie = '{PENDING_COOKIE}=; path=/; max-age=0';</script>",
                    height=0)
    return unquote(value)
