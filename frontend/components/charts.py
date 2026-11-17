import json
import streamlit as st
import plotly.io as pio


def render_plotly_json(figure_json_str: str, use_container_width: bool = True):
    if not figure_json_str:
        st.warning("No visualization data available.")
        return
    try:
        fig_dict = json.loads(figure_json_str)
        fig = pio.from_json(json.dumps(fig_dict))
        st.plotly_chart(fig, use_container_width=use_container_width)
    except Exception as exc:
        st.error(f"Failed to render chart: {str(exc)}")
