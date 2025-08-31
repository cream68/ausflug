# app_overview.py
from __future__ import annotations

import streamlit as st

from app.camping_section import render_camping
from app.hikes_section import render_poi_hikes
from app.overview_section import render_startpage
from app.restaurants_section import render_restaurants
from data import locations_trip, winner_id

trip_name, trip_center = locations_trip[winner_id]


st.set_page_config(page_title="IFM Trip", page_icon="🗺️", layout="wide")
st.markdown(f"""
    ### 🗺️ Es geht nach: {trip_name}
    """
)
options = ["Info", "Camping", "POIs", "Restaurants"]
choice = st.segmented_control(label="Menu", options=options, key="section", default="Info")
if choice == "Info":
    render_startpage()
elif choice == "Camping":
    render_camping()
elif choice == "POIs":
    render_poi_hikes()
else:
    render_restaurants()
