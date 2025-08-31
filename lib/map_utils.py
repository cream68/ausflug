# lib/map_utils.py
from __future__ import annotations

import json

import folium
from folium import plugins

# Prefer st_folium; fall back to folium_static
try:
    from streamlit_folium import st_folium as _ST_RENDER
    _USES_ST = True
    DEFAULT_RENDER_ARGS = dict(
        returned_objects=[],
        use_container_width=True,
        height=520,   # reduced from 650 to avoid large whitespace
    )
except Exception:  # pragma: no cover
    from streamlit_folium import folium_static as _ST_RENDER  # type: ignore
    _USES_ST = False
    DEFAULT_RENDER_ARGS = dict(height=520)


def new_map(center: tuple[float, float], zoom: int = 10) -> folium.Map:
    return folium.Map(
        location=center,
        zoom_start=zoom,
        tiles="CartoDB Positron",
        control_scale=True,
    )


def add_default_plugins(m: folium.Map) -> None:
    plugins.Fullscreen(position="topright").add_to(m)
    plugins.LocateControl(auto_start=False).add_to(m)
    plugins.MeasureControl(primary_length_unit="kilometers").add_to(m)
    plugins.MiniMap(toggle_display=True).add_to(m)
    plugins.MousePosition(separator=" | ", position="bottomleft").add_to(m)


def points_to_bounds(points: list[list[float]]) -> list[list[float]]:
    """[[lat, lon], ...] -> [[south, west], [north, east]]"""
    lats = [p[0] for p in points]
    lons = [p[1] for p in points]
    return [[min(lats), min(lons)], [max(lats), max(lons)]]


def fit_bounds(m: folium.Map, points: list[list[float]], max_zoom: int = 15) -> None:
    if not points:
        return
    m.fit_bounds(points, max_zoom=max_zoom)


def force_fit_on_mount(
    m: folium.Map, points: list[list[float]], max_zoom: int = 15, padding_px: int = 24
) -> None:
    """Fix Leaflet rendering when container was hidden: invalidateSize + fitBounds after mount."""
    if not points:
        return
    sw_ne = points_to_bounds(points)
    js = f"""
    <script>(function(){{
      function fit(){{
        try {{
          var map = {m.get_name()};
          map.invalidateSize();
          map.fitBounds({json.dumps(sw_ne)}, {{maxZoom:{max_zoom}, padding:[{padding_px},{padding_px}]}});
        }} catch(e) {{}}
      }}
      setTimeout(fit,0); setTimeout(fit,200); setTimeout(fit,600);
    }})();</script>
    """
    m.get_root().html.add_child(folium.Element(js))


def render_map(m: folium.Map, *, key: str, **kwargs) -> None:
    """Render regardless of backend; only pass key/extras when supported."""
    if _USES_ST:
        args = dict(DEFAULT_RENDER_ARGS)
        args.update(kwargs)
        _ST_RENDER(m, key=key, **args)
    else:
        _ST_RENDER(
            m,
            height=kwargs.get("height", DEFAULT_RENDER_ARGS.get("height", 520)),
        )
