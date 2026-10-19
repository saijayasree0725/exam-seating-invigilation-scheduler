"""Students management view: CRUD, CSV import/export, and course enrollments."""
import streamlit as st
import pandas as pd
import io
from data.storage import DataStorage
from csp.models import Student
from ui.components import render_header


def render_students(storage: DataStorage):
    render_header(
        title="Student Registrations & Course Enrollments",
        subtitle="Manage examinee profiles, departments, and course enrollments",
        icon="👨‍🎓",
    )

    students = storage.load_students()
    exams = storage.load_exams()
    available_exam_codes = [e.exam_code for e in exams]

    # Toolbar: Search & Add Student
    col_search, col_dept, col_btn = st.columns([2, 1.5, 1])
    with col_search:
        search_query = st.text_input("🔍 Search Student", placeholder="Search by name or ID...").lower().strip()
    with col_dept:
        depts = sorted(list(set(s.department for s in students))) if students else []
        selected_dept = st.selectbox("Filter Department", ["All Departments"] + depts)
    with col_btn:
        st.write("")
        st.write("")
        add_modal = st.button("➕ Add Student", use_container_width=True, type="primary")

    # Add Student Form in an expander or modal
    if "show_add_student" not in st.session_state:
        st.session_state.show_add_student = False

    if add_modal:
        st.session_state.show_add_student = not st.session_state.show_add_student

    if st.session_state.show_add_student:
        with st.form("add_student_form", clear_on_submit=True):
            st.subheader("Add New Student")
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                new_id = st.text_input("Student ID (e.g. CS-99)", "").strip()
                new_name = st.text_input("Full Name", "").strip()
            with f_col2:
                new_dept = st.text_input("Department", "Computer Science").strip()
                new_courses = st.multiselect("Enrolled Exam Courses", options=available_exam_codes)

            submitted = st.form_submit_button("Save Student", type="primary")
            if submitted:
                if not new_id or not new_name:
                    st.error("Student ID and Full Name are required.")
                elif any(s.student_id == new_id for s in students):
                    st.error(f"Student ID '{new_id}' already exists!")
                else:
                    students.append(Student(student_id=new_id, name=new_name, department=new_dept, courses=new_courses))
                    storage.save_students(students)
                    st.session_state.show_add_student = False
                    st.success(f"Added student {new_name} ({new_id}) successfully!")
                    st.rerun()

    # Filtered list
    filtered_students = students
    if search_query:
        filtered_students = [
            s for s in filtered_students
            if search_query in s.name.lower() or search_query in s.student_id.lower()
        ]
    if selected_dept != "All Departments":
        filtered_students = [s for s in filtered_students if s.department == selected_dept]

    # Data Table View
    st.write(f"Showing **{len(filtered_students)}** of **{len(students)}** students:")

    if filtered_students:
        data_rows = []
        for s in filtered_students:
            data_rows.append({
                "Student ID": s.student_id,
                "Name": s.name,
                "Department": s.department,
                "Enrolled Courses": ", ".join(s.courses),
                "Exam Count": len(s.courses),
            })
        df = pd.DataFrame(data_rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No matching students found.")

    st.markdown("---")

    # CSV Import / Export Section
    exp_col1, exp_col2 = st.columns(2)

    with exp_col1:
        st.subheader("📥 Export Student Data (CSV)")
        export_csv_data = pd.DataFrame([s.to_dict() for s in students]).to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download students.csv",
            data=export_csv_data,
            file_name="students.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with exp_col2:
        st.subheader("📤 Import Student Data (CSV)")
        uploaded_file = st.file_uploader("Upload CSV file", type=["csv"], key="upload_students_csv")
        if uploaded_file is not None:
            try:
                uploaded_df = pd.read_csv(uploaded_file)
                required_cols = {"student_id", "name", "department", "courses"}
                if not required_cols.issubset(set(uploaded_df.columns)):
                    st.error(f"Uploaded CSV must contain columns: {', '.join(required_cols)}")
                else:
                    imported_students = []
                    for _, row in uploaded_df.iterrows():
                        c_raw = str(row["courses"]) if pd.notna(row["courses"]) else ""
                        c_list = [c.strip() for c in c_raw.split(";") if c.strip()]
                        imported_students.append(
                            Student(
                                student_id=str(row["student_id"]).strip(),
                                name=str(row["name"]).strip(),
                                department=str(row["department"]).strip(),
                                courses=c_list,
                            )
                        )
                    storage.save_students(imported_students)
                    st.success(f"Successfully imported {len(imported_students)} students!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error parsing CSV: {e}")
