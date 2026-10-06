import os
import sys

# Streamlit runs this file as a script, so the repository root is not on sys.path.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

st.set_page_config(
    page_title="WeatherRetail Intelligence",
    page_icon=":material/partly_cloudy_day:",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.logo(os.path.join(os.path.dirname(__file__), "assets", "mark.svg"), size="small")

# Shadows only. Color, type, and radius come from .streamlit/config.toml.
st.html(
    """
    <style>
    [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stMetric"] {
      box-shadow: 0 1px 2px rgba(31, 26, 23, 0.04), 0 10px 28px rgba(31, 26, 23, 0.05);
    }
    </style>
    """
)

page = st.navigation(
    [
        st.Page(
            os.path.join("app_pages", "overview.py"),
            title="Overview",
            icon=":material/dashboard:",
            default=True,
        ),
        st.Page(
            os.path.join("app_pages", "sensitivity.py"),
            title="Weather sensitivity",
            icon=":material/thermostat:",
        ),
        st.Page(
            os.path.join("app_pages", "risk.py"),
            title="Risk and forecast",
            icon=":material/warning:",
        ),
        st.Page(
            os.path.join("app_pages", "store.py"),
            title="Store deep dive",
            icon=":material/storefront:",
        ),
    ],
    position="top",
)
page.run()
