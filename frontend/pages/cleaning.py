import streamlit as st
import pandas as pd
from frontend.api_client import api_client
from frontend.components.tables import render_preview_table


def render_cleaning_page():
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h1 style="font-size: 2rem; font-weight: 700; color: #0f172a; margin-bottom: 4px;">
                Data Cleaning Studio
            </h1>
            <p style="color: #64748b; font-size: 0.95rem;">
                Perform reliable, non-destructive data preparation and imputation. Compare before & after metrics before committing.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    dataset_id = st.session_state.get("selected_dataset_id")
    if not dataset_id:
        st.warning("No dataset selected. Please select or upload a dataset first.")
        return

    # Fetch preview for current schema
    preview, err = api_client.get_preview(dataset_id)
    if err:
        st.error(f"Failed to load dataset: {err}")
        return

    columns = preview["columns"]
    dtypes = preview["dtypes"]

    st.markdown("### 1. Select Cleaning Operations")

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**Duplicates & Missing Records**")
        remove_dups = st.checkbox(
            f"Remove Duplicate Rows (Currently: {preview['duplicate_count']} duplicates)",
            value=preview['duplicate_count'] > 0
        )
        drop_na = st.checkbox(
            "Drop Any Rows with Missing Values",
            value=False,
            help="Removes any row that contains one or more missing values."
        )

        st.markdown("**Missing Value Imputation**")
        fill_num = st.selectbox(
            "Numerical Missing Imputation:",
            ["None", "mean", "median"],
            index=0,
            help="Fill null values in numerical columns with calculated mean or median."
        )
        fill_cat = st.selectbox(
            "Categorical Missing Imputation:",
            ["None", "mode"],
            index=0,
            help="Fill null values in categorical columns with most frequent value (mode)."
        )

    with col_b:
        st.markdown("**Column Renaming (Optional)**")
        rename_col_target = st.selectbox("Select column to rename:", ["None"] + columns)
        new_col_name = ""
        if rename_col_target != "None":
            new_col_name = st.text_input(f"New name for '{rename_col_target}':", value=rename_col_target)

        st.markdown("**Type Conversion (Optional)**")
        type_col_target = st.selectbox("Select column to convert type:", ["None"] + columns)
        target_type = None
        if type_col_target != "None":
            curr_dtype = dtypes.get(type_col_target, "")
            st.caption(f"Current type: `{curr_dtype}`")
            target_type = st.selectbox("Target type:", ["int", "float", "str", "datetime"])

    st.markdown("### 2. Destination Options")
    save_as_new = st.checkbox("Save as a brand new dataset (keeps active dataset untouched)", value=True)
    new_name = ""
    if save_as_new:
        new_name = st.text_input("New Dataset Name:", value=f"{preview['dataset_name']}_cleaned")

    # Build cleaning payload
    rename_dict = {}
    if rename_col_target != "None" and new_col_name.strip() and new_col_name.strip() != rename_col_target:
        rename_dict[rename_col_target] = new_col_name.strip()

    convert_dict = {}
    if type_col_target != "None" and target_type:
        convert_dict[type_col_target] = target_type

    payload = {
        "remove_duplicates": remove_dups,
        "fill_numeric": fill_num if fill_num != "None" else None,
        "fill_categorical": fill_cat if fill_cat != "None" else None,
        "drop_na": drop_na,
        "rename_columns": rename_dict if rename_dict else None,
        "convert_types": convert_dict if convert_dict else None,
        "save_as_new": save_as_new,
        "new_dataset_name": new_name if save_as_new else None
    }

    st.divider()

    btn_col1, btn_col2 = st.columns([1, 1])

    with btn_col1:
        if st.button("👀 Preview Cleaned Results", use_container_width=True):
            with st.spinner("Calculating cleaning transformation..."):
                preview_res, p_err = api_client.preview_clean(dataset_id, payload)
                if p_err:
                    st.error(p_err)
                else:
                    st.session_state["cleaning_preview_data"] = preview_res

    with btn_col2:
        if st.button("💾 Apply & Commit Cleaning", type="primary", use_container_width=True):
            with st.spinner("Executing non-destructive cleaning pipeline..."):
                clean_res, c_err = api_client.execute_clean(dataset_id, payload)
                if c_err:
                    st.error(c_err)
                else:
                    st.success(f"Success! {clean_res['message']}")
                    if "changes_summary" in clean_res:
                        for chg in clean_res["changes_summary"]:
                            st.write(f"• {chg}")
                    if save_as_new:
                        st.session_state["selected_dataset_id"] = clean_res["dataset_id"]
                    st.rerun()

    # Show Preview if generated
    if "cleaning_preview_data" in st.session_state:
        st.markdown("### 3. Before vs After Comparison")
        prev_data = st.session_state["cleaning_preview_data"]

        stat_c1, stat_c2, stat_c3, stat_c4 = st.columns(4)
        with stat_c1:
            diff_rows = prev_data["after_rows"] - prev_data["before_rows"]
            st.metric("Rows", f"{prev_data['after_rows']:,}", f"{diff_rows:+d} rows" if diff_rows != 0 else "Unchanged")
        with stat_c2:
            diff_cols = prev_data["after_columns"] - prev_data["before_columns"]
            st.metric("Columns", f"{prev_data['after_columns']}", f"{diff_cols:+d} cols" if diff_cols != 0 else "Unchanged")
        with stat_c3:
            diff_missing = prev_data["after_missing"] - prev_data["before_missing"]
            st.metric("Missing Cells", f"{prev_data['after_missing']:,}", f"{diff_missing:+d} cells" if diff_missing != 0 else "0", delta_color="inverse")
        with stat_c4:
            diff_dups = prev_data["after_duplicates"] - prev_data["before_duplicates"]
            st.metric("Duplicates", f"{prev_data['after_duplicates']:,}", f"{diff_dups:+d} dups" if diff_dups != 0 else "0", delta_color="inverse")

        st.markdown("**Applied Transformation Rules:**")
        for ch in prev_data["changes_summary"]:
            st.write(f"- {ch}")

        st.markdown("**Cleaned Head Preview:**")
        render_preview_table(prev_data["preview_rows"])
