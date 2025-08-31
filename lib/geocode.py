# lib/geocode.py
from __future__ import annotations

from typing import Optional, Tuple

import streamlit as st
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim


def _new_geocoder() -> Nominatim:
    return Nominatim(user_agent="ausflug/1.0 (streamlit)", timeout=5)

@st.cache_data(show_spinner=False, ttl=60 * 60 * 24)
def geocode_one(address: str) -> Optional[Tuple[float, float]]:
    safe = RateLimiter(_new_geocoder().geocode, min_delay_seconds=1, swallow_exceptions=True)
    loc = safe(address)
    return (float(loc.latitude), float(loc.longitude)) if loc else None
