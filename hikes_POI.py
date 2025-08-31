# poi_hikes_section.py
from __future__ import annotations

import math
from itertools import cycle
from typing import Iterable, List, Optional, Tuple

import folium
from folium import plugins
import geopandas as gpd
import pandas as pd
import streamlit as st
from shapely.geometry import LineString, MultiLineString

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.distance import geodesic

from streamlit_folium import st_folium as _st_render_map
_RENDER_ARGS = dict(returned_objects=[], use_container_width=True, height=650)

from data import HIKES, POIs, locations_trip, winner_id, camping

# --- Icons / constants --------------------------------------------------------
CAMP_ICON_URL = "https://cdn-icons-png.flaticon.com/512/9173/9173952.png"
CAMP_ICON_SIZE = (40, 40)
CAMP_ICON_ANCHOR = (20, 40)  # bottom center

# --- Helpers ------------------------------------------------------------------
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

def _new_geocoder() -> Nominatim:
    return Nominatim(user_agent="poi-hike-mapper/1.0 (streamlit)", timeout=5)

@st.cache_data(show_spinner=False, ttl=60 * 60 * 24)
def geocode_one(address: str) -> Optional[Tuple[float, float]]:
    geocoder = _new_geocoder()
    safe = RateLimiter(geocoder.geocode, min_delay_seconds=1, swallow_exceptions=True)
    loc = safe(address)
    if not loc:
        return None
    return float(loc.latitude), float(loc.longitude)

def _extract_track_coords(gdf: gpd.GeoDataFrame) -> List[List[float]]:
    coords: List[List[float]] = []
    for geom in gdf.geometry:
        if isinstance(geom, LineString):
            coords.extend([[lat, lon] for lon, lat in list(geom.coords)])
        elif isinstance(geom, MultiLineString):
            for line in geom.geoms:
                coords.extend([[lat, lon] for lon, lat in list(line.coords)])
    return coords

# --- Public API ---------------------------------------------------------------
def render_poi_hikes(selected_trip_id: Optional[int] = None) -> None:
    """
    Render the POIs + Hikes map (with camping markers) and the tables/metrics.
    Safe to call inside a Streamlit tab. Does NOT set page config or a page title.
    """
    trip_id = selected_trip_id if selected_trip_id is not None else winner_id
    trip_name, trip_center = locations_trip[trip_id]
    trip_POIs = [p.copy() for p in POIs if p.get("trip_id") == trip_id]
    trip_HIKES = [h.copy() for h in HIKES if h.get("trip_id") == trip_id]
    trip_CAMPS = [c.copy() for c in camping if c.get("trip_id") == trip_id]

    # Map (CartoDB Light)
    m = folium.Map(location=trip_center, zoom_start=10, tiles="CartoDB Positron", control_scale=True)
    plugins.Fullscreen(position="topright").add_to(m)
    plugins.LocateControl(auto_start=False).add_to(m)
    plugins.MeasureControl(primary_length_unit="kilometers").add_to(m)
    plugins.MiniMap(toggle_display=True).add_to(m)
    plugins.MousePosition(separator=" | ", position="bottomleft").add_to(m)

    # Feature groups
    fg_camps = folium.FeatureGroup(name="🏕️ Camping", show=True).add_to(m)
    fg_pois = folium.FeatureGroup(name="📌 POIs", show=True).add_to(m)
    fg_hikes_master = folium.FeatureGroup(name="🥾 Wanderungen", show=True).add_to(m)

    # Clustering for POIs
    clu_pois = plugins.MarkerCluster(name="POIs Cluster", show=True)
    clu_pois.add_to(fg_pois)

    all_coords: List[List[float]] = [list(trip_center)]

    # Camping markers
    for camp in trip_CAMPS:
        lat, lon = float(camp["lat"]), float(camp["lon"])
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(f"<b>{camp.get('name','')}</b>", max_width=250),
            icon=folium.CustomIcon(CAMP_ICON_URL, icon_size=CAMP_ICON_SIZE, icon_anchor=CAMP_ICON_ANCHOR),
            z_index_offset=0,
        ).add_to(fg_camps)
        all_coords.append([lat, lon])

    # POIs (geocode + markers)
    failed_geocodes: List[str] = []
    progress = st.progress(0, text="Geocoding POIs …")
    N = max(len(trip_POIs), 1)

    for i, poi in enumerate(trip_POIs, start=1):
        addr = poi.get("address", "")
        coords = geocode_one(addr) if addr else None
        if not coords:
            failed_geocodes.append(poi.get("name", ""))
            poi["lat"], poi["lon"] = None, None
            progress.progress(i / N, text=f"Geocoding POIs … ({i}/{len(trip_POIs)})")
            continue

        lat, lon = coords
        poi["lat"], poi["lon"] = lat, lon

        html = f"""
            <div style='font-size: 14px; max-width: 260px'>
                <b>{poi.get('name','')}</b><br>
                <p style="margin: 6px 0">{poi.get('description','')}</p>
                <a href="{poi.get('gmap_url','#')}" target="_blank">📍 Auf Google Maps öffnen</a>
            </div>
        """
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(html, max_width=300),
            icon=folium.Icon(icon="info-sign", prefix="glyphicon", color="blue"),
        ).add_to(clu_pois)

        all_coords.append([lat, lon])
        progress.progress(i / N, text=f"Geocoding POIs … ({i}/{len(trip_POIs)})")

    progress.empty()
    if failed_geocodes:
        with st.expander(f"⚠️ {len(failed_geocodes)} POIs konnten nicht geocoded werden (anzeigen)"):
            for n in failed_geocodes:
                st.write(f"- {n}")

    # Hikes (lines)
    palette = ["#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00", "#ffff33", "#a65628", "#f781bf", "#999999"]
    palette_cycler = cycle(palette)
    loaded_hikes = 0

    for hike in trip_HIKES:
        try:
            gdf = gpd.read_file(hike["file"], layer="tracks")
            if gdf.empty:
                st.warning(f"Keine Track-Daten in {hike['name']}")
                continue

            coords = _extract_track_coords(gdf)
            if not coords:
                st.warning(f"Kein Linien-Geom in {hike['name']}")
                continue

            xmin, ymin, xmax, ymax = gdf.total_bounds
            all_coords += [[ymin, xmin], [ymax, xmax]]

            color = next(palette_cycler)
            fg = folium.FeatureGroup(name=f"🥾 {hike['name']}")
            folium.PolyLine(
                locations=coords,
                color=color,
                weight=3,
                popup=folium.Popup(
                    f"<b>{hike['name']}</b><br>{hike.get('duration','')}<br>"
                    f"<a href='{hike.get('link','#')}' target='_blank'>🔗 Hike Info</a>",
                    max_width=300,
                ),
            ).add_to(fg)
            fg.add_to(fg_hikes_master)
            loaded_hikes += 1
        except Exception as e:
            st.warning(f"Fehler beim Laden von '{hike['name']}': {e}")

    folium.LayerControl(collapsed=False).add_to(m)

    # Fit bounds (camps + POIs + hikes)
    if all_coords:
        m.fit_bounds(all_coords, max_zoom=15)
    else:
        m.location = trip_center
        m.zoom_start = 13

    # Render map
    _st_render_map(m, key="hikes", **_RENDER_ARGS)

    # --- Tables ---------------------------------------------------------------
    st.subheader("POI Liste")
    # POI list WITHOUT address, but includes lat/lon + Google Maps link
    df_pois = pd.DataFrame([
        {
            "Name": p.get("name",""),
            "Beschreibung": p.get("description",""),
            "Google Maps": p.get("gmap_url",""),
        }
        for p in trip_POIs
    ])
    st.dataframe(
        df_pois,
        use_container_width=True,
        column_config={
            "Google Maps": st.column_config.LinkColumn("Google Maps", display_text="📍 Link"),
        },
    )
    st.download_button("POIs als CSV herunterladen",
                       df_pois.to_csv(index=False).encode("utf-8"),
                       file_name="pois.csv", mime="text/csv")

    st.subheader("Wanderungen")
    df_hikes = pd.DataFrame([
        {"Name": h.get("name",""), "Dauer": h.get("duration",""), "Link": h.get("link","")}
        for h in trip_HIKES
    ])
    st.dataframe(
        df_hikes,
        use_container_width=True,
        column_config={"Link": st.column_config.LinkColumn("Link", display_text="🔗 Hike Info")},
    )
    st.download_button("Wanderungen als CSV herunterladen",
                       df_hikes.to_csv(index=False).encode("utf-8"),
                       file_name="hikes.csv", mime="text/csv")
