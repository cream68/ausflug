# app/overview_section.py
from __future__ import annotations

from typing import List

import folium
import streamlit as st

from data import locations_home, locations_trip, winner_id
from lib.map_utils import add_default_plugins, fit_bounds, force_fit_on_mount, new_map, render_map


def render_startpage() -> None:
    st.markdown("""
    Willkommen zur Planung unseres kleinen Ausflugs zwischen **Wiesloch** und **Reutte**!  
    Jede*r kann Vorschläge einbringen: Städte, Wanderungen, Restaurants, Sehenswürdigkeiten.

    📲 einfach per WhatsApp an **Mark** schicken – gerne mit Link oder kurzer Beschreibung.

    **Plappermaulpaul** hat sich bereits freiwillig als unser ehrenwerter gruppenguide gemeldet.  
    Er verspricht, uns mit viel Fachwissen (und mindestens genauso viel halbwissen) sicher durchs Tagesprogramm zu führen – auch fernab der römischen Geschichte.
    """)

    trip_name, trip_center = locations_trip[winner_id]
    m = new_map(trip_center, zoom=7)
    add_default_plugins(m)

    fg_homes = folium.FeatureGroup(name="🏠 Startorte", show=True).add_to(m)
    fg_dest  = folium.FeatureGroup(name="📍 Ziel", show=True).add_to(m)

    HOME_ICON = "https://cdn-icons-png.flaticon.com/512/25/25694.png"
    DEST_ICON = "https://cdn-icons-png.flaticon.com/512/684/684908.png"

    all_coords: List[List[float]] = []
    for city, (lat, lon) in locations_home.items():
        folium.Marker(
            [lat, lon],
            popup=city,
            icon=folium.CustomIcon(HOME_ICON, icon_size=(40,40), icon_anchor=(20,40))
        ).add_to(fg_homes)
        all_coords.append([lat, lon])

    lat, lon = trip_center
    folium.Marker(
        [lat, lon],
        icon=folium.DivIcon(html=f'<div style="width:160px;margin-top:-30px;margin-left:26px;font-weight:600">{trip_name}</div>')
    ).add_to(m)
    folium.Marker(
        [lat, lon],
        popup=trip_name,
        icon=folium.CustomIcon(DEST_ICON, icon_size=(40,40), icon_anchor=(20,40))
    ).add_to(fg_dest)
    all_coords.append([lat, lon])

    # folium.LayerControl(collapsed=False).add_to(m)
    fit_bounds(m, all_coords, max_zoom=7)
    # Ensure bounds are re-applied after the map iframe mounts (fixes "not all markers visible")
    force_fit_on_mount(m, all_coords, max_zoom=12, padding_px=32)

    render_map(m, key="overview_start")
