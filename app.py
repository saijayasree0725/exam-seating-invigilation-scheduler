"""Main Application Entry Point: Exam Seating and Invigilation Duty Scheduling using CSP."""
import streamlit as st
import os

from data.storage import DataStorage
from ui.styles import CUSTOM_CSS
from ui.dashboard_view import render_dashboard
from ui.students_view import render_students
from ui.exams_view import render_exams
from ui.rooms_view import render_rooms
from ui.faculty_view import render_faculty
from ui.generate_view import render_generate_schedule
from ui.seating_view import render_seating_plan
from ui.invigilation_view import render_invigilation_duties
from ui.reports_view import render_reports


def main():
    st.set_page_config(
        page_title="Exam Seating & Invigilation Scheduling (CSP)",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Inject distinctive purple, teal, and warm neutral CSS
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # Initialize persistent storage
    storage = DataStorage()

    # Sidebar Navigation
    with st.sidebar:
        st.markdown(
            """
            <div style="text-align: left; padding: 10px 0 16px 0;">
                <div style="font-size: 1.25rem; font-weight: 800; color: #FFFFFF; letter-spacing: -0.02em;">
                    🎓 Exam Scheduler
                </div>
                <div style="font-size: 0.8rem; color: #14B8A6; font-weight: 600;">
                    Constraint Satisfaction AI Engine
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        nav_options = [
            "Dashboard",
            "Students",
            "Exams",
            "Rooms",
            "Faculty",
            "Generate Schedule",
            "Seating Plan",
            "Invigilation Duties",
            "Reports",
        ]

        icons = {
            "Dashboard": "📊",
            "Students": "👥",
            "Exams": "📝",
            "Rooms": "🏢",
            "Faculty": "👨‍🏫",
            "Generate Schedule": "⚙️",
            "Seating Plan": "🪑",
            "Invigilation Duties": "🛡️",
            "Reports": "📄",
        }

        # Handle page redirect from session state
        default_index = 0
        if "nav_page" in st.session_state and st.session_state.nav_page in nav_options:
            default_index = nav_options.index(st.session_state.nav_page)

        selected_page = st.radio(
            "Navigation Menu",
            nav_options,
            index=default_index,
            format_func=lambda x: f"{icons.get(x, '•')}  {x}",
        )
        st.session_state.nav_page = selected_page

        st.markdown("---")

        # Sidebar Resource Counter
        students = storage.load_students()
        exams = storage.load_exams()
        rooms = storage.load_rooms()
        faculty = storage.load_faculty()

        st.markdown(
            f"""
            <div style="background: rgba(255,255,255,0.06); border-radius: 8px; padding: 12px; font-size: 0.82rem; margin-bottom: 12px;">
                <div style="font-weight: 700; color: #14B8A6; margin-bottom: 6px;">DATASET COUNTS</div>
                <div>• Students: <strong>{len(students)}</strong></div>
                <div>• Exams: <strong>{len(exams)}</strong></div>
                <div>• Halls: <strong>{len([r for r in rooms if r.is_active])} active</strong></div>
                <div>• Faculty: <strong>{len(faculty)}</strong></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("🔄 Reset Demo Data", use_container_width=True):
            storage.reset_to_demo_data()
            if "schedule_result" in st.session_state:
                st.session_state.schedule_result = None
            st.success("Reset data to college demo dataset!")
            st.rerun()

        st.markdown(
            """
            <div style="font-size: 0.72rem; color: #9CA3AF; margin-top: 20px; line-height: 1.4;">
                <strong>Project:</strong> CSP Exam Scheduler<br/>
                <strong>Algorithms:</strong> Backtracking, MRV, Forward Checking<br/>
                <strong>Palette:</strong> Purple, Teal, Warm Neutral
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Route to selected page
    if selected_page == "Dashboard":
        render_dashboard(storage)
    elif selected_page == "Students":
        render_students(storage)
    elif selected_page == "Exams":
        render_exams(storage)
    elif selected_page == "Rooms":
        render_rooms(storage)
    elif selected_page == "Faculty":
        render_faculty(storage)
    elif selected_page == "Generate Schedule":
        render_generate_schedule(storage)
    elif selected_page == "Seating Plan":
        render_seating_plan(storage)
    elif selected_page == "Invigilation Duties":
        render_invigilation_duties(storage)
    elif selected_page == "Reports":
        render_reports(storage)


if __name__ == "__main__":
    main()
