"""Faculty management view: Invigilator pool, max duties, and slot unavailabilities."""
import streamlit as st
import pandas as pd
from data.storage import DataStorage
from csp.models import Faculty
from ui.components import render_header


def render_faculty(storage: DataStorage):
    render_header(
        title="Faculty & Invigilator Roster",
        subtitle="Manage faculty invigilators, workload quotas, and slot unavailability restrictions",
        icon="👨‍🏫",
    )

    faculty_list = storage.load_faculty()
    exams = storage.load_exams()
    distinct_slots = sorted(list({e.slot_key for e in exams}))

    total_duty_capacity = sum(f.max_duties for f in faculty_list)
    st.write(f"Total Available Faculty: **{len(faculty_list)} members** | Total Workload Capacity: **{total_duty_capacity} duties**.")

    col_search, col_btn = st.columns([3, 1])
    with col_search:
        search_query = st.text_input("🔍 Search Faculty", placeholder="Search by name or ID...").lower().strip()
    with col_btn:
        st.write("")
        st.write("")
        add_modal = st.button("➕ Add Faculty", use_container_width=True, type="primary")

    if "show_add_faculty" not in st.session_state:
        st.session_state.show_add_faculty = False

    if add_modal:
        st.session_state.show_add_faculty = not st.session_state.show_add_faculty

    if st.session_state.show_add_faculty:
        with st.form("add_faculty_form", clear_on_submit=True):
            st.subheader("Add New Faculty Member")
            c1, c2 = st.columns(2)
            with c1:
                f_id = st.text_input("Faculty ID (e.g. FAC-09)", "").strip().upper()
                f_name = st.text_input("Full Name (e.g. Dr. Rajesh Verma)", "").strip()
                f_dept = st.text_input("Department", "Computer Science").strip()
            with c2:
                f_max = st.number_input("Max Duty Limit", min_value=1, max_value=10, value=3, step=1)
                f_unavail = st.multiselect("Mark Unavailable for Slots", options=distinct_slots)

            submitted = st.form_submit_button("Save Faculty Member", type="primary")
            if submitted:
                if not f_id or not f_name:
                    st.error("Faculty ID and Full Name are required.")
                elif any(f.faculty_id == f_id for f in faculty_list):
                    st.error(f"Faculty ID '{f_id}' already exists!")
                else:
                    faculty_list.append(Faculty(faculty_id=f_id, name=f_name, department=f_dept, max_duties=int(f_max), unavailable_slots=f_unavail))
                    storage.save_faculty(faculty_list)
                    st.session_state.show_add_faculty = False
                    st.success(f"Added {f_name} successfully!")
                    st.rerun()

    filtered_faculty = faculty_list
    if search_query:
        filtered_faculty = [
            f for f in filtered_faculty
            if search_query in f.name.lower() or search_query in f.faculty_id.lower()
        ]

    data_rows = []
    for f in filtered_faculty:
        data_rows.append({
            "Faculty ID": f.faculty_id,
            "Name": f.name,
            "Department": f.department,
            "Max Duties": f.max_duties,
            "Unavailable Slots": "; ".join(f.unavailable_slots) if f.unavailable_slots else "None (Fully Available)",
        })

    if data_rows:
        df = pd.DataFrame(data_rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No faculty found.")

    st.markdown("---")

    # CSV Import / Export
    exp_col1, exp_col2 = st.columns(2)
    with exp_col1:
        st.subheader("📥 Export Faculty (CSV)")
        export_csv_data = pd.DataFrame([f.to_dict() for f in faculty_list]).to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download faculty.csv",
            data=export_csv_data,
            file_name="faculty.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with exp_col2:
        st.subheader("📤 Import Faculty (CSV)")
        uploaded_file = st.file_uploader("Upload CSV file", type=["csv"], key="upload_faculty_csv")
        if uploaded_file is not None:
            try:
                uploaded_df = pd.read_csv(uploaded_file)
                required_cols = {"faculty_id", "name", "department", "max_duties"}
                if not required_cols.issubset(set(uploaded_df.columns)):
                    st.error(f"Uploaded CSV must contain columns: {', '.join(required_cols)}")
                else:
                    imported_faculty = []
                    for _, row in uploaded_df.iterrows():
                        u_raw = str(row.get("unavailable_slots", "")) if pd.notna(row.get("unavailable_slots")) else ""
                        u_list = [u.strip() for u in u_raw.split(";") if u.strip()]
                        imported_faculty.append(
                            Faculty(
                                faculty_id=str(row["faculty_id"]).strip(),
                                name=str(row["name"]).strip(),
                                department=str(row["department"]).strip(),
                                max_duties=int(row["max_duties"]),
                                unavailable_slots=u_list,
                            )
                        )
                    storage.save_faculty(imported_faculty)
                    st.success(f"Successfully imported {len(imported_faculty)} faculty members!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error parsing CSV: {e}")
