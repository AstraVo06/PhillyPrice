"""Shared look and feel: colors, CSS, the top bar, and HTML blocks used on several pages."""

import streamlit as st

APP_NAME = "PhillyPrice"
TAGLINE = "Know what a Philadelphia home should list for"

# "Philly flag" palette: the blue and gold of the City of Philadelphia flag.
BLUE = "#1B3A6B"
NAVY = BLUE
DEEP = "#0E1F3D"
GOLD = "#F2B233"
GOLD_DARK = "#DDA01F"
GOLD_TEXT = "#8A5A00"
GOLD_TINT = "#FFF4DC"
GOLD_LINE = "#F5D58A"
RED = "#C2412D"
INK = "#1B2537"
MUTED = "#5E6575"
LINE = "#E8E5E0"
PAPER = "#F7F5F2"
GREEN = "#2E8B57"

# Philadelphia skyline over the Schuylkill River, served from static/ (Unsplash License).
HERO_PHOTO = "app/static/philly-skyline.jpg"
PHOTO_CREDIT = ('Cover photo by <a href="https://unsplash.com/photos/M_P5NZ-jKuw?utm_source=philly_price&utm_medium=referral" '
                'target="_blank">Alejandro Barba</a> on <a href="https://unsplash.com/?utm_source=philly_price&utm_medium=referral" '
                'target="_blank">Unsplash</a>')

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..900&family=Public+Sans:wght@400;500;600;700;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,0,0&display=block');

html, body, [class*="st-"], .stMarkdown, button, input, select, textarea {{ font-family: 'Public Sans', sans-serif; }}
h1, h2, h3, h4, .pp-section-title, .pp-big, .pp-band h2, .pp-callout .t, .pp-step .h, .pp-footer .logo,
.st-key-nav_logo [data-testid="stPageLink"] a p {{ font-family: 'Archivo', sans-serif !important; font-stretch: 108%; }}
.material-symbols-rounded, [data-testid="stIconMaterial"], [data-testid="stAlertDynamicIcon"],
[data-testid="stAlertDynamicIcon"] * {{ font-family: 'Material Symbols Rounded' !important; }}

/* Streamlit chrome off: this is a website, not a notebook */
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stSidebarCollapsedControl"],
[data-testid="stDecoration"], #MainMenu, footer {{ display: none !important; }}
[data-testid="stHeaderActionElements"] {{ display: none !important; }}
[data-testid="stAppViewContainer"] {{ overflow-x: hidden; }}
.block-container {{ padding-top: 0 !important; padding-bottom: 0; max-width: 1180px; }}
h1, h2, h3, h4 {{ color: {INK}; letter-spacing: -0.02em; }}

/* Top bar */
.st-key-navbar {{
    position: sticky; top: 0; z-index: 1000; background: #fff; padding: 12px 0 10px;
    box-shadow: 0 0 0 100vmax #fff, 0 1px 0 100vmax {LINE}; clip-path: inset(0 -100vmax -1px);
}}
.st-key-navbar [data-testid="stHorizontalBlock"] {{ align-items: center; flex-wrap: nowrap; gap: 2px; overflow-x: auto; }}
.st-key-navbar [data-testid="stColumn"] {{ width: auto !important; flex: 0 0 auto !important; min-width: 0 !important; }}
.st-key-navbar [data-testid="stColumn"]:nth-child(2) {{ flex: 1 1 auto !important; }}
.st-key-navbar [data-testid="stPageLink"] a {{ border-radius: 999px; padding: 6px 14px; }}
.st-key-navbar [data-testid="stPageLink"] a p {{ font-weight: 600; color: {INK}; font-size: 0.98rem; white-space: nowrap; }}
.st-key-nav_logo [data-testid="stPageLink"] a {{ padding-left: 0; background: transparent !important; }}
.st-key-nav_logo [data-testid="stPageLink"] a p {{ font-size: 1.5rem !important; font-weight: 800 !important; color: {NAVY} !important; letter-spacing: -0.03em; }}
.st-key-nav_logo [data-testid="stIconMaterial"] {{ color: {GOLD}; font-size: 1.9rem; width: 1.9rem; height: 1.9rem;
    line-height: 1.9rem; display: inline-flex; align-items: center; justify-content: center; }}
.st-key-nav_logo [data-testid="stPageLink"] a span:has(> [data-testid="stIconMaterial"]) {{ width: auto; height: auto;
    overflow: visible; margin-right: -3px; }}
.st-key-nav_logo [data-testid="stPageLink"] a {{ gap: 2px !important; }}
.st-key-nav_cta [data-testid="stPageLink"] a {{ background: {GOLD} !important; box-shadow: none !important; }}
.st-key-nav_cta [data-testid="stPageLink"] a p {{ color: {INK} !important; }}
.st-key-nav_cta [data-testid="stPageLink"] a:hover {{ background: {GOLD_DARK} !important; }}
@media (max-width: 900px) {{
    .st-key-nav_cta {{ display: none; }}
    .st-key-navbar [data-testid="stPageLink"] a {{ padding: 6px 9px; }}
    .st-key-nav_logo [data-testid="stPageLink"] a p {{ font-size: 1.3rem !important; }}
}}

.st-key-nav_account button {{ border-radius: 999px; border: 1px solid {LINE}; font-weight: 600; white-space: nowrap; }}
.st-key-nav_account button p {{ font-weight: 600; color: {INK}; }}
.st-key-signin_card {{ border-left: 4px solid {GOLD}; padding: 6px 0 6px 16px; margin: 12px 0; }}

/* Hero */
.pp-hero {{
    width: 100vw; margin-left: calc(50% - 50vw); position: relative; min-height: 520px;
    background: linear-gradient(rgba(14,31,61,0.45), rgba(14,31,61,0.62)), url('{HERO_PHOTO}') center 45%/cover;
    display: flex; flex-direction: column; justify-content: center; align-items: center;
    text-align: center; padding: 90px 24px 160px;
}}
.pp-hero h1 {{ color: #fff; font-family: 'Archivo', sans-serif; font-stretch: 112%; font-weight: 800; font-size: clamp(2.4rem, 6vw, 4.6rem);
              line-height: 1.04; letter-spacing: -0.035em; margin: 0 0 16px; max-width: 1000px;
              animation: ppRise 0.9s cubic-bezier(.2,.7,.2,1) both; }}
.pp-hero p {{ animation: ppRise 0.9s 0.15s cubic-bezier(.2,.7,.2,1) both; }}
.pp-hero h1 em {{ font-style: normal; color: {GOLD}; display: block; }}
.pp-hero p {{ color: rgba(255,255,255,0.93); font-size: clamp(1.05rem, 2vw, 1.3rem); max-width: 760px; margin: 0; }}
.pp-hero.pp-compact {{ min-height: 280px; padding: 70px 24px; }}
[data-testid="stElementContainer"]:has(.pp-hero.pp-compact) {{ margin-bottom: 30px; }}
.pp-hero.pp-compact h1 {{ font-size: clamp(2rem, 4.5vw, 3.3rem); }}

/* Address search inside the home hero */
.pp-hero.pp-home {{ min-height: 500px; padding: 70px 24px 160px; }}
.pp-hero.pp-home h1 {{ font-size: clamp(2.2rem, 5.2vw, 4.1rem); }}
.st-key-search_card {{
    background: #fff; border-radius: 999px; padding: 8px 8px 8px 22px; border: none;
    box-shadow: 0 22px 60px rgba(8,12,20,0.35); max-width: 800px; width: 100%; margin: 0 auto;
    position: relative; z-index: 5; flex: 0 1 auto !important; height: fit-content !important; align-self: flex-start;
}}
[data-testid="stLayoutWrapper"]:has(> .st-key-search_card) {{ margin-top: -154px; position: relative; z-index: 5; }}
.st-key-search_card [data-testid="stForm"] {{ border: none; padding: 0; }}
.st-key-search_card [data-testid="stTextInput"] div[data-baseweb="input"],
.st-key-search_card [data-testid="stTextInput"] div[data-baseweb="base-input"],
.st-key-search_card [data-testid="stTextInputRootElement"] {{ border: none !important; background: transparent !important; }}
.st-key-search_card [data-testid="stTextInput"] input {{ font-size: 1.15rem; padding: 14px 4px; background: transparent; }}
.st-key-search_card [data-testid="InputInstructions"] {{ display: none; }}
.st-key-search_card [data-testid="stFormSubmitButton"] button {{ padding: 0 1.6rem; min-height: 60px; font-size: 1.15rem;
    white-space: nowrap; width: 100%; }}
.st-key-search_card [data-testid="stFormSubmitButton"] button p {{ font-size: 1.15rem; }}
.st-key-search_card [data-testid="stFormSubmitButton"], .st-key-search_card [data-testid="stFormSubmitButton"] > div {{ width: 100%; }}
.st-key-search_card [data-testid="stFormSubmitButton"] button [data-testid="stIconMaterial"] {{ font-size: 1.4rem; }}
.st-key-browse_more {{ margin-top: 16px; }}
.st-key-search_card [data-testid="stFormSubmitButton"] button p {{ white-space: nowrap; }}
.st-key-hero_extras {{ max-width: 800px; margin: 0 auto; position: relative; z-index: 5; text-align: center;
                      flex: 0 1 auto !important; height: fit-content !important; gap: 0 !important; }}
.st-key-hero_extras [data-testid="stHorizontalBlock"] {{ justify-content: center; align-items: center; }}
.st-key-hero_extras .stButton button[kind="tertiary"] p, .st-key-hero_extras .stButton button[kind="tertiary"] span {{ color: #fff !important; }}
.st-key-hero_extras .stButton button[kind="tertiary"] {{ text-decoration: underline; }}
.st-key-hero_extras .stButton, .st-key-hero_extras [data-testid="stElementContainer"] {{ display: flex; justify-content: center; width: 100% !important; }}
.pp-trust {{ color: rgba(255,255,255,0.88); font-size: 0.92rem; text-align: center; }}
.pp-trust b {{ color: #fff; }}
.st-key-details_card {{
    background: #fff; border-radius: 22px; padding: 22px 26px 8px; border: 1px solid {LINE};
    box-shadow: 0 12px 34px rgba(12,17,28,0.10); margin-top: 26px;
}}
.pp-step-label {{ font-weight: 800; color: {INK}; font-size: 1.05rem; margin: 2px 0 8px; }}
.pp-step-label span {{ display: inline-flex; width: 26px; height: 26px; border-radius: 50%; background: {GOLD};
                      color: {INK}; align-items: center; justify-content: center; font-size: 0.85rem; margin-right: 8px; }}
.stButton button[kind="primary"], [data-testid="stFormSubmitButton"] button {{
    background: {GOLD}; color: {INK}; border: none; border-radius: 999px; font-weight: 700; padding: 0.7rem 2rem; font-size: 1.05rem;
    box-shadow: 0 8px 20px rgba(242,178,51,0.35);
}}
.stButton button[kind="primary"] p, [data-testid="stFormSubmitButton"] button p,
.stButton button[kind="primary"] [data-testid="stIconMaterial"], [data-testid="stFormSubmitButton"] button [data-testid="stIconMaterial"] {{ color: {INK}; }}
.stButton button[kind="primary"]:hover, [data-testid="stFormSubmitButton"] button:hover {{ background: {GOLD_DARK}; color: {INK}; }}
.stButton button[kind="tertiary"] {{ color: {BLUE}; font-weight: 600; }}

/* Result */
.pp-pair {{ display: grid; grid-template-columns: 1fr auto 1fr; gap: 14px; align-items: center; }}
.pp-pcard {{ background: #fff; border: 1.5px solid {LINE}; border-radius: 18px; padding: 20px 24px; }}
.pp-pcard.coral {{ background: {GOLD_TINT}; border-color: {GOLD_LINE}; }}
.pp-label {{ color: {MUTED}; font-size: 0.9rem; font-weight: 600; }}
.pp-label.coral {{ color: {GOLD_TEXT}; }}
.pp-big {{ color: {INK}; font-size: clamp(1.9rem, 3.6vw, 2.7rem); font-weight: 800; letter-spacing: -0.04em; line-height: 1.15; margin-top: 4px; }}
.pp-big.coral {{ color: {BLUE}; }}
.pp-arrow {{ color: {MUTED}; font-size: 1.6rem; }}
.pp-callout {{ background: {GOLD_TINT}; border: 1.5px solid {GOLD_LINE}; border-radius: 18px; padding: 18px 24px; margin-top: 14px; }}
.pp-callout .t {{ color: {BLUE}; font-weight: 800; font-size: 1.3rem; margin-bottom: 4px; }}
.pp-callout .s {{ color: {INK}; font-size: 0.98rem; line-height: 1.7; }}
@media (max-width: 640px) {{ .pp-pair {{ grid-template-columns: 1fr; }} .pp-arrow {{ display: none; }} }}

.pp-photo {{ background: linear-gradient(135deg, {PAPER}, #EFE9E2); border: 1px solid {LINE}; border-radius: 18px;
             height: 230px; display: flex; flex-direction: column; align-items: center; justify-content: center;
             color: {MUTED}; gap: 8px; margin-bottom: 10px; font-weight: 600; text-align: center; padding: 0 20px; }}
.pp-photo .material-symbols-rounded {{ font-size: 64px; color: {GOLD}; }}
.pp-pic {{ position: relative; overflow: hidden; background-color: #E6EBF2; }}
.pp-pic img {{ width: 100%; height: 100%; object-fit: cover; display: block; transition: transform .5s ease; }}
.pp-pic .credit {{ position: absolute; right: 6px; bottom: 5px; font-size: 10px; color: #fff; background: rgba(0,0,0,0.45);
                   padding: 1px 6px; border-radius: 6px; }}
.pp-comp:hover .pp-pic img {{ transform: scale(1.06); }}
.pp-pic.map::after {{ content: ""; position: absolute; left: 50%; top: 50%; width: 18px; height: 18px; margin: -9px 0 0 -9px;
                     border-radius: 50%; background: {GOLD}; border: 3px solid #fff; box-shadow: 0 2px 10px rgba(14,31,61,0.45); }}
.pp-hero-pic .pp-pic {{ border-radius: 18px; margin-bottom: 10px; border: 1px solid {LINE}; }}
.pp-howto {{ display: flex; gap: 12px; align-items: flex-start; border-left: 4px solid {GOLD};
             padding: 4px 0 4px 14px; margin-bottom: 12px; color: {INK}; font-size: 0.95rem; line-height: 1.55; }}
.pp-howto .material-symbols-rounded {{ color: {GOLD_TEXT}; font-size: 24px; }}
.pp-facts {{ background: #fff; border: 1px solid {LINE}; border-radius: 18px; padding: 18px 22px; }}
.pp-facts .f {{ display: flex; align-items: center; gap: 12px; padding: 7px 0; color: {INK}; font-weight: 600;
               border-bottom: 1px solid {LINE}; }}
.pp-facts .f:last-of-type {{ border-bottom: none; }}
.pp-facts .f .material-symbols-rounded {{ color: {BLUE}; font-size: 22px; }}
.pp-facts .src {{ color: {MUTED}; font-size: 0.8rem; margin-top: 8px; }}
.pp-comps {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(205px, 1fr)); gap: 14px; }}
.pp-comp {{ background: #fff; border: 1px solid {LINE}; border-radius: 12px; overflow: hidden; }}
.pp-comp .price {{ font-weight: 800; color: {INK}; font-size: 1.02rem; margin-bottom: 4px; }}
.pp-comp .top {{ background: {BLUE}; color: #fff; font-weight: 800; text-align: center; padding: 10px; }}
.pp-comp .body {{ padding: 14px 16px; }}
.pp-comp .price, .pp-comp .sub {{ white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.pp-comp .addr {{ font-weight: 700; color: {INK}; line-height: 1.35; height: 2.7em; overflow: hidden;
                 display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }}
.pp-comp .sub {{ color: {MUTED}; font-size: 0.86rem; margin: 2px 0 8px; }}
.pp-comp .feat {{ color: {INK}; font-size: 0.9rem; line-height: 1.5; min-height: 3em; }}

.pp-reasons {{ list-style: none; padding: 0; margin: 0; }}
.pp-reasons li {{ display: flex; gap: 10px; align-items: flex-start; padding: 9px 0; border-bottom: 1px solid {LINE}; color: {INK}; }}
.pp-reasons li:last-child {{ border-bottom: none; }}
.pp-reasons .dot {{ flex: 0 0 28px; height: 28px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center;
                   font-family: 'Material Symbols Rounded'; font-size: 18px; }}
.pp-reasons .up {{ background: #E3F3EA; color: {GREEN}; }}
.pp-reasons .down {{ background: #FBE9E5; color: {RED}; }}

/* Cards and sections */
.maplibregl-map {{ position: relative; }}
.maplibregl-ctrl-bottom-right {{ position: absolute !important; right: 0; bottom: 0; z-index: 2; }}
.maplibregl-ctrl-attrib {{ font-size: 10px; background: rgba(255,255,255,0.8); padding: 1px 6px; }}
.maplibregl-ctrl-attrib-button {{ display: none; }}

.pp-card {{ background: #fff; border: 1px solid {LINE}; border-radius: 18px; padding: 22px 24px; height: 100%; }}
.pp-stat {{ background: {PAPER}; border-radius: 14px; padding: 14px 16px; min-height: 100px; }}
.pp-stat div {{ margin: 0; }}
.pp-stat .v {{ font-size: 1.3rem; font-weight: 800; color: {INK}; }}
.pp-stat .l {{ font-size: 0.83rem; color: {MUTED}; }}
.pp-section-title {{ font-size: clamp(1.45rem, 2.7vw, 2rem); font-weight: 800; color: {INK}; margin: 40px 0 6px; letter-spacing: -0.035em; line-height: 1.15; }}
.pp-section-sub {{ color: {MUTED}; margin: 0 0 16px; font-size: 1rem; }}
.pp-eyebrow {{ color: {GOLD_TEXT}; font-weight: 700; font-size: 0.95rem; margin-top: 40px; }}

.pp-band {{ width: 100vw; margin-left: calc(50% - 50vw); background: {DEEP}; padding: 64px 24px; margin-top: 56px; }}
.pp-band h2 {{ color: #fff; text-align: center; font-size: clamp(1.7rem, 3.6vw, 2.8rem); font-weight: 800; margin: 0 auto 34px; max-width: 900px; }}
.pp-band-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 18px; max-width: 1180px; margin: 0 auto; }}
@media (max-width: 1000px) {{ .pp-band-grid {{ grid-template-columns: repeat(2, 1fr); }} }}
@media (max-width: 560px) {{ .pp-band-grid {{ grid-template-columns: 1fr; }} }}
.pp-band-card {{ background: #152B52; border: 1px solid #25406E; border-radius: 18px; padding: 30px 22px; text-align: center; }}
.pp-band-card .icon {{
    width: 60px; height: 60px; border-radius: 50%; background: #1E3A66; color: {GOLD};
    display: inline-flex; align-items: center; justify-content: center; font-size: 30px; margin-bottom: 16px;
}}
.pp-band-card h4 {{ color: #fff; margin: 0 0 8px; font-size: 1.08rem; }}
.pp-band-card p {{ color: #C4CBD8; margin: 0; font-size: 0.93rem; line-height: 1.55; }}

.pp-steps {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 28px; margin-top: 8px; }}
.pp-step {{ border-top: 2px solid {INK}; padding-top: 14px; }}
.pp-step .tag {{ color: {MUTED}; font-weight: 700; font-size: 0.85rem; }}
.pp-step .h {{ margin: 4px 0 6px; font-size: 1.15rem; font-weight: 800; color: {INK}; }}
.pp-step p {{ margin: 0; color: {MUTED}; line-height: 1.6; }}

.pp-check {{ list-style: none; padding: 0; margin: 0; }}
.pp-check li {{ padding: 8px 0 8px 24px; position: relative; color: {INK}; line-height: 1.6; border-bottom: 1px solid {LINE}; }}
.pp-check li:last-child {{ border-bottom: none; }}
.pp-check li::before {{ content: ""; position: absolute; left: 2px; top: 19px; width: 10px; height: 3px; background: {GOLD}; }}

[data-testid="stExpander"] details {{ border-radius: 14px; border-color: {LINE}; }}
[data-testid="stExpander"] summary p {{ font-weight: 700; font-size: 1.02rem; }}

.pp-footer {{ width: 100vw; margin-left: calc(50% - 50vw); background: #0A1830; color: #C4CBD8; padding: 44px 24px 30px; margin-top: 64px; }}
.pp-footer .wrap {{ max-width: 1180px; margin: 0 auto; }}
.pp-footer .logo {{ color: #fff; font-size: 1.4rem; font-weight: 800; margin: 0 0 6px; }}
.pp-footer a {{ color: #fff; }}
.pp-footer .cols {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 22px; }}
.pp-footer p {{ margin: 0 0 6px; font-size: 0.92rem; line-height: 1.7; }}
.pp-footer .fine {{ border-top: 1px solid #25406E; margin-top: 24px; padding-top: 16px; font-size: 0.8rem; color: #8D96A8; line-height: 1.6; }}
/* Motion and hover */
@keyframes ppRise {{ from {{ opacity: 0; transform: translateY(18px); }} to {{ opacity: 1; transform: none; }} }}
@keyframes ppFade {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
.pp-pair, .pp-callout, .pp-comps, .pp-facts, .pp-photo, .pp-reasons, .pp-stat, .pp-band-card, .pp-step {{
    animation: ppRise 0.7s cubic-bezier(.2,.7,.2,1) both; }}
.pp-comp, .pp-band-card, .pp-stat, .pp-pcard {{ transition: transform .25s ease, box-shadow .25s ease; }}
.pp-comp:hover, .pp-pcard:hover {{ transform: translateY(-5px); box-shadow: 0 16px 34px rgba(14,31,61,0.16); }}
.pp-band-card:hover {{ transform: translateY(-6px); border-color: {GOLD}; }}
.pp-stat:hover {{ transform: translateY(-3px); }}
[data-testid="stMain"], html {{ scroll-behavior: smooth; }}
[id^="pp-"] {{ scroll-margin-top: 90px; }}

/* Floating section bar (results) */
.pp-float {{
    position: fixed; left: 50%; bottom: 22px; transform: translateX(-50%); z-index: 1500;
    display: flex; gap: 4px; padding: 6px; border-radius: 999px; background: rgba(14,31,61,0.88);
    backdrop-filter: blur(10px); box-shadow: 0 14px 40px rgba(14,31,61,0.35); animation: ppFade .6s both;
    max-width: calc(100vw - 24px); overflow-x: auto;
}}
.pp-float a {{ color: #fff !important; text-decoration: none !important; font-weight: 700; font-size: 0.88rem;
              padding: 8px 14px; border-radius: 999px; white-space: nowrap; letter-spacing: 0.02em; }}
.pp-float a:hover {{ background: {GOLD}; color: {INK} !important; }}

/* Intro screen */
.st-key-splash {{
    position: fixed; inset: 0; z-index: 3000; display: flex; flex-direction: column; align-items: center;
    justify-content: center; gap: 0 !important; text-align: center; padding: 8vh 24px 0;
    background: linear-gradient(180deg, rgba(10,24,48,0.35) 0%, rgba(10,24,48,0.55) 50%, rgba(10,24,48,0.85) 100%),
                url('{HERO_PHOTO}') center 40%/cover;
    animation: ppFade 0.8s both;
}}
.st-key-splash [data-testid="stElementContainer"] {{ width: auto !important; display: flex; justify-content: center; }}
.pp-splash-mark {{ display: flex; align-items: center; justify-content: center; gap: 10px; color: #fff; font-weight: 700;
                  font-size: 1rem; margin-bottom: 18px; animation: ppRise .9s .1s both; }}
.pp-splash-mark .bar {{ width: 34px; height: 4px; background: {GOLD}; border-radius: 2px; }}
.pp-splash-title {{ font-family: 'Archivo', sans-serif; font-stretch: 115%; font-weight: 900; color: #fff;
                   font-size: clamp(3.2rem, 8.5vw, 7rem); line-height: 1.08; letter-spacing: -0.045em;
                   margin: 0 0 18px; padding-bottom: 0.06em; animation: ppRise 1s .2s both;
                   text-shadow: 0 4px 30px rgba(10,24,48,0.45); }}
.pp-splash-title span {{ color: {GOLD}; }}
.pp-splash-sub {{ color: rgba(255,255,255,0.92); font-size: clamp(1.05rem, 1.6vw, 1.3rem); line-height: 1.55; max-width: 600px;
                 margin: 0 auto 30px; animation: ppRise 1s .35s both; }}
.st-key-splash .stButton button {{ background: {GOLD}; color: {INK}; border: none; border-radius: 999px;
    padding: 0.85rem 2.2rem; font-weight: 800; font-size: 1.08rem; animation: ppRise 1s .5s both;
    box-shadow: 0 12px 34px rgba(0,0,0,0.3); transition: transform .2s ease, background .2s ease; }}
.st-key-splash .stButton button:hover {{ background: #fff; color: {BLUE}; transform: scale(1.04); }}
.st-key-splash .stButton button p {{ color: inherit; font-weight: 800; }}
.pp-splash-foot {{ position: fixed; bottom: 26px; left: 24px; right: 24px; text-align: center; color: rgba(255,255,255,0.7);
                  font-size: 0.88rem; animation: ppFade 1.2s .8s both; }}

/* Result header and estimate panel */
.pp-addr h2 {{ font-family: 'Archivo', sans-serif; font-stretch: 108%; font-size: clamp(1.6rem, 3.2vw, 2.3rem); font-weight: 800;
              letter-spacing: -0.035em; margin: 34px 0 2px; padding: 0; color: {INK}; }}
.pp-addr .hood {{ color: {MUTED}; font-size: 1rem; }}
.pp-tabs {{ display: flex; gap: 26px; border-bottom: 1px solid {LINE}; margin: 18px 0 22px; overflow-x: auto; }}
.pp-tabs a {{ color: {INK} !important; text-decoration: none !important; font-weight: 600; font-size: 0.95rem; padding: 10px 0;
             border-bottom: 3px solid transparent; white-space: nowrap; }}
.pp-tabs a:hover {{ border-bottom-color: {GOLD}; }}
.pp-hero-pic .pp-pic {{ border-radius: 12px; }}
.pp-est .k {{ color: {MUTED}; font-weight: 600; }}
.pp-est .v {{ font-family: 'Archivo', sans-serif; font-stretch: 110%; font-weight: 800; font-size: clamp(2.6rem, 5vw, 3.6rem);
             letter-spacing: -0.045em; color: {INK}; line-height: 1.05; margin: 2px 0 26px; }}
.pp-est .bar {{ position: relative; height: 8px; background: {LINE}; border-radius: 4px; }}
.pp-est .fill {{ position: absolute; top: 0; bottom: 0; background: {BLUE}; border-radius: 4px; opacity: 0.85; }}
.pp-est .pin {{ position: absolute; top: 50%; width: 18px; height: 18px; margin: -9px 0 0 -9px; border-radius: 50%;
               background: {GOLD}; border: 3px solid #fff; box-shadow: 0 1px 4px rgba(0,0,0,0.3); }}
.pp-est .tick {{ position: absolute; top: -7px; width: 2px; height: 22px; background: {INK}; }}
.pp-est .tick-lbl {{ position: absolute; top: -30px; transform: translateX(-50%); font-size: 0.75rem; color: {INK};
                    font-weight: 600; white-space: nowrap; }}
.pp-est .ends {{ display: flex; justify-content: space-between; font-size: 0.85rem; color: {MUTED}; margin-top: 8px; }}
.pp-est .ends span:first-child, .pp-est .ends span:last-child {{ color: {INK}; font-weight: 700; }}
.pp-est .range-note {{ color: {MUTED}; font-size: 0.8rem; margin-top: 4px; }}
.pp-est .facts {{ display: grid; grid-template-columns: repeat(4, 1fr); border-top: 1px solid {LINE}; border-bottom: 1px solid {LINE};
                 margin: 22px 0 12px; }}
.pp-est .facts div {{ padding: 12px 0; }}
.pp-est .facts div + div {{ padding-left: 14px; border-left: 1px solid {LINE}; }}
.pp-est .facts b {{ display: block; font-size: 1.25rem; color: {INK}; }}
.pp-est .facts span {{ color: {MUTED}; font-size: 0.85rem; }}
.pp-est .meta {{ color: {INK}; font-size: 0.92rem; line-height: 1.6; margin-bottom: 14px; }}
.pp-est .meta span {{ color: {MUTED}; font-size: 0.8rem; }}
.pp-compline {{ border-left: 4px solid {BLUE}; padding: 4px 0 4px 16px; margin: 26px 0 14px; color: {INK}; line-height: 1.65; }}

/* Notes and clickable cards */
.pp-note {{ max-width: 800px; margin: 10px auto 0; padding: 12px 18px; border-radius: 14px; background: #fff; color: {INK};
           border-left: 5px solid {GOLD}; box-shadow: 0 10px 30px rgba(8,12,20,0.18); position: relative; z-index: 5; }}
.st-key-pick_card {{ background: #fff; border: 1px solid {LINE}; border-radius: 18px; padding: 18px 22px;
                    box-shadow: 0 10px 30px rgba(14,31,61,0.07); }}
[class*="st-key-compcard_"] {{ position: relative; height: 100%; }}
[class*="st-key-compcard_"] [data-testid="stElementContainer"]:has(.stButton) {{ position: absolute; inset: 0; z-index: 4; margin: 0; }}
[class*="st-key-compcard_"] .stButton, [class*="st-key-compcard_"] .stButton button {{ width: 100%; height: 100%; }}
[class*="st-key-compcard_"] .stButton button {{ opacity: 0; cursor: pointer; }}
[class*="st-key-compcard_"]:hover .pp-comp {{ transform: translateY(-5px); box-shadow: 0 16px 34px rgba(14,31,61,0.16); border-color: {GOLD}; }}
[class*="st-key-compcard_"]:hover .pp-pic img {{ transform: scale(1.06); }}
.pp-comp {{ margin-bottom: 20px; }}
.pp-comp .top.light {{ background: {GOLD_TINT}; color: {BLUE}; font-weight: 700; font-size: 0.9rem; }}
.pp-comp .go {{ margin-top: 10px; color: {BLUE}; font-weight: 700; font-size: 0.9rem; }}

/* Audience cards and notes (About) */
.pp-cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 16px; }}
.pp-cards .c {{ background: #fff; border: 1px solid {LINE}; border-radius: 16px; padding: 22px; }}
.pp-cards .c .material-symbols-rounded {{ color: {BLUE}; font-size: 30px; }}
.pp-cards .c h4 {{ margin: 10px 0 6px; font-family: 'Archivo', sans-serif; font-stretch: 108%; font-size: 1.15rem; }}
.pp-cards .c p {{ margin: 0; color: {MUTED}; line-height: 1.6; }}
.pp-notes {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 0; background: {PAPER};
            border-radius: 16px; }}
.pp-notes div {{ padding: 18px 22px; color: {INK}; line-height: 1.6; border-left: 1px solid {LINE}; }}
.pp-notes div:first-child {{ border-left: none; }}
.pp-notes b {{ display: block; margin-bottom: 4px; }}

/* What-if */
.st-key-whatif {{ background: #fff; border: 1px solid {LINE}; border-radius: 22px; padding: 22px 26px;
                 box-shadow: 0 10px 30px rgba(14,31,61,0.07); }}
</style>
"""


def setup():
    st.markdown(CSS, unsafe_allow_html=True)


def navbar(home, links, saved_page=None, current=None, cta_label="Get my estimate"):
    """Branded top bar. `home`, `links`, `saved_page` and `current` are st.Page objects."""
    from core import account

    if current is not None and current.title == home.title:
        # On the estimate page itself: darker gold with a navy ring, like the grey pill on other pages.
        st.markdown(f"""<style>.st-key-nav_cta [data-testid="stPageLink"] a {{ background: {GOLD_DARK} !important;
            box-shadow: inset 0 0 0 2px {BLUE} !important; }}</style>""", unsafe_allow_html=True)

    with st.container(key="navbar"):
        cols = st.columns(len(links) + 4, vertical_alignment="center")
        with cols[0]:
            with st.container(key="nav_logo"):
                st.page_link(home, label=APP_NAME, icon=":material/home:")
        for col, page in zip(cols[2:-2], links):
            with col:
                st.page_link(page)
        with cols[-2]:
            with st.container(key="nav_account"):
                if account.signed_in():
                    with st.popover(account.first_name(), icon=":material/account_circle:"):
                        st.caption(f"Signed in as {account.email()}")
                        st.page_link(saved_page, label="Saved homes", icon=":material/favorite:")
                        if st.button("Sign out", icon=":material/logout:", key="sign_out"):
                            st.session_state.clear()
                            st.logout()
                elif account.enabled():
                    if st.button("Sign in", key="sign_in", icon=":material/account_circle:"):
                        st.login()
        with cols[-1]:
            with st.container(key="nav_cta"):
                st.page_link(home, label=cta_label)


def hero(title, subtitle, compact=False, home=False):
    extra = " pp-compact" if compact else (" pp-home" if home else "")
    st.markdown(f'<div class="pp-hero{extra}"><h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)


def section(title, subtitle=None, eyebrow=None, anchor=None):
    eyebrow_html = f'<div class="pp-eyebrow">{eyebrow}</div>' if eyebrow else ""
    if anchor:
        eyebrow_html = f'<div id="pp-{anchor}"></div>' + eyebrow_html
    sub = f'<div class="pp-section-sub">{subtitle}</div>' if subtitle else ""
    top = ' style="margin-top:6px"' if eyebrow else ""
    st.markdown(f'{eyebrow_html}<div class="pp-section-title"{top}>{title}</div>{sub}', unsafe_allow_html=True)


def splash(home_count, sale_count, last_sale):
    """Full-screen intro shown once per visit, in the spirit of a product launch page."""
    with st.container(key="splash"):
        st.markdown('<div class="pp-splash-mark"><span class="bar"></span>Philadelphia, PA</div>'
                    '<div class="pp-splash-title">Philly<span>Price</span></div>'
                    '<div class="pp-splash-sub">Know what any Philadelphia home is worth, from the city\'s own '
                    'sales records. Free to use, no account needed.</div>', unsafe_allow_html=True)
        started = st.button("Get started  →", key="start_button")
        st.markdown(f'<div class="pp-splash-foot">{home_count:,} homes · {sale_count:,} recorded sales · Sales through {last_sale:%B %Y}</div>',
                    unsafe_allow_html=True)
    return started


def floating_nav(items):
    links = "".join(f'<a href="#pp-{anchor}">{label}</a>' for anchor, label in items)
    st.markdown(f'<nav class="pp-float">{links}</nav>', unsafe_allow_html=True)


def stat_cards(items, columns=None):
    cols = st.columns(columns or len(items))
    for i, (value, label) in enumerate(items):
        cols[i % len(cols)].markdown(f'<div class="pp-stat" style="margin-bottom:12px"><div class="v">{value}</div>'
                                     f'<div class="l">{label}</div></div>', unsafe_allow_html=True)


def feature_band():
    cards = [
        ("sell", "A suggested list price", "From a model trained on 107,321 Philadelphia home sales."),
        ("swap_vert", "A realistic price range", "Prices are never exact, so you see a low and a high end too."),
        ("home_work", "Homes that sold nearby", "Recent sales close by with a similar size, to check the estimate."),
        ("lightbulb", "The reasons, in plain words", "What pushed the price up and what pulled it down."),
    ]
    items = "".join(
        f'<div class="pp-band-card"><span class="icon material-symbols-rounded">{icon}</span>'
        f'<h4>{title}</h4><p>{text}</p></div>'
        for icon, title, text in cards
    )
    st.markdown(f'<div class="pp-band"><h2>Price a Philly home like a pro, even if it\'s your first time</h2>'
                f'<div class="pp-band-grid">{items}</div></div>', unsafe_allow_html=True)


def steps(items):
    html = "".join(
        f'<div class="pp-step"><span class="tag">{i:02d}</span><div class="h">{title}</div><p>{text}</p></div>'
        for i, (title, text) in enumerate(items, start=1)
    )
    st.markdown(f'<div class="pp-steps">{html}</div>', unsafe_allow_html=True)


def cards(items):
    """Equal-height cards: (icon, title, text)."""
    st.markdown('<div class="pp-cards">' + "".join(
        f'<div class="c"><span class="material-symbols-rounded">{i}</span><h4>{t}</h4><p>{x}</p></div>'
        for i, t, x in items) + "</div>", unsafe_allow_html=True)


def notes(items):
    """A single strip of short (title, text) notes side by side."""
    st.markdown('<div class="pp-notes">' + "".join(f"<div><b>{t}</b>{x}</div>" for t, x in items) + "</div>",
                unsafe_allow_html=True)


def checklist(items):
    st.markdown('<ul class="pp-check">' + "".join(f"<li>{i}</li>" for i in items) + "</ul>",
                unsafe_allow_html=True)


def footer():
    st.markdown(f"""
<div class="pp-footer"><div class="wrap">
  <div class="cols">
    <div><div class="logo">{APP_NAME}</div><p>{TAGLINE}. Free estimates for single-family homes,
      built on the city's public sales records.</p></div>
    <div><p><b style="color:#fff">Explore</b></p>
      <p><a href="/" target="_self">Get an estimate</a><br><a href="/find_homes" target="_self">Find homes</a><br>
      <a href="/market_map" target="_self">Market map</a><br>
      <a href="/price_trends" target="_self">Price trends</a><br><a href="/how_it_works" target="_self">How it works</a><br>
      <a href="/about" target="_self">About</a><br><a href="/privacy" target="_self">Privacy</a> ·
      <a href="/terms" target="_self">Terms</a></p></div>
    <div><p><b style="color:#fff">Data</b></p>
      <p><a href="https://opendataphilly.org/datasets/philadelphia-properties-and-assessment-history/" target="_blank">OpenDataPhilly property sales</a><br>
      <a href="https://data.census.gov/" target="_blank">U.S. Census Bureau ACS 2024</a><br>
      <a href="https://fred.stlouisfed.org/series/MORTGAGE30US" target="_blank">FRED mortgage rates</a></p></div>
  </div>
  <div class="fine">Estimates are for informational purposes only. {APP_NAME} does not provide appraisals, brokerage
  services, or investment advice. Talk to a licensed real estate professional before making a buying or selling decision.
  <br>© 2026 {APP_NAME} · {PHOTO_CREDIT} · Map tiles © CARTO, © OpenStreetMap contributors.</div>
</div></div>
""", unsafe_allow_html=True)


def money(value):
    return f"${value:,.0f}"


def money_short(value):
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    return f"${value / 1000:,.0f}K"
