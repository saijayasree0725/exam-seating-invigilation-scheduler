"""Dashboard view: System Overview, KPIs, CSP Architecture, and Quick Actions."""
import streamlit as st
import pandas as pd
from data.storage import DataStorage
from csp.solver import ExamCSPSolver
from ui.components import render_header, render_metric_card, render_validation_summary_card


def render_dashboard(storage: DataStorage):
    render_header(
        title="Exam Seating & Invigilation Duty Scheduling",
        subtitle="Constraint Satisfaction Problem (CSP) Solver with Backtracking & Constraint Propagation",
        icon="🏛️",
    )

    students = storage.load_students()
    exams = storage.load_exams()
    rooms = storage.load_rooms()
    faculty = storage.load_faculty()

    active_rooms = [r for r in rooms if r.is_active]
    total_capacity = sum(r.capacity for r in active_rooms)
    unique_slots = len({e.slot_key for e in exams})

    # KPI Metrics Row
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(render_metric_card("Registered Students", len(students), "Across 4 departments"), unsafe_allow_html=True)
    with col2:
        st.markdown(render_metric_card("Scheduled Exams", len(exams), f"{unique_slots} Exam Slots"), unsafe_allow_html=True)
    with col3:
        st.markdown(render_metric_card("Examination Halls", len(active_rooms), f"{total_capacity} Total Seats"), unsafe_allow_html=True)
    with col4:
        st.markdown(render_metric_card("Faculty Pool", len(faculty), "Invigilator Roster"), unsafe_allow_html=True)
    with col5:
        has_schedule = "schedule_result" in st.session_state and st.session_state.schedule_result is not None
        if has_schedule and st.session_state.schedule_result.success:
            st.markdown(render_metric_card("Schedule Status", "✅ VERIFIED", "Hard constraints 100%"), unsafe_allow_html=True)
        elif has_schedule and not st.session_state.schedule_result.success:
            st.markdown(render_metric_card("Schedule Status", "⚠️ CONFLICTS", "Infeasible constraints"), unsafe_allow_html=True)
        else:
            st.markdown(render_metric_card("Schedule Status", "⏳ PENDING", "Ready to generate"), unsafe_allow_html=True)

    st.markdown("---")

    # Quick Action Banners
    st.subheader("⚡ Quick Actions & College Data Controls")
    btn_col1, btn_col2, btn_col3 = st.columns([1.2, 1.2, 1.6])

    with btn_col1:
        if st.button("🚀 Run CSP Solver", use_container_width=True, type="primary"):
            st.session_state.nav_page = "Generate Schedule"
            st.rerun()

    with btn_col2:
        if st.button("🪑 View Seating Plan", use_container_width=True):
            st.session_state.nav_page = "Seating Plan"
            st.rerun()

    with btn_col3:
        if st.button("🔄 Reset to Default Demo Data", use_container_width=True):
            storage.reset_to_demo_data()
            if "schedule_result" in st.session_state:
                st.session_state.schedule_result = None
            st.success("Successfully reset all datasets to realistic college demo data!")
            st.rerun()

    st.markdown("---")

    # Independent Validator Audit Section
    st.subheader("🛡️ Independent Schedule Validator Audit")
    if has_schedule:
        result = st.session_state.schedule_result
        # Safely extract actual assignments without assuming result has validation_summary
        seating_assigns = getattr(result, "seating_assignments", []) if hasattr(result, "seating_assignments") else []
        invig_assigns = getattr(result, "invigilation_assignments", []) if hasattr(result, "invigilation_assignments") else []

        # Run independent validator on the actual generated schedule data
        from csp.validator import IndependentScheduleValidator
        validation_summary = IndependentScheduleValidator.validate_schedule(
            students=students,
            exams=exams,
            rooms=rooms,
            faculty=faculty,
            seating_assignments=seating_assigns,
            invigilation_assignments=invig_assigns,
        )

        # Include solver conflicts if any exist
        if hasattr(result, "conflicts") and result.conflicts:
            for c in result.conflicts:
                if not any(v.conflict_type == c.conflict_type and v.description == c.description for v in validation_summary.all_violations):
                    validation_summary.all_violations.append(c)
            validation_summary.overall_passed = False

        render_validation_summary_card(validation_summary, title_prefix="System Audit Status")
    else:
        st.info("ℹ️ No active schedule currently loaded. Click **'Run CSP Solver'** to generate and independently audit a schedule.")

    st.markdown("---")

    # CSP Technical Formulation Guide
    st.subheader("🧠 Constraint Satisfaction Problem (CSP) Formulation")
    info_col1, info_col2 = st.columns(2)

    with info_col1:
        st.markdown(
            """
            <div style="background: #FFFFFF; border: 1px solid #E5DFD7; border-radius: 10px; padding: 18px;">
                <h4 style="color: #5B21B6; margin-top: 0;">🔒 Hard Constraints (Strict Compliance)</h4>
                <ul style="font-size: 0.9rem; line-height: 1.6; color: #374151;">
                    <li><strong>No Student Overlap:</strong> A student cannot sit for two exams at the same time slot.</li>
                    <li><strong>Unique Seat Assignment:</strong> Every seat (Row, Col) in a room holds at most one student.</li>
                    <li><strong>Room Capacity:</strong> Student allocation never exceeds room capacity (Rows × Columns).</li>
                    <li><strong>No Invigilator Double-Booking:</strong> A faculty member cannot supervise two rooms simultaneously.</li>
                    <li><strong>Faculty Availability:</strong> Faculty are never assigned to slots they marked as unavailable.</li>
                    <li><strong>Workload Limit:</strong> Total assigned duties per faculty &le; max duties limit.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with info_col2:
        st.markdown(
            """
            <div style="background: #FFFFFF; border: 1px solid #E5DFD7; border-radius: 10px; padding: 18px;">
                <h4 style="color: #0D9488; margin-top: 0;">✨ Soft Preferences (Optimization Heuristics)</h4>
                <ul style="font-size: 0.9rem; line-height: 1.6; color: #374151;">
                    <li><strong>Anti-Cheating Seating Distance:</strong> Interleave different subject codes to avoid seating students taking the same exam adjacent to each other.</li>
                    <li><strong>Invigilation Workload Fairness:</strong> Balance duties evenly across all available faculty (minimizing standard deviation).</li>
                    <li><strong>Efficient Hall Packing:</strong> Consolidate students into minimum necessary examination halls to optimize resource usage.</li>
                    <li><strong>Conflict Diagnosis Engine:</strong> If a problem is mathematically infeasible, explain the root cause and provide actionable recommendations.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Solver Search Mechanics
    with st.expander("🔍 Deep Dive: CSP Backtracking Algorithm & Heuristics", expanded=False):
        st.markdown(
            """
            This project implements a genuine constraint satisfaction engine built on classical AI principles:
            - **Minimum Remaining Values (MRV):** Variables with the fewest legal values remaining are prioritized first (the *fail-first principle*).
            - **Constraint Propagation / Forward Checking:** Every time an assignment is made, incompatible values are instantly pruned from future domains. If any domain is wiped out, the algorithm prunes the entire branch immediately without wasting iterations.
            - **Least Constraining / Fairness Value Ordering:** Prefers values that leave the maximum flexibility for neighboring assignments, while maximizing workload fairness.
            """
        )
