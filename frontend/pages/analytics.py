import streamlit as st
import pandas as pd
from frontend.api_client import api_client
from frontend.components.charts import render_plotly_json


def render_analytics_page():
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h1 style="font-size: 2rem; font-weight: 700; color: #0f172a; margin-bottom: 4px;">
                Statistical Analytics & Visualizations
            </h1>
            <p style="color: #64748b; font-size: 0.95rem;">
                Explore descriptive metrics, categorical frequencies, and generate production-grade interactive Plotly visualizations.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    dataset_id = st.session_state.get("selected_dataset_id")
    if not dataset_id:
        st.warning("No dataset selected. Please select or upload a dataset first.")
        return

    # Fetch statistics and schema
    stats_data, err = api_client.get_statistics(dataset_id)
    if err:
        st.error(f"Failed to calculate statistics: {err}")
        return

    preview, p_err = api_client.get_preview(dataset_id)
    if p_err:
        st.error(p_err)
        return

    columns = preview["columns"]

    tab_stats, tab_charts, tab_corr = st.tabs([
        "📊 Descriptive Statistics",
        "📈 Interactive Visualizations",
        "🔥 Correlation Matrix"
    ])

    with tab_stats:
        st.markdown("#### Numerical Feature Statistics")
        num_stats = stats_data.get("numerical_stats", [])
        if num_stats:
            num_rows = []
            for s in num_stats:
                num_rows.append({
                    "Column": s["column"],
                    "Count": f"{s['count']:,}",
                    "Mean": f"{s['mean']:,.2f}" if s["mean"] is not None else "N/A",
                    "Std Dev": f"{s['std']:,.2f}" if s["std"] is not None else "N/A",
                    "Min": f"{s['min']:,.2f}" if s["min"] is not None else "N/A",
                    "25%": f"{s['q25']:,.2f}" if s["q25"] is not None else "N/A",
                    "Median": f"{s['median']:,.2f}" if s["median"] is not None else "N/A",
                    "75%": f"{s['q75']:,.2f}" if s["q75"] is not None else "N/A",
                    "Max": f"{s['max']:,.2f}" if s["max"] is not None else "N/A",
                    "Missing": s["missing_count"],
                    "Unique": s["unique_count"]
                })
            st.dataframe(pd.DataFrame(num_rows), use_container_width=True, hide_index=True)
        else:
            st.info("No numerical columns found in this dataset.")

        st.markdown("#### Categorical Feature Frequencies")
        cat_stats = stats_data.get("categorical_stats", [])
        if cat_stats:
            for c in cat_stats:
                with st.expander(f"📌 Column: {c['column']} ({c['unique_count']} unique values, {c['missing_count']} missing)"):
                    top_vals = c["top_values"]
                    if top_vals:
                        cat_df = pd.DataFrame([{"Value": k, "Frequency": v} for k, v in top_vals.items()])
                        st.dataframe(cat_df, use_container_width=True, hide_index=True)
                    else:
                        st.caption("No values recorded.")
        else:
            st.info("No categorical columns found in this dataset.")

    with tab_charts:
        st.markdown("#### Dynamic Chart Builder")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            chart_type = st.selectbox(
                "Chart Type:",
                ["Histogram", "Scatter", "Bar", "Line", "Box", "Pie"]
            )
        with c2:
            x_col = st.selectbox("X-Axis Feature:", columns)
        with c3:
            # Y-axis optional for histogram, required for scatter/line
            y_options = ["None"] + columns
            default_y = 1 if len(columns) > 1 and chart_type in ["Scatter", "Line"] else 0
            y_col = st.selectbox("Y-Axis Feature:", y_options, index=default_y)
        with c4:
            group_options = ["None"] + columns
            group_col = st.selectbox("Group / Color By (Optional):", group_options)

        title_input = st.text_input("Chart Title (Optional):", value="")

        if st.button("🎨 Render Visualization", type="primary"):
            chart_payload = {
                "chart_type": chart_type.lower(),
                "x_column": x_col,
                "y_column": y_col if y_col != "None" else None,
                "group_column": group_col if group_col != "None" else None,
                "title": title_input if title_input.strip() else None
            }
            with st.spinner("Generating Plotly chart from backend..."):
                chart_res, c_err = api_client.generate_visualization(dataset_id, chart_payload)
                if c_err:
                    st.error(c_err)
                else:
                    render_plotly_json(chart_res["figure_json"])

    with tab_corr:
        st.markdown("#### Correlation Matrix")
        corr_data = stats_data.get("correlation_matrix")
        if corr_data:
            corr_df = pd.DataFrame(corr_data)
            st.dataframe(corr_df.style.background_gradient(cmap="Blues"), use_container_width=True)
        else:
            st.info("At least 2 numerical columns are required to compute correlations.")
