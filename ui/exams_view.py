"""Exams timetable management view: Schedules, slots, and student overlap pre-checks."""
import streamlit as st
import pandas as pd
from data.storage import DataStorage
from csp.models import Exam
from csp.constraints import ConstraintValidator
from ui.components import render_header, render_conflict_card


def render_exams(storage: DataStorage):
    render_header(
        title="Examination Timetable & Slots",
        subtitle="Manage exam subjects, dates, time slots, and detect student schedule collisions",
        icon="📝",
    )

    exams = storage.load_exams()
    students = storage.load_students()

    # Pre-check for student exam overlaps
    overlap_conflicts = ConstraintValidator.validate_student_exam_conflicts(students, exams)
    if overlap_conflicts:
        st.error(f"⚠️ Warning: Found {len(overlap_conflicts)} student exam overlap conflict(s) in current timetable!")
        for i, c in enumerate(overlap_conflicts[:3], 1):
            render_conflict_card(c, index=i)
        if len(overlap_conflicts) > 3:
            st.info(f"+ {len(overlap_conflicts) - 3} more student conflicts...")
    else:
        st.success("✅ Clean Timetable: Zero student exam slot conflicts detected.")

    # Action Toolbar
    col_search, col_btn = st.columns([3, 1])
    with col_search:
        search_query = st.text_input("🔍 Search Exam", placeholder="Search by course code or subject...").lower().strip()
    with col_btn:
        st.write("")
        st.write("")
        add_modal = st.button("➕ Add Exam", use_container_width=True, type="primary")

    if "show_add_exam" not in st.session_state:
        st.session_state.show_add_exam = False

    if add_modal:
        st.session_state.show_add_exam = not st.session_state.show_add_exam

    if st.session_state.show_add_exam:
        with st.form("add_exam_form", clear_on_submit=True):
            st.subheader("Add New Examination")
            c1, c2 = st.columns(2)
            with c1:
                e_code = st.text_input("Course Code (e.g. CS401)", "").strip().upper()
                e_name = st.text_input("Subject Title", "").strip()
                e_dept = st.text_input("Department", "Computer Science").strip()
            with c2:
                e_date = st.date_input("Exam Date").strftime("%Y-%m-%d")
                e_slot = st.selectbox("Time Slot", [
                    "Morning (09:30 - 12:30)",
                    "Afternoon (01:30 - 04:30)",
                    "Evening (05:00 - 08:00)",
                ])
                e_dur = st.number_input("Duration (Hours)", min_value=1.0, max_value=4.0, value=3.0, step=0.5)

            submitted = st.form_submit_button("Save Exam", type="primary")
            if submitted:
                if not e_code or not e_name:
                    st.error("Course Code and Subject Title are required.")
                elif any(e.exam_code == e_code for e in exams):
                    st.error(f"Exam Code '{e_code}' already exists!")
                else:
                    exams.append(Exam(exam_code=e_code, subject_name=e_name, department=e_dept, date=e_date, time_slot=e_slot, duration_hours=e_dur))
                    storage.save_exams(exams)
                    st.session_state.show_add_exam = False
                    st.success(f"Added exam '{e_name}' successfully!")
                    st.rerun()

    # Filtered exams
    filtered_exams = exams
    if search_query:
        filtered_exams = [
            e for e in filtered_exams
            if search_query in e.exam_code.lower() or search_query in e.subject_name.lower()
        ]

    # Student Count per Exam lookup
    exam_student_count = {}
    for e in exams:
        count = sum(1 for s in students if e.exam_code in s.courses)
        exam_student_count[e.exam_code] = count

    st.write(f"Showing **{len(filtered_exams)}** exam courses:")
    data_rows = []
    for e in filtered_exams:
        data_rows.append({
            "Exam Code": e.exam_code,
            "Subject Name": e.subject_name,
            "Department": e.department,
            "Date": e.date,
            "Time Slot": e.time_slot,
            "Duration (Hrs)": e.duration_hours,
            "Enrolled Students": exam_student_count.get(e.exam_code, 0),
        })

    if data_rows:
        df = pd.DataFrame(data_rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No exams found.")

    st.markdown("---")

    # CSV Import / Export
    exp_col1, exp_col2 = st.columns(2)
    with exp_col1:
        st.subheader("📥 Export Exams (CSV)")
        export_csv_data = pd.DataFrame([e.to_dict() for e in exams]).to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download exams.csv",
            data=export_csv_data,
            file_name="exams.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with exp_col2:
        st.subheader("📤 Import Exams (CSV)")
        uploaded_file = st.file_uploader("Upload CSV file", type=["csv"], key="upload_exams_csv")
        if uploaded_file is not None:
            try:
                uploaded_df = pd.read_csv(uploaded_file)
                required_cols = {"exam_code", "subject_name", "department", "date", "time_slot"}
                if not required_cols.issubset(set(uploaded_df.columns)):
                    st.error(f"Uploaded CSV must contain columns: {', '.join(required_cols)}")
                else:
                    imported_exams = []
                    for _, row in uploaded_df.iterrows():
                        imported_exams.append(
                            Exam(
                                exam_code=str(row["exam_code"]).strip(),
                                subject_name=str(row["subject_name"]).strip(),
                                department=str(row["department"]).strip(),
                                date=str(row["date"]).strip(),
                                time_slot=str(row["time_slot"]).strip(),
                                duration_hours=float(row.get("duration_hours", 3.0) or 3.0),
                            )
                        )
                    storage.save_exams(imported_exams)
                    st.success(f"Successfully imported {len(imported_exams)} exams!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error parsing CSV: {e}")
