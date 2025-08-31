# app/camping_section.py
from __future__ import annotations

from typing import Iterable, List, Optional, Tuple

import folium
from folium import plugins

from data import bakery, camping, locations_trip, supermarkt, winner_id
from lib.geocode import geocode_one
from lib.map_utils import (
    add_default_plugins,
    fit_bounds,
    force_fit_on_mount,
    new_map,
    render_map,
)
from lib.session import unique_map_key

CAMP_ICON_URL = "https://cdn-icons-png.flaticon.com/512/9173/9173952.png"
CAMP_ICON_SIZE = (40, 40)
CAMP_ICON_ANCHOR = (20, 40)
MAX_ZOOM = 15
FA_BAKERY = "coffee"
FA_SUPERMARKET = "shopping-basket"


def popup_html(name: str, desc: str, gmap_url: str) -> str:
    return f"""<div style="max-width:250px"><b>{name}</b><br>
               <span style="font-size:12px">{desc}</span><br>
               <a href="{gmap_url}" target="_blank">📍 View on Google Maps</a></div>"""


def render_camping(selected_trip_id: Optional[int] = None, *, page_id: str = "camping") -> None:
    trip_id = selected_trip_id if selected_trip_id is not None else winner_id
    trip_name, trip_center = locations_trip[trip_id]

    trip_camps = [c for c in camping if c.get("trip_id") == trip_id]
    trip_bakeries = [b for b in bakery if b.get("trip_id") == trip_id]
    trip_supermarkets = [s for s in supermarkt if s.get("trip_id") == trip_id]

    camp_points: List[Tuple[float, float]] = [
        (float(c["lat"]), float(c["lon"])) for c in trip_camps if c.get("lat") and c.get("lon")
    ]
    if camp_points:
        center_lat = sum(p[0] for p in camp_points) / len(camp_points)
        center_lon = sum(p[1] for p in camp_points) / len(camp_points)
        m = new_map((center_lat, center_lon), zoom=12 if len(camp_points) == 1 else 11)
    else:
        m = new_map(trip_center, zoom=10)

    add_default_plugins(m)
    fg_camps = folium.FeatureGroup(name="🏕️ Camping", show=True).add_to(m)
    fg_bakeries = folium.FeatureGroup(name="🥐 Bakeries", show=True).add_to(m)
    fg_supermarkets = folium.FeatureGroup(name="🛒 Supermarkets", show=True).add_to(m)

    clu_b = plugins.MarkerCluster(name="Bakeries cluster", show=True); clu_b.add_to(fg_bakeries)
    clu_s = plugins.MarkerCluster(name="Supermarkets cluster", show=True); clu_s.add_to(fg_supermarkets)

    all_points: List[List[float]] = []
    for c in trip_camps:
        lat, lon = float(c["lat"]), float(c["lon"])
        folium.Marker([lat, lon],
            popup=folium.Popup(html=f"<b>{c['name']}</b>", max_width=250),
            icon=folium.CustomIcon(CAMP_ICON_URL, icon_size=CAMP_ICON_SIZE, icon_anchor=CAMP_ICON_ANCHOR)
        ).add_to(fg_camps)
        all_points.append([lat, lon])

    def add_group(places: Iterable[dict], fa_icon: str, color: str, cluster) -> None:
        for r in places:
            coords = geocode_one(r.get("address", "")) if r.get("address") else None
            if not coords: continue
            lat, lon = coords
            folium.Marker([lat, lon],
                popup=popup_html(r.get("name",""), r.get("description",""), r.get("gmap_url","#")),
                icon=folium.Icon(icon=fa_icon, prefix="fa", color=color)
            ).add_to(cluster)
            all_points.append([lat, lon])

    add_group(trip_bakeries, FA_BAKERY, "orange", clu_b)
    add_group(trip_supermarkets, FA_SUPERMARKET, "blue", clu_s)

    folium.LayerControl(collapsed=False).add_to(m)

    # Fit + client refit (hidden container safe)
    base = [list(m.location)] + all_points if all_points else [list(m.location)]
    fit_bounds(m, base, max_zoom=MAX_ZOOM)
    force_fit_on_mount(m, base, max_zoom=MAX_ZOOM)

    # Unique key per visit + bounds signature
    lats = [p[0] for p in base]; lons = [p[1] for p in base]
    sig = (round(min(lats),4), round(min(lons),4), round(max(lats),4), round(max(lons),4))
    key = unique_map_key(page_id, trip_id, sig)

    render_map(m, key=key)
