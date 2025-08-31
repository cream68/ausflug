# app/poi_hikes_section.py
from __future__ import annotations

from itertools import cycle
from typing import List, Optional

import folium
import geopandas as gpd
import pandas as pd
import streamlit as st
from folium import plugins
from shapely.geometry import LineString, MultiLineString

from data import HIKES, POIs, camping, locations_trip, winner_id
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

PALETTE = ["#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00",
           "#ffff33", "#a65628", "#f781bf", "#999999"]


def popup_html(name: str, desc: str, gmap_url: str) -> str:
    return (
        "<div style='max-width:260px'>"
        f"<b>{name}</b><br>"
        f"<span style='font-size:12px'>{desc}</span><br>"
        f"<a href='{gmap_url}' target='_blank'>📍 Auf Google Maps öffnen</a>"
        "</div>"
    )


def _extract_track_coords(gdf: gpd.GeoDataFrame) -> List[List[float]]:
    coords: List[List[float]] = []
    for geom in gdf.geometry:
        if isinstance(geom, LineString):
            coords.extend([[lat, lon] for lon, lat in list(geom.coords)])
        elif isinstance(geom, MultiLineString):
            for line in geom.geoms:
                coords.extend([[lat, lon] for lon, lat in list(line.coords)])
    return coords


def render_poi_hikes(selected_trip_id: Optional[int] = None, *, page_id: str = "poi_hikes") -> None:
    trip_id = selected_trip_id if selected_trip_id is not None else winner_id
    trip_name, trip_center = locations_trip[trip_id]
    trip_pois  = [p.copy() for p in POIs  if p.get("trip_id") == trip_id]
    trip_hikes = [h.copy() for h in HIKES if h.get("trip_id") == trip_id]
    trip_camps = [c.copy() for c in camping if c.get("trip_id") == trip_id]

    m = new_map(trip_center, zoom=10)
    add_default_plugins(m)

    fg_camps = folium.FeatureGroup(name="🏕️ Camping", show=True).add_to(m)
    fg_pois  = folium.FeatureGroup(name="📌 POIs", show=True).add_to(m)
    fg_hikes_master = folium.FeatureGroup(name="🥾 Wanderungen", show=True).add_to(m)
    clu_pois = plugins.MarkerCluster(name="POIs Cluster", show=True); clu_pois.add_to(fg_pois)

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

    # POIs (geocode)
    failed: List[str] = []
    prog = st.progress(0, text="Geocoding POIs …")
    N = max(len(trip_pois), 1)
    for i, p in enumerate(trip_pois, start=1):
        coords = geocode_one(p.get("address", "")) if p.get("address") else None
        if not coords:
            p["lat"], p["lon"] = None, None
            failed.append(p.get("name", ""))
            prog.progress(i / N, text=f"Geocoding POIs … ({i}/{len(trip_pois)})")
            continue

        lat, lon = coords
        p["lat"], p["lon"] = lat, lon

        folium.Marker(
            [lat, lon],
            popup=folium.Popup(popup_html(p.get("name",""), p.get("description",""), p.get("gmap_url","#")), max_width=300),
            icon=folium.Icon(icon="info-sign", prefix="glyphicon", color="blue"),
        ).add_to(clu_pois)
        points.append([lat, lon])
        prog.progress(i / N, text=f"Geocoding POIs … ({i}/{len(trip_pois)})")
    prog.empty()

    if failed:
        with st.expander(f"⚠️ {len(failed)} POIs konnten nicht geocoded werden (anzeigen)"):
            for n in failed:
                st.write(f"- {n}")

    # Hikes
    loaded = 0
    colors = cycle(PALETTE)
    for h in trip_hikes:
        try:
            gdf = gpd.read_file(h["file"], layer="tracks")
            if gdf.empty:
                st.warning(f"Keine Track-Daten in {h['name']}")
                continue

            coords = _extract_track_coords(gdf)
            if not coords:
                st.warning(f"Kein Linien-Geom in {h['name']}")
                continue

            xmin, ymin, xmax, ymax = gdf.total_bounds
            points += [[ymin, xmin], [ymax, xmax]]

            fg = folium.FeatureGroup(name=f"🥾 {h['name']}")
            folium.PolyLine(
                locations=coords,
                color=next(colors),
                weight=3,
                popup=folium.Popup(
                    f"<b>{h['name']}</b><br>{h.get('duration','')}<br>"
                    f"<a href='{h.get('link','#')}' target='_blank'>🔗 Hike Info</a>",
                    max_width=300,
                ),
            ).add_to(fg)
            fg.add_to(fg_hikes_master)
            loaded += 1
        except Exception as e:  # keep robust
            st.warning(f"Fehler beim Laden von '{h.get('name','?')}': {e}")

    folium.LayerControl(collapsed=False).add_to(m)
    fit_bounds(m, points, max_zoom=MAX_ZOOM)
    force_fit_on_mount(m, points, max_zoom=MAX_ZOOM)

    # Unique key per visit + bounds signature
    lats = [p[0] for p in points]; lons = [p[1] for p in points]
    sig = (round(min(lats),4), round(min(lons),4), round(max(lats),4), round(max(lons),4))
    render_map(m, key=unique_map_key(page_id, trip_id, sig))

    st.subheader("POI Liste")
    # Note: address intentionally omitted (per your earlier requirement)
    df_pois = pd.DataFrame([
        {"Name": p.get("name",""), "Beschreibung": p.get("description",""),
         "Latitude": p.get("lat"), "Longitude": p.get("lon"), "Google Maps": p.get("gmap_url","")}
        for p in trip_pois
    ])
    st.dataframe(
        df_pois,
        use_container_width=True,
        column_config={
            "Google Maps": st.column_config.LinkColumn("Google Maps", display_text="📍 Link"),
            "Latitude": st.column_config.NumberColumn(format="%.6f"),
            "Longitude": st.column_config.NumberColumn(format="%.6f"),
        },
    )
    st.download_button("POIs als CSV herunterladen",
                       df_pois.to_csv(index=False).encode("utf-8"),
                       file_name="pois.csv", mime="text/csv")

    st.subheader("Wanderungen")
    df_hikes = pd.DataFrame([
        {"Name": h.get("name",""), "Dauer": h.get("duration",""), "Link": h.get("link","")}
        for h in trip_hikes
    ])
    st.dataframe(
        df_hikes,
        use_container_width=True,
        column_config={"Link": st.column_config.LinkColumn("Link", display_text="🔗 Hike Info")},
    )
    st.download_button("Wanderungen als CSV herunterladen",
                       df_hikes.to_csv(index=False).encode("utf-8"),
                       file_name="hikes.csv", mime="text/csv")
