"""
Pictures of a home for cards and the estimate page.

Where a photo comes from, in order:
1. Google Street View, if the secret GOOGLE_MAPS_API_KEY is set (Street View Static API enabled).
2. Mapillary street-level photos (free, CC BY-SA), if the secret MAPILLARY_TOKEN is set.
3. Otherwise a small OpenStreetMap street map with the home pinned.
Photos are fetched on the server, so keys never appear in the page.
"""

import base64
import math

import requests
import streamlit as st

STREET_VIEW = "https://maps.googleapis.com/maps/api/streetview"
MAPILLARY = "https://graph.mapillary.com/images"


def secret(name):
    try:
        return st.secrets.get(name)
    except Exception:
        return None


def api_key():
    return secret("GOOGLE_MAPS_API_KEY")


def _bearing(lat1, lon1, lat2, lon2):
    """Compass direction in degrees from point 1 to point 2."""
    phi1, phi2, dl = math.radians(lat1), math.radians(lat2), math.radians(lon2 - lon1)
    x = math.sin(dl) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dl)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


@st.cache_data(show_spinner=False, ttl=24 * 3600, max_entries=5000)
def mapillary_jpeg(lat, lon):
    """The Mapillary photo closest to the home that faces it, or None."""
    token = secret("MAPILLARY_TOKEN")
    if not token:
        return None
    box = 0.0006  # about 60 meters each way
    try:
        found = requests.get(MAPILLARY, params={
            "access_token": token, "fields": "id,thumb_1024_url,compass_angle,computed_geometry,is_pano",
            "bbox": f"{lon - box},{lat - box},{lon + box},{lat + box}", "limit": 50}, timeout=10).json().get("data", [])
        best, best_score = None, None
        for image in found:
            geometry = image.get("computed_geometry") or {}
            if image.get("is_pano") or not image.get("thumb_1024_url") or "coordinates" not in geometry:
                continue
            ilon, ilat = geometry["coordinates"]
            meters = math.hypot((ilat - lat) * 111_000, (ilon - lon) * 85_000)
            facing = abs((_bearing(ilat, ilon, lat, lon) - (image.get("compass_angle") or 0) + 180) % 360 - 180)
            if facing > 120:
                continue
            score = meters + facing * 0.15
            if best_score is None or score < best_score:
                best, best_score = image, score
        if best is None:
            return None
        photo = requests.get(best["thumb_1024_url"], timeout=12)
        return photo.content if photo.ok else None
    except (requests.RequestException, ValueError):
        return None


def street_view_jpeg(lat, lon, size="480x300"):
    """Street View photo bytes looking straight at the home, or None when there is no key or no imagery."""
    key = api_key()
    return _street_view_jpeg(lat, lon, size, key) if key else None


@st.cache_data(show_spinner=False, ttl=7 * 24 * 3600, max_entries=5000)
def _street_view_jpeg(lat, lon, size, key):
    location = f"{lat:.6f},{lon:.6f}"
    try:
        meta = requests.get(f"{STREET_VIEW}/metadata", params={"location": location, "radius": 40,
                                                               "source": "outdoor", "key": key}, timeout=8).json()
        if meta.get("status") != "OK":
            return None
        # Stand where the street photo was taken and turn to face the home, zoomed in on its front.
        cam = meta["location"]
        heading = _bearing(cam["lat"], cam["lng"], lat, lon)
        image = requests.get(STREET_VIEW, params={"size": size, "pano": meta["pano_id"], "heading": f"{heading:.1f}",
                                                  "fov": 60, "pitch": 8, "key": key}, timeout=12)
        return image.content if image.ok else None
    except (requests.RequestException, ValueError, KeyError):
        return None


def map_thumbnail_style(lat, lon, zoom=18):
    """CSS background that draws 5x3 OpenStreetMap tiles with the home in the center."""
    n = 2 ** zoom
    x_float = (lon + 180) / 360 * n
    y_float = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    x, y = int(x_float), int(y_float)
    px, py = (x_float - x) * 256, (y_float - y) * 256
    images, positions = [], []
    for dy in (-1, 0, 1):
        for dx in (-2, -1, 0, 1, 2):
            images.append(f"url('https://tile.openstreetmap.org/{zoom}/{x + dx}/{y + dy}.png')")
            positions.append(f"calc(50% + {dx * 256 - px:.0f}px) calc(50% + {dy * 256 - py:.0f}px)")
    return (f"background-image:{','.join(images)};background-position:{','.join(positions)};"
            "background-size:256px 256px;background-repeat:no-repeat;")


def photo_bytes(lat, lon):
    """(photo bytes, credit HTML) from Street View or Mapillary, or (None, "")."""
    lat, lon = round(float(lat), 6), round(float(lon), 6)
    photo = street_view_jpeg(lat, lon)
    if photo:
        return photo, ""
    photo = mapillary_jpeg(lat, lon)
    return (photo, '<span class="credit">© Mapillary, CC BY-SA</span>') if photo else (None, "")


def has_photos(points):
    """For a list of (lat, lon), whether each home has a photo. Looks them up in parallel."""
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=12) as pool:
        return list(pool.map(lambda p: photo_bytes(*p)[0] is not None, points))


def picture_html(lat, lon, height=150):
    """HTML block with the home's photo, or a pinned map when no photo is available."""
    photo, credit = photo_bytes(lat, lon)
    if photo:
        encoded = base64.b64encode(photo).decode()
        return (f'<div class="pp-pic" style="height:{height}px">'
                f'<img src="data:image/jpeg;base64,{encoded}" alt="Street-level photo near the home">{credit}</div>')
    return f'<div class="pp-pic map" style="height:{height}px;{map_thumbnail_style(float(lat), float(lon))}"></div>'
