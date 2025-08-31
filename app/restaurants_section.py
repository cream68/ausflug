# app/restaurants_section.py
from __future__ import annotations

from typing import List, Optional, Tuple

import folium
import pandas as pd
import streamlit as st
from folium import plugins

from data import camping, locations_trip, restaurants, winner_id
from lib.geocode import geocode_one
from lib.map_utils import (
    add_default_plugins,
    fit_bounds,
    force_fit_on_mount,
    new_map,
    render_map,
)
from lib.session import unique_map_key

# --- Icons / constants --------------------------------------------------------
CAMP_ICON_URL = "https://cdn-icons-png.flaticon.com/512/9173/9173952.png"
CAMP_ICON_SIZE = (40, 40)
CAMP_ICON_ANCHOR = (20, 40)
MAX_ZOOM = 15


def popup_html(name: str, desc: str, gmap_url: str) -> str:
    return (
        "<div style='max-width:250px'>"
        f"<b>{name}</b><br>"
        f"<span style='font-size:12px'>{desc}</span><br>"
        f"<a href='{gmap_url}' target='_blank'>📍 Auf Google Maps öffnen</a>"
        "</div>"
    )


def render_restaurants(selected_trip_id: Optional[int] = None, *, page_id: str = "restaurants") -> None:
    trip_id = selected_trip_id if selected_trip_id is not None else winner_id
    trip_name, trip_center = locations_trip[trip_id]
    trip_rests = [r.copy() for r in restaurants if r.get("trip_id") == trip_id]
    trip_camps = [c.copy() for c in camping    if c.get("trip_id") == trip_id]

    # Center: mean of camp coords if present, else trip center
    camp_points: List[Tuple[float, float]] = [
        (float(c["lat"]), float(c["lon"]))
        for c in trip_camps if c.get("lat") and c.get("lon")
    ]
    if camp_points:
        clat = sum(p[0] for p in camp_points) / len(camp_points)
        clon = sum(p[1] for p in camp_points) / len(camp_points)
        m = new_map((clat, clon), zoom=12 if len(camp_points) == 1 else 11)
    else:
        m = new_map(trip_center, zoom=10)

    add_default_plugins(m)

    # Layers
    fg_camps = folium.FeatureGroup(name="🏕️ Camping", show=True).add_to(m)
    fg_rest  = folium.FeatureGroup(name="🍴 Restaurants", show=True).add_to(m)
    clu_rest = plugins.MarkerCluster(name="Restaurants Cluster", show=True)
    clu_rest.add_to(fg_rest)

    # Collect bounds
    points: List[List[float]] = [list(m.location)]

    # Camps
    for c in trip_camps:
        lat, lon = float(c["lat"]), float(c["lon"])
        folium.Marker(
            [lat, lon],
            popup=folium.Popup(f"<b>{c.get('name','')}</b>", max_width=250),
            icon=folium.CustomIcon(CAMP_ICON_URL, icon_size=CAMP_ICON_SIZE, icon_anchor=CAMP_ICON_ANCHOR),
        ).add_to(fg_camps)
        points.append([lat, lon])

    # Restaurants (geocode)
    failed: List[str] = []
    prog = st.progress(0, text="Geocoding Restaurants …")
    N = max(len(trip_rests), 1)

    for i, r in enumerate(trip_rests, start=1):
        coords = geocode_one(r.get("address", "")) if r.get("address") else None
        if not coords:
            r["lat"], r["lon"] = None, None
            failed.append(r.get("name", ""))
            prog.progress(i / N, text=f"Geocoding Restaurants … ({i}/{len(trip_rests)})")
            continue

        lat, lon = coords
        r["lat"], r["lon"] = lat, lon

        folium.Marker(
            [lat, lon],
            popup=folium.Popup(popup_html(r.get("name",""), r.get("description",""), r.get("gmap_url","#")), max_width=300),
            icon=folium.Icon(icon="cutlery", prefix="fa", color="red"),
        ).add_to(clu_rest)
        points.append([lat, lon])
        prog.progress(i / N, text=f"Geocoding Restaurants … ({i}/{len(trip_rests)})")
    prog.empty()

    if failed:
        with st.expander(f"⚠️ {len(failed)} Restaurants konnten nicht geocoded werden (anzeigen)"):
            for n in failed:
                st.write(f"- {n}")

    folium.LayerControl(collapsed=False).add_to(m)
    fit_bounds(m, points, max_zoom=MAX_ZOOM)
    force_fit_on_mount(m, points, max_zoom=MAX_ZOOM)

    # Unique key per visit + bounds signature
    lats = [p[0] for p in points]; lons = [p[1] for p in points]
    sig = (round(min(lats),4), round(min(lons),4), round(max(lats),4), round(max(lons),4))
    render_map(m, key=unique_map_key(page_id, trip_id, sig))

    st.subheader("Restaurant-Liste")
    df_rests = pd.DataFrame([
        {"Name": r.get("name",""), "Beschreibung": r.get("description",""),
         "Latitude": r.get("lat"), "Longitude": r.get("lon"), "Google Maps": r.get("gmap_url","")}
        for r in trip_rests
    ])
    st.dataframe(
        df_rests,
        use_container_width=True,
        column_config={
            "Google Maps": st.column_config.LinkColumn("Google Maps", display_text="📍 Link"),
            "Latitude": st.column_config.NumberColumn(format="%.6f"),
            "Longitude": st.column_config.NumberColumn(format="%.6f"),
        },
    )
    st.download_button("Restaurants als CSV herunterladen",
                       df_rests.to_csv(index=False).encode("utf-8"),
                       file_name="restaurants.csv", mime="text/csv")
