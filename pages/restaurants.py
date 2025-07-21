import folium
import pandas as pd
import streamlit as st
from geopy.geocoders import Nominatim
from streamlit_folium import folium_static

from data import locations_trip, restaurants

geolocator = Nominatim(user_agent="restaurant-mapper", timeout=5)

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

filtered_restaurants = [restaurant for restaurant in restaurants if restaurant.get("trip_id") == selected_trip_id]

for r in filtered_restaurants:
    location = geolocator.geocode(r["address"])
    if location:
        r["location"] = [location.latitude, location.longitude]
    else:
        r["location"] = [0, 0]  # fallback

st.title("Restaurants")

m = folium.Map(location=trip_center)

all_lats = [trip_center[0]]
all_lons = [trip_center[1]]

for r in filtered_restaurants:
    html_popup = f"""
        <b>{r['name']}</b><br>
        {r['description']}<br>
        <a href="{r['gmap_url']}" target="_blank">📍 View on Google Maps</a>
    """
    folium.Marker(
        location=r["location"],
        popup=html_popup,
        icon=folium.Icon(icon="cutlery", prefix="fa", color="red")
    ).add_to(m)

    all_lats.append(r["location"][0])
    all_lons.append(r["location"][1])

folium.Marker(
    location=trip_center,
    tooltip=f"{trip_name}",
    icon=folium.Icon(icon="star", prefix="fa", color="green")
).add_to(m)

if all_lats and all_lons:
    min_lat, max_lat = min(all_lats), max(all_lats)
    min_lon, max_lon = min(all_lons), max(all_lons)

    center_lat = (min_lat + max_lat) / 2
    center_lon = (min_lon + max_lon) / 2

    half_height = (max_lat - min_lat) / 2
    half_width = (max_lon - min_lon) / 2

    scale = 1.4
    expanded_half_height = half_height * scale
    expanded_half_width = half_width * scale

    expanded_min_lat = center_lat - expanded_half_height
    expanded_max_lat = center_lat + expanded_half_height
    expanded_min_lon = center_lon - expanded_half_width
    expanded_max_lon = center_lon + expanded_half_width

    m.fit_bounds([[expanded_min_lat, expanded_min_lon], [expanded_max_lat, expanded_max_lon]])

folium_static(m)

data = [
    {
        "Name": r["name"],
        "Description": r["description"],
        "Google Maps": f"[📍 Link]({r['gmap_url']})"
    }
    for r in filtered_restaurants
]

df = pd.DataFrame(data)

st.markdown("Restaurants")
st.write(df.to_markdown(index=False), unsafe_allow_html=True)
