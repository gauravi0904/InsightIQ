import streamlit as st
import pandas as pd
from frontend.api_client import api_client
from frontend.components.metric_cards import render_metric_card
from frontend.components.tables import render_preview_table


def render_explorer_page():
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h1 style="font-size: 2rem; font-weight: 700; color: #0f172a; margin-bottom: 4px;">
                Data Explorer
            </h1>
            <p style="color: #64748b; font-size: 0.95rem;">
                Inspect column schemas, data types, missing records, duplicates, and tabular observations.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    dataset_id = st.session_state.get("selected_dataset_id")
    if not dataset_id:
        st.warning("No dataset selected. Please select or upload a dataset first.")
        return

    # Fetch preview and schema
    preview, err = api_client.get_preview(dataset_id)
    if err:
        st.error(f"Failed to load dataset preview: {err}")
        return

    schema_data, s_err = api_client.get_schema(dataset_id)
    if s_err:
        st.error(f"Failed to load schema details: {s_err}")
        return

    # Overview Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_metric_card("Total Rows", f"{preview['row_count']:,}")
    with m2:
        render_metric_card("Total Columns", str(preview['column_count']))
    with m3:
        render_metric_card("Duplicate Rows", f"{preview['duplicate_count']:,}")
    with m4:
        render_metric_card("Missing Cells", f"{preview['total_missing_cells']:,}")

    # Tabs for Explorer
    tab_overview, tab_head, tab_tail, tab_schema = st.tabs([
        "📋 Column Schema & Quality",
        "🔝 First 10 Rows (Head)",
        "🔚 Last 10 Rows (Tail)",
        "🔬 Interactive Filter & Sort"
    ])

    with tab_overview:
        st.markdown("#### Column Inventory & Data Quality")
        cols_list = schema_data["columns"]
        schema_rows = []
        for c in cols_list:
            schema_rows.append({
                "Column Name": c["name"],
                "Data Type": c["dtype"],
                "Missing Values": c["missing_count"],
                "Missing (%)": f"{c['missing_percentage']}%",
                "Unique Values": c["unique_count"],
                "Sample Values": ", ".join(str(v) for v in c.get("sample_values", []) if v is not None)
            })
        df_schema = pd.DataFrame(schema_rows)
        st.dataframe(df_schema, use_container_width=True, hide_index=True)

    with tab_head:
        st.markdown("#### Head Preview (First 10 Observations)")
        render_preview_table(preview["head"])

    with tab_tail:
        st.markdown("#### Tail Preview (Last 10 Observations)")
        render_preview_table(preview["tail"])

    with tab_schema:
        st.markdown("#### Interactive Column View")
        head_df = pd.DataFrame(preview["head"])
        if not head_df.empty:
            all_cols = list(head_df.columns)
            selected_cols = st.multiselect("Select columns to view:", all_cols, default=all_cols[:8] if len(all_cols) > 8 else all_cols)
            sort_col = st.selectbox("Sort by column:", ["None"] + selected_cols)
            ascending = st.checkbox("Ascending order", value=True)

            filtered_df = head_df[selected_cols]
            if sort_col != "None":
                filtered_df = filtered_df.sort_values(by=sort_col, ascending=ascending)

            st.dataframe(filtered_df, use_container_width=True, hide_index=True)
