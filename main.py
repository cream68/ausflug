# app_overview.py
from __future__ import annotations
import streamlit as st
from start import render_startpage
from camping import render_camping
from hikes_POI import render_poi_hikes
from restaurants import render_restaurants
from data import locations_home, locations_trip, winner_id
trip_name, trip_center = locations_trip[winner_id]


st.set_page_config(page_title="IFM Trip", page_icon="🗺️", layout="wide")
st.markdown(f"""
    ### 🗺️ Es geht nach: {trip_name}
    """
)
tab1, tab2, tab3, tab4 = st.tabs(["Info", "Camping", "POIS", "Restaurants"])
with tab1:
    render_startpage()
with tab2:
    render_camping()
with tab3:
    render_poi_hikes()
with tab4:
    render_restaurants()
