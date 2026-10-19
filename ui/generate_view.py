"""Generate Schedule view: CSP solver execution, constraint validation, and conflict diagnosis."""
import streamlit as st
import time
from data.storage import DataStorage
from csp.solver import ExamCSPSolver
from ui.components import render_header, render_conflict_card, render_metric_card, render_validation_summary_card


def render_generate_schedule(storage: DataStorage):
    render_header(
        title="Generate Schedule & Constraint Satisfaction",
        subtitle="Execute backtracking search with forward checking, MRV heuristic, and constraint verification",
        icon="⚙️",
    )

    students = storage.load_students()
    exams = storage.load_exams()
    rooms = storage.load_rooms()
    faculty = storage.load_faculty()

    # Pre-computation summary
    active_rooms = [r for r in rooms if r.is_active]
    total_cap = sum(r.capacity for r in active_rooms)
    total_fac_duties = sum(f.max_duties for f in faculty)

    st.markdown(
        f"""
        <div style="background:#FFFFFF; border:1px solid #E5DFD7; border-radius:10px; padding:16px; margin-bottom:20px;">
            <div style="font-size:0.95rem; font-weight:600; color:#5B21B6; margin-bottom:8px;">Current Problem Scale & Resources:</div>
            <span style="margin-right:20px;">👥 <strong>{len(students)}</strong> Students</span>
            <span style="margin-right:20px;">📝 <strong>{len(exams)}</strong> Exams</span>
            <span style="margin-right:20px;">🏢 <strong>{len(active_rooms)}</strong> Active Halls ({total_cap} seats)</span>
            <span>👨‍🏫 <strong>{len(faculty)}</strong> Faculty ({total_fac_duties} max duties)</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Solver Options & Heuristics
    st.subheader("🎯 Heuristics & Soft Preference Configuration")
    opt_col1, opt_col2, opt_col3 = st.columns(3)

    with opt_col1:
        sep_pref = st.checkbox(
            "Anti-Cheating Seating Distance",
            value=True,
            help="Interleaves different exam cohorts so students taking the same exam do not sit adjacent to each other.",
        )
    with opt_col2:
        fair_pref = st.checkbox(
            "Faculty Workload Fairness",
            value=True,
            help="Uses least-constraining value ordering to equalize invigilation duties across faculty members.",
        )
    with opt_col3:
        pack_pref = st.checkbox(
            "Efficient Hall Utilization",
            value=True,
            help="Packs examination halls systematically to avoid leaving partially filled empty halls.",
        )

    st.markdown("---")

    # Run Solver Button
    gen_col1, gen_col2 = st.columns([1.5, 3])
    with gen_col1:
        run_solver = st.button("🚀 Run Constraint Satisfaction Solver", type="primary", use_container_width=True)

    if run_solver:
        with st.spinner("Executing CSP Backtracking Search & Constraint Propagation..."):
            progress_bar = st.progress(10)
            time.sleep(0.15)
            progress_bar.progress(40)

            solver = ExamCSPSolver(
                students=students,
                exams=exams,
                rooms=rooms,
                faculty=faculty,
                enable_seating_separation=sep_pref,
                enable_workload_balance=fair_pref,
                enable_room_packing=pack_pref,
            )

            result = solver.solve()
            st.session_state.schedule_result = result
            progress_bar.progress(100)
            time.sleep(0.1)
            progress_bar.empty()

    # Display Results if available
    if "schedule_result" in st.session_state and st.session_state.schedule_result is not None:
        result = st.session_state.schedule_result

        if result.success and result.validation_passed:
            st.markdown(
                """
                <div class="success-box">
                    <h3 style="color: #065F46; margin: 0 0 6px 0;">🎉 Optimal Schedule Generated & 100% Verified!</h3>
                    <div style="font-size: 0.95rem; color: #064E3B;">
                        Every single hard constraint was strictly validated against the generated schedule. No collisions or violations exist.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Solver Performance Metrics
            st.subheader("📊 CSP Performance & Search Metrics")
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)

            metrics = result.metrics
            with m_col1:
                st.markdown(render_metric_card("Solver Runtime", f"{metrics.get('runtime_seconds', 0)*1000:.1f} ms", "Backtracking + Propagation"), unsafe_allow_html=True)
            with m_col2:
                tot_backtracks = metrics.get('seating_backtracks', 0) + metrics.get('invigilation_backtracks', 0)
                st.markdown(render_metric_card("Backtracks", tot_backtracks, "MRV pruned dead ends"), unsafe_allow_html=True)
            with m_col3:
                prunings = metrics.get('forward_checking_prunings', 0)
                st.markdown(render_metric_card("Forward Checking", prunings, "Domain values pruned"), unsafe_allow_html=True)
            with m_col4:
                soft_score = metrics.get('soft_score', 0)
                st.markdown(render_metric_card("Composite Quality", f"{soft_score}/100", "Weighted soft score"), unsafe_allow_html=True)

            # Soft Preference Quality breakdown
            st.subheader("✨ Soft Preference Quality Assessment")
            q_col1, q_col2, q_col3 = st.columns(3)

            sep_m = metrics.get("separation_metrics", {})
            work_m = metrics.get("workload_metrics", {})
            room_m = metrics.get("room_efficiency_metrics", {})

            with q_col1:
                st.metric(
                    label="Anti-Cheating Neighbor Separation",
                    value=f"{sep_m.get('score', 0)}%",
                    help="Percentage of adjacent seats with different exams or vacant borders.",
                )
                st.caption(sep_m.get("summary", ""))

            with q_col2:
                st.metric(
                    label="Faculty Workload Balance",
                    value=f"{work_m.get('score', 0)}%",
                    help="Fairness metric based on standard deviation of assigned duties.",
                )
                st.caption(work_m.get("summary", ""))

            with q_col3:
                st.metric(
                    label="Active Room Utilization",
                    value=f"{room_m.get('score', 0)}%",
                    help="Average seat fill percentage across all utilized examination halls.",
                )
                st.caption(room_m.get("summary", ""))

            # Independent Verification Checklist
            st.subheader("🛡️ Independent Constraint Audit & Verification")
            seating_assigns = getattr(result, "seating_assignments", []) if hasattr(result, "seating_assignments") else []
            invig_assigns = getattr(result, "invigilation_assignments", []) if hasattr(result, "invigilation_assignments") else []

            from csp.validator import IndependentScheduleValidator
            val_summary = IndependentScheduleValidator.validate_schedule(
                students=students,
                exams=exams,
                rooms=rooms,
                faculty=faculty,
                seating_assignments=seating_assigns,
                invigilation_assignments=invig_assigns,
            )

            if hasattr(result, "conflicts") and result.conflicts:
                for c in result.conflicts:
                    if not any(v.conflict_type == c.conflict_type and v.description == c.description for v in val_summary.all_violations):
                        val_summary.all_violations.append(c)
                val_summary.overall_passed = False

            render_validation_summary_card(val_summary, title_prefix="Independent Audit")



            # Navigation buttons
            st.markdown("---")
            nav_col1, nav_col2, nav_col3 = st.columns(3)
            with nav_col1:
                if st.button("🪑 Explore Seating Plan", use_container_width=True, type="primary"):
                    st.session_state.nav_page = "Seating Plan"
                    st.rerun()
            with nav_col2:
                if st.button("👨‍🏫 Explore Invigilation Duties", use_container_width=True):
                    st.session_state.nav_page = "Invigilation Duties"
                    st.rerun()
            with nav_col3:
                if st.button("📄 Generate Printable Reports", use_container_width=True):
                    st.session_state.nav_page = "Reports"
                    st.rerun()

        else:
            # Solver Infeasible / Failed with detailed diagnostic explanation
            st.markdown(
                f"""
                <div class="conflict-box">
                    <h3>🛑 Schedule Infeasible: CSP Constraints Violated</h3>
                    <div style="font-size: 0.95rem; color: #4B1220;">
                        The CSP solver halted because no assignment exists that satisfies all hard constraints simultaneously.
                        Rather than silently violating institutional rules, here is the exact diagnostic breakdown:
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            for i, c in enumerate(result.conflicts, 1):
                render_conflict_card(c, index=i)

            st.info("💡 To resolve these issues, make the recommended adjustments in Students, Exams, Rooms, or Faculty pages, then re-run the solver.")
    else:
        st.info("Click **'Run Constraint Satisfaction Solver'** above to compute the optimal exam schedule.")
