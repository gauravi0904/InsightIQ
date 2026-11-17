import streamlit as st
from typing import Optional


def render_metric_card(title: str, value: str, subtitle: Optional[str] = None, delta: Optional[str] = None, delta_color: str = "normal"):
    card_html = f"""
    <div style="background: white; border: 1px solid #e2e8f0; border-radius: 10px; padding: 18px 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 12px;">
        <div style="font-size: 0.82rem; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">
            {title}
        </div>
        <div style="font-size: 1.8rem; font-weight: 700; color: #0f172a; margin: 4px 0;">
            {value}
        </div>
        {f'<div style="font-size: 0.78rem; color: #64748b;">{subtitle}</div>' if subtitle else ''}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)
