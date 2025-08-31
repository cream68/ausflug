# lib/session.py
from __future__ import annotations

import streamlit as st


def visit_token(page_id: str) -> int:
    """Bumps once when (re)entering a page/section during this app run."""
    last = st.session_state.get("__last_page")
    if last != page_id:
        st.session_state["__last_page"] = page_id
        st.session_state[f"__visit_{page_id}"] = st.session_state.get(f"__visit_{page_id}", 0) + 1
    return st.session_state.get(f"__visit_{page_id}", 0)


def unique_map_key(page_id: str, trip_id: int, bounds_sig: tuple[float, float, float, float]) -> str:
    """Stable, unique key per page visit and data state (prevents stale viewport restore)."""
    visit = visit_token(page_id)
    short = abs(hash(bounds_sig)) % 1_000_000
    return f"{page_id}_map_{trip_id}_{visit}_{short}"
