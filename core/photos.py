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
import re
import string

import numpy as np
import pandas as pd
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


def street_address(address, zip_code=None):
    """'2426 S CHADWICK ST' -> '2426 S Chadwick St, Philadelphia, PA 19145', for Google to find the front door."""
    if not isinstance(address, str) or not address.strip():
        return None
    text = string.capwords(address.strip().lower())
    if "philadelphia" in text.lower():
        return text
    try:
        return f"{text}, Philadelphia, PA {int(float(zip_code))}"
    except (TypeError, ValueError):
        return f"{text}, Philadelphia, PA"


def street_view_jpeg(lat, lon, size="480x300", address=None):
    """Street View photo bytes looking straight at the home, or None when there is no key or no imagery."""
    key = api_key()
    return _street_view_jpeg(lat, lon, size, key, address) if key else None


@st.cache_resource(show_spinner=False)
def _street_rows():
    """Every home's location, grouped by street and side of the street (odd or even house numbers)."""
    from core import insights as ins            # here, not at the top, so the two modules don't import each other
    homes = ins.load_homes()
    parts = homes["address"].str.extract(r"^(\d+)\s+(.+)$")
    rows = pd.DataFrame({"num": pd.to_numeric(parts[0], errors="coerce"), "street": parts[1],
                         "lat": homes["lat"], "lon": homes["lon"]}).dropna()
    return {key: g[["num", "lat", "lon"]].to_numpy()
            for key, g in rows.groupby([rows["street"], rows["num"] % 2])}


def _front_target(address, lat, lon, cam_lat, cam_lon):
    """Where the camera should look: the home's front wall, worked out from the line of homes on its side of the
    street. Returns (east, north) in meters from the camera, or None when the street can't be worked out."""
    m = re.match(r"\s*(\d+)\s+([^,]+)", address or "")
    if not m:
        return None
    num, street = int(m.group(1)), m.group(2).strip().upper()
    rows = _street_rows().get((street, num % 2))
    if rows is None:
        return None
    near = rows[np.abs(rows[:, 0] - num) <= 40]
    if len(near) < 3:
        return None
    xy = np.column_stack([(near[:, 2] - lon) * 85_000, (near[:, 1] - lat) * 111_000])   # meters, home at 0,0
    along_dir = np.linalg.svd(xy - xy.mean(axis=0))[2][0]                              # which way the street runs
    across_dir = np.array([-along_dir[1], along_dir[0]])
    cam = np.array([(cam_lon - lon) * 85_000, (cam_lat - lat) * 111_000])
    along, across = -cam @ along_dir, -cam @ across_dir   # home position seen from the camera
    if abs(across) < 2:
        return None
    # The home's map point sits in the middle of the lot; its front wall is a few meters closer to the street.
    front = math.copysign(min(max(abs(across) - 7, 3.5), 10), across)
    target = along * along_dir + front * across_dir
    return float(target[0]), float(target[1])


@st.cache_data(show_spinner=False, ttl=7 * 24 * 3600, max_entries=5000)
def _street_view_jpeg(lat, lon, size, key, address=None):
    try:
        meta = requests.get(f"{STREET_VIEW}/metadata", params={"location": f"{lat:.6f},{lon:.6f}", "radius": 40,
                                                               "source": "outdoor", "key": key}, timeout=8).json()
        # Only Google's own Street View cars: photo spheres uploaded by people are often far from the house.
        if meta.get("status") != "OK" or "Google" not in meta.get("copyright", ""):
            return None
        cam = meta["location"]
        target = _front_target(address, lat, lon, cam["lat"], cam["lng"]) if address else None
        if target is None:     # no street to go by: look at the home's map point
            target = ((lon - cam["lng"]) * 85_000, (lat - cam["lat"]) * 111_000)
        heading = (math.degrees(math.atan2(target[0], target[1])) + 360) % 360
        # Zoom so about 16 m of front fits: the home in the middle with its neighbors, never tighter than 60 degrees
        # (a tight zoom from far down the block shows only side walls).
        fov = min(90, max(60, 2 * math.degrees(math.atan(8 / max(math.hypot(*target), 1)))))
        image = requests.get(STREET_VIEW, params={"size": size, "pano": meta["pano_id"], "heading": f"{heading:.1f}",
                                                  "fov": f"{fov:.0f}", "pitch": 10, "key": key}, timeout=12)
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


def photo_bytes(lat, lon, address=None):
    """(photo bytes, credit HTML) from Street View or Mapillary, or (None, "")."""
    lat, lon = round(float(lat), 6), round(float(lon), 6)
    photo = street_view_jpeg(lat, lon, address=address)
    if photo:
        return photo, ""
    photo = mapillary_jpeg(lat, lon)
    return (photo, '<span class="credit">© Mapillary, CC BY-SA</span>') if photo else (None, "")


def has_photos(points):
    """For a list of (lat, lon) or (lat, lon, address), whether each home has a photo. Looks them up in parallel."""
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=12) as pool:
        return list(pool.map(lambda p: photo_bytes(*p)[0] is not None, points))


def picture_html(lat, lon, height=150, address=None):
    """HTML block with the home's photo, or a pinned map when no photo is available."""
    photo, credit = photo_bytes(lat, lon, address)
    if photo:
        encoded = base64.b64encode(photo).decode()
        return (f'<div class="pp-pic" style="height:{height}px">'
                f'<img src="data:image/jpeg;base64,{encoded}" alt="Street-level photo near the home">{credit}</div>')
    return f'<div class="pp-pic map" style="height:{height}px;{map_thumbnail_style(float(lat), float(lon))}"></div>'
