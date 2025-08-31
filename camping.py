from typing import Optional, Tuple, Iterable, List
import folium
from folium import plugins
import streamlit as st
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

# st_folium vs folium_static handling
try:
    from streamlit_folium import st_folium as _ST_RENDER
    _USES_ST_FOLIUM = True
    _RENDER_ARGS = dict(returned_objects=[], use_container_width=True, height=650)
except Exception:
    from streamlit_folium import folium_static as _ST_RENDER  # type: ignore
    _USES_ST_FOLIUM = False
    _RENDER_ARGS = dict(height=650)

from data import locations_trip, winner_id, camping, bakery, supermarkt

CAMP_ICON_URL = "https://cdn-icons-png.flaticon.com/512/9173/9173952.png"
CAMP_ICON_SIZE = (40, 40)
CAMP_ICON_ANCHOR = (20, 40)
MAX_ZOOM = 15
FA_BAKERY = "coffee"
FA_SUPERMARKET = "shopping-basket"

def _new_geocoder() -> Nominatim:
    return Nominatim(user_agent="restaurant-mapper/1.0 (streamlit)", timeout=5)

@st.cache_data(show_spinner=False, ttl=60 * 60 * 24)
def geocode_one(address: str) -> Optional[Tuple[float, float]]:
    safe = RateLimiter(_new_geocoder().geocode, min_delay_seconds=1, swallow_exceptions=True)
    loc = safe(address)
    if not loc:
        return None
    return float(loc.latitude), float(loc.longitude)

def popup_html(name: str, desc: str, gmap_url: str) -> str:
    return f"""
        <div style="max-width: 250px">
            <b>{name}</b><br>
            <span style="font-size: 12px">{desc}</span><br>
            <a href="{gmap_url}" target="_blank">📍 View on Google Maps</a>
        </div>
    """

def _render_map(m: folium.Map, key: str) -> None:
    if _USES_ST_FOLIUM:
        _ST_RENDER(m, key=key, **_RENDER_ARGS)
    else:
        _ST_RENDER(m, **_RENDER_ARGS)  # folium_static has no key/support

def render_camping(selected_trip_id: Optional[int] = None, *, key: Optional[str] = None) -> None:
    trip_id = selected_trip_id if selected_trip_id is not None else winner_id
    trip_name, trip_center = locations_trip[trip_id]

    # Filter to trip
    trip_camps = [c for c in camping if c.get("trip_id") == trip_id]
    trip_bakeries = [b for b in bakery if b.get("trip_id") == trip_id]
    trip_supermarkets = [s for s in supermarkt if s.get("trip_id") == trip_id]

    # Center on camping locations
    camp_points: List[Tuple[float, float]] = [
        (float(c["lat"]), float(c["lon"]))
        for c in trip_camps if c.get("lat") is not None and c.get("lon") is not None
    ]
    if camp_points:
        center_lat = sum(p[0] for p in camp_points) / len(camp_points)
        center_lon = sum(p[1] for p in camp_points) / len(camp_points)
        map_center = (center_lat, center_lon)
        start_zoom = 12 if len(camp_points) == 1 else 11
    else:
        map_center = trip_center
        start_zoom = 10

    m = folium.Map(location=map_center, zoom_start=start_zoom, tiles="CartoDB Positron", control_scale=True)
    all_coords: List[List[float]] = [list(map_center)]

    # Plugins
    plugins.Fullscreen(position="topright").add_to(m)
    plugins.LocateControl(auto_start=False).add_to(m)
    plugins.MeasureControl(primary_length_unit="kilometers").add_to(m)
    plugins.MiniMap(toggle_display=True).add_to(m)
    plugins.MousePosition(separator=" | ", position="bottomleft").add_to(m)

    # Layers
    fg_camps = folium.FeatureGroup(name="🏕️ Camping", show=True).add_to(m)
    fg_bakeries = folium.FeatureGroup(name="🥐 Bakeries", show=True).add_to(m)
    fg_supermarkets = folium.FeatureGroup(name="🛒 Supermarkets", show=True).add_to(m)

    clu_bakeries = plugins.MarkerCluster(name="Bakeries cluster", show=True); clu_bakeries.add_to(fg_bakeries)
    clu_supermarkets = plugins.MarkerCluster(name="Supermarkets cluster", show=True); clu_supermarkets.add_to(fg_supermarkets)

    for c in trip_camps:
        lat, lon = float(c["lat"]), float(c["lon"])
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(html=f"<b>{c['name']}</b>", max_width=250),
            icon=folium.CustomIcon(CAMP_ICON_URL, icon_size=CAMP_ICON_SIZE, icon_anchor=CAMP_ICON_ANCHOR),
        ).add_to(fg_camps)
        all_coords.append([lat, lon])

    def add_poi_group(places: Iterable[dict], fa_icon: str, color: str, cluster_layer: plugins.MarkerCluster, label: str) -> int:
        added = 0
        failures: List[dict] = []
        progress = st.progress(0, text=f"Geocoding {label} …")
        places_list = list(places)
        n = len(places_list) or 1
        for i, r in enumerate(places_list, start=1):
            coords = geocode_one(r.get("address", ""))
            progress.progress(i / n, text=f"Geocoding {label} ({i}/{len(places_list)})")
            if not coords:
                failures.append(r); continue
            lat, lon = coords
            folium.Marker(
                location=[lat, lon],
                popup=popup_html(r.get("name",""), r.get("description",""), r.get("gmap_url","#")),
                icon=folium.Icon(icon=fa_icon, prefix="fa", color=color),
            ).add_to(cluster_layer)
            all_coords.append([lat, lon]); added += 1
        progress.empty()
        if failures:
            with st.expander(f"⚠️ {len(failures)} {label.lower()} could not be geocoded (click to view)"):
                for r in failures:
                    st.write(f"- {r.get('name','')} — `{r.get('address','')}`")
        return added

    add_poi_group(trip_bakeries, FA_BAKERY, "orange", clu_bakeries, "Bakeries")
    add_poi_group(trip_supermarkets, FA_SUPERMARKET, "blue", clu_supermarkets, "Supermarkets")

    folium.LayerControl(collapsed=False).add_to(m)

    # Fit bounds
    if all_coords:
        m.fit_bounds(all_coords, max_zoom=MAX_ZOOM)

    # --- IMPORTANT: make the key unique to data/state ------------------------
    # include trip_id AND a small hash of bounds so the widget resets when points change
    lats = [c[0] for c in all_coords]; lons = [c[1] for c in all_coords]
    bounds_tuple = (round(min(lats), 4), round(min(lons), 4), round(max(lats), 4), round(max(lons), 4))
    view_hash = abs(hash(bounds_tuple)) % 10_000_000  # short
    map_key = key or f"camping_map_{trip_id}_{view_hash}"

    _render_map(m, map_key)
