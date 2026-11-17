import streamlit as st
import pandas as pd
from typing import List, Dict, Any


def render_preview_table(records: List[Dict[str, Any]], title: str = ""):
    if title:
        st.markdown(f"**{title}**")
    if not records:
        st.info("No records to display.")
        return
    df = pd.DataFrame(records)
    st.dataframe(df, use_container_width=True, hide_index=True)
