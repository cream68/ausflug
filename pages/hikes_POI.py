import folium
import geopandas as gpd
import pandas as pd
import streamlit as st
from geopy.geocoders import Nominatim
from streamlit_folium import folium_static

from data import HIKES, POIs, locations_trip

st.set_page_config(page_title="POI & Hiking Map")
st.title("POI's und Wanderungen")

# Get trip keys
trip_keys = list(locations_trip.keys())

# Initialize default if not already set
if "selected_trip_id" not in st.session_state:
    st.session_state["selected_trip_id"] = trip_keys[0]

# Show selectbox, and bind it to the session state directly
st.session_state.selected_trip_id = st.sidebar.selectbox(
    "Choose a trip location",
    options=trip_keys,
    format_func=lambda k: locations_trip[k][0],
    index=trip_keys.index(st.session_state["selected_trip_id"])
)

# Now retrieve selected_trip_id and corresponding data
selected_trip_id = st.session_state.selected_trip_id
trip_name, trip_center = locations_trip[selected_trip_id]

trip_POIs = [p for p in POIs if p.get("trip_id") == selected_trip_id]
trip_HIKES = [h for h in HIKES if h.get("trip_id") == selected_trip_id]

geolocator = Nominatim(user_agent="poi-mapper", timeout=5)
for poi in trip_POIs:
    try:
        loc = geolocator.geocode(poi["address"])
        poi["location"] = [loc.latitude, loc.longitude] if loc else [0, 0]
    except Exception as e:
        st.warning(f"Geocoding failed for {poi['name']}: {e}")
        poi["location"] = [0, 0]

m = folium.Map(location=trip_center)
for poi in trip_POIs:
    html = f"""
    <div style='font-size: 14px;'>
        <b>{poi['name']}</b><br>
        <p>{poi['description']}</p>
        <a href="{poi['gmap_url']}" target="_blank">📍 View on Google Maps</a>
    </div>
    """
    folium.Marker(
        location=poi["location"],
        popup=folium.Popup(html, max_width=300),
        icon=folium.Icon(icon="info-sign", prefix="glyphicon", color="blue")
    ).add_to(m)

all_lats = [trip_center[0]] + [p["location"][0] for p in trip_POIs if p["location"] != [0, 0]]
all_lons = [trip_center[1]] + [p["location"][1] for p in trip_POIs if p["location"] != [0, 0]]

colors = ["#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00", "#ffff33", "#a65628", "#f781bf", "#999999"]

for hike, color in zip(trip_HIKES, colors):
    try:
        gdf = gpd.read_file(hike["file"], layer="tracks")
        if gdf.empty:
            st.warning(f"No track data found in {hike['name']}")
            continue

        coords = gdf.geometry.get_coordinates()[["y", "x"]].values.tolist()
        xmin, ymin, xmax, ymax = gdf.total_bounds
        all_lons += [xmin, xmax]
        all_lats += [ymin, ymax]

        polyline = folium.PolyLine(
            locations=coords,
            color=color,
            weight=3,
            popup=folium.Popup(
                f"<b>{hike['name']}</b><br>{hike['duration']}<br><a href='{hike['link']}' target='_blank'>🔗 Hike Info</a>",
                max_width=300
            )
        )
        fg = folium.FeatureGroup(name=hike["name"])
        polyline.add_to(fg)
        fg.add_to(m)
    except Exception as e:
        st.warning(f"Failed to load hike '{hike['name']}': {e}")

folium.LayerControl().add_to(m)

if all_lats and all_lons:
    lat_center = (min(all_lats) + max(all_lats)) / 2
    lon_center = (min(all_lons) + max(all_lons)) / 2
    h_half = (max(all_lats) - min(all_lats)) * 0.7
    w_half = (max(all_lons) - min(all_lons)) * 0.7
    m.fit_bounds([[lat_center - h_half, lon_center - w_half], [lat_center + h_half, lon_center + w_half]])
else:
    m.location = trip_center
    m.zoom_start = 13

folium.Marker(
    location=trip_center,
    tooltip=trip_name,
    icon=folium.Icon(icon="star", prefix="fa", color="green")
).add_to(m)

st.subheader("Interactive Map")
folium_static(m)

st.subheader("POI List")
st.markdown(pd.DataFrame([
    {"Name": p["name"], "Description": p["description"], "Google Maps": f"[📍 Link]({p['gmap_url']})"}
    for p in trip_POIs
]).to_markdown(index=False), unsafe_allow_html=True)

st.subheader("Wanderungen")
st.markdown(pd.DataFrame([
    {"Name": h["name"], "Duration": h["duration"], "Link": f"[🔗 Hike Info]({h['link']})"}
    for h in trip_HIKES
]).to_markdown(index=False), unsafe_allow_html=True)
