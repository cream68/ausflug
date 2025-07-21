import folium
import streamlit as st
from streamlit_folium import folium_static

from data import locations_home, locations_trip

m = folium.Map(location=[48.5, 9.5], zoom_start=7, tiles="OpenStreetMap")

for city, (lat, lon) in locations_home.items():
    folium.Marker(
        location=[lat, lon],
        popup=city,
        icon=folium.CustomIcon(
        icon_image="https://cdn-icons-png.flaticon.com/512/25/25694.png",
        icon_size=(40, 40),
        icon_anchor=(20, 40)
    )
    ).add_to(m)


for trip_id, (city_name, (lat, lon)) in locations_trip.items():
    folium.Marker(
        [lat, lon],
        icon=folium.DivIcon(
            html=f"""
            <div style="
                width: 150px;
                text-align: left;
                font-size: 12px;
                font-weight: bold;
                color: black;
                margin-top: -30px;
                margin-left: 25px;
                white-space: nowrap;
            ">
                {city_name}
            </div>
            """
        )
    ).add_to(m)

    folium.Marker(
        location=[lat, lon],
        popup=city,
        icon=folium.CustomIcon(
            icon_image="https://cdn-icons-png.flaticon.com/512/684/684908.png",
            icon_size=(40, 40),
            icon_anchor=(20, 40)
        )
    ).add_to(m)

st.title("Ausflug")
st.text("Karte")
folium_static(m)

