# app_overview.py
from __future__ import annotations

from typing import List

import folium
from folium import plugins
import pandas as pd  # (optional; safe to remove if unused)
import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo

# Prefer st_folium if available (more features), fall back to folium_static
try:
    from streamlit_folium import st_folium as _st_render_map
    _RENDER_ARGS = dict(returned_objects=[], use_container_width=True, height=650)
except Exception:
    from streamlit_folium import folium_static as _st_render_map  # type: ignore
    _RENDER_ARGS = {}

from data import locations_home, locations_trip, winner_id
trip_name, trip_center = locations_trip[winner_id]

# --- Page ---------------------------------------------------------------------
def render_startpage():
    st.markdown(f"""
    Willkommen zur Planung unseres kleinen Ausflugs zwischen **Wiesloch** und **Reutte**!  
    Jede*r kann Vorschläge einbringen: Städte, Wanderungen, Restaurants, Sehenswürdigkeiten.

    📲 einfach per WhatsApp an **Mark** schicken – gerne mit Link oder kurzer Beschreibung.

    **Plappermaulpaul** hat sich bereits freiwillig als unser ehrenwerter gruppenguide gemeldet.  
    Er verspricht, uns mit viel Fachwissen (und mindestens genauso viel halbwissen) sicher durchs Tagesprogramm zu führen – auch fernab der römischen Geschichte.

    ---
    """)
    # --- Map (CartoDB Light only) --------------------------------------------
    m = folium.Map(location=trip_center, zoom_start=7, tiles="CartoDB Positron", control_scale=True)

    # Plugins for UX
    plugins.Fullscreen(position="topright").add_to(m)
    plugins.LocateControl(auto_start=False).add_to(m)
    plugins.MeasureControl(primary_length_unit="kilometers").add_to(m)
    plugins.MiniMap(toggle_display=True).add_to(m)
    plugins.MousePosition(separator=" | ", position="bottomleft").add_to(m)

    # Feature groups
    fg_homes = folium.FeatureGroup(name="🏠 startorte", show=True).add_to(m)
    fg_dest = folium.FeatureGroup(name="📍 ziel", show=True).add_to(m)

    # Collect bounds
    all_coords: List[List[float]] = []

    # Home markers (custom icon)
    HOME_ICON = "https://cdn-icons-png.flaticon.com/512/25/25694.png"
    DEST_ICON = "https://cdn-icons-png.flaticon.com/512/684/684908.png"

    for city, (lat, lon) in locations_home.items():
        folium.Marker(
            location=[lat, lon],
            popup=city,
            icon=folium.CustomIcon(icon_image=HOME_ICON, icon_size=(40, 40), icon_anchor=(20, 40)),
        ).add_to(fg_homes)
        all_coords.append([lat, lon])

    # Destination label + marker
    lat, lon = trip_center
    folium.Marker(
        [lat, lon],
        icon=folium.DivIcon(
            html=f"""
            <div style="
                width: 160px; text-align: left; font-size: 12px; font-weight: 600;
                color: #111; margin-top: -30px; margin-left: 26px; text-shadow: 0 1px 0 #fff;
                white-space: nowrap;
            ">{trip_name}</div>
            """
        ),
    ).add_to(m)

    folium.Marker(
        location=[lat, lon],
        popup=trip_name,  # fixed: was 'city' before
        icon=folium.CustomIcon(icon_image=DEST_ICON, icon_size=(40, 40), icon_anchor=(20, 40)),
    ).add_to(fg_dest)
    all_coords.append([lat, lon])

    # Layers + fit bounds
    folium.LayerControl(collapsed=False).add_to(m)
    if all_coords:
        m.fit_bounds(all_coords, max_zoom=10)


    _st_render_map(m, key="start", **_RENDER_ARGS)
