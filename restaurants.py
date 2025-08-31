# restaurants_section.py
from __future__ import annotations

from typing import List, Optional, Tuple

import folium
from folium import plugins
import pandas as pd
import streamlit as st

from streamlit_folium import st_folium as _st_render_map
_RENDER_ARGS = dict(returned_objects=[], use_container_width=True, height=650)

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.distance import geodesic

from data import locations_trip, restaurants, winner_id, camping

# --- Icons / helpers ----------------------------------------------------------
CAMP_ICON_URL = "https://cdn-icons-png.flaticon.com/512/9173/9173952.png"
CAMP_ICON_SIZE = (40, 40)
CAMP_ICON_ANCHOR = (20, 40)  # bottom-center

def add_label(map_obj: folium.Map, lat: float, lon: float, text: str) -> None:
    folium.Marker(
        location=[lat, lon],
        icon=folium.DivIcon(
            html=f"""
            <div style="
                width: 160px; text-align: left; font-size: 12px; font-weight: 600;
                color: #111; margin-top: -30px; margin-left: 26px; text-shadow: 0 1px 0 #fff;
                white-space: nowrap;
            ">{text}</div>
            """
        ),
        z_index_offset=1000,
    ).add_to(map_obj)

# --- Geocoding (cached + respectful) -----------------------------------------
def _new_geocoder() -> Nominatim:
    return Nominatim(user_agent="restaurant-mapper/1.0 (streamlit)", timeout=5)

@st.cache_data(show_spinner=False, ttl=60 * 60 * 24)  # 24h cache
def geocode_one(address: str) -> Optional[Tuple[float, float]]:
    geocoder = _new_geocoder()
    safe_geocode = RateLimiter(geocoder.geocode, min_delay_seconds=1, swallow_exceptions=True)
    loc = safe_geocode(address)
    if not loc:
        return None
    return (float(loc.latitude), float(loc.longitude))

# --- Public API ---------------------------------------------------------------
def render_restaurants(
    selected_trip_id: Optional[int] = None,
    *,
    show_camp_labels: bool = False,
) -> None:
    """
    Render the Restaurants + Camping section (map, metrics, tables).
    Safe to call inside a Streamlit tab. Does NOT set page title or page config.
    """
    trip_id = selected_trip_id if selected_trip_id is not None else winner_id
    trip_name, trip_center = locations_trip[trip_id]
    trip_RESTS = [r.copy() for r in restaurants if r.get("trip_id") == trip_id]
    trip_CAMPS = [c.copy() for c in camping if c.get("trip_id") == trip_id]

    # --- Map (CartoDB Light only) --------------------------------------------
    m = folium.Map(location=trip_center, zoom_start=10, tiles="CartoDB Positron", control_scale=True)

    # Plugins for UX
    plugins.Fullscreen(position="topright").add_to(m)
    plugins.LocateControl(auto_start=False).add_to(m)
    plugins.MeasureControl(primary_length_unit="kilometers").add_to(m)
    plugins.MiniMap(toggle_display=True).add_to(m)
    plugins.MousePosition(separator=" | ", position="bottomleft").add_to(m)

    # Feature groups
    fg_camps = folium.FeatureGroup(name="🏕️ Camping", show=True).add_to(m)
    fg_rest = folium.FeatureGroup(name="🍴 Restaurants", show=True).add_to(m)

    # Cluster layer for restaurants
    clu_rest = plugins.MarkerCluster(name="Restaurants Cluster", show=True)
    clu_rest.add_to(fg_rest)

    # --- Collect bounds -------------------------------------------------------
    all_coords: List[List[float]] = [list(trip_center)]

    # --- Camping markers ------------------------------------------------------
    for camp in trip_CAMPS:
        lat, lon = float(camp.get("lat", 0)), float(camp.get("lon", 0))
        if not lat and not lon:
            continue
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(f"<b>{camp.get('name','')}</b>", max_width=250),
            icon=folium.CustomIcon(CAMP_ICON_URL, icon_size=CAMP_ICON_SIZE, icon_anchor=CAMP_ICON_ANCHOR),
            z_index_offset=0,
        ).add_to(fg_camps)
        if show_camp_labels:
            add_label(m, lat, lon, camp.get("name", ""))
        all_coords.append([lat, lon])

    # --- Geocode restaurants + add markers -----------------------------------
    failed_geocodes: List[str] = []
    progress = st.progress(0, text="Geocoding Restaurants …")
    N = max(len(trip_RESTS), 1)

    for i, r in enumerate(trip_RESTS, start=1):
        addr = r.get("address", "")
        coords = geocode_one(addr) if addr else None

        if not coords:
            r["lat"], r["lon"] = None, None
            failed_geocodes.append(r.get("name", ""))
            progress.progress(i / N, text=f"Geocoding Restaurants … ({i}/{len(trip_RESTS)})")
            continue

        lat, lon = coords
        r["lat"], r["lon"] = lat, lon

        html_popup = f"""
            <div style='font-size: 14px; max-width: 260px'>
                <b>{r.get('name','')}</b><br>
                <p style="margin: 6px 0">{r.get('description','')}</p>
                <a href="{r.get('gmap_url','#')}" target="_blank">📍 Auf Google Maps öffnen</a>
            </div>
        """
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(html_popup, max_width=300),
            icon=folium.Icon(icon="cutlery", prefix="fa", color="red"),
        ).add_to(clu_rest)

        all_coords.append([lat, lon])
        progress.progress(i / N, text=f"Geocoding Restaurants … ({i}/{len(trip_RESTS)})")
    progress.empty()

    if failed_geocodes:
        with st.expander(f"⚠️ {len(failed_geocodes)} Restaurants konnten nicht geocoded werden (anzeigen)"):
            for n in failed_geocodes:
                st.write(f"- {n}")

    folium.LayerControl(collapsed=False).add_to(m)

    # Fit bounds smartly (includes camps + restaurants)
    if all_coords:
        m.fit_bounds(all_coords, max_zoom=15)
    else:
        m.location = trip_center
        m.zoom_start = 13

    # Render map
    _st_render_map(m,key="restaurants", **_RENDER_ARGS)

    st.subheader("Restaurant-Liste")
    df_rests = pd.DataFrame([
        {
            "Name": r.get("name", ""),
            "Beschreibung": r.get("description", ""),
            "Google Maps": r.get("gmap_url", ""),
        }
        for r in trip_RESTS
    ])
    st.dataframe(
        df_rests,
        use_container_width=True,
        column_config={
            "Google Maps": st.column_config.LinkColumn("Google Maps", display_text="📍 Link"),
        },
    )
    st.download_button(
        "Restaurants als CSV herunterladen",
        df_rests.to_csv(index=False).encode("utf-8"),
        file_name="restaurants.csv",
        mime="text/csv",
    )
