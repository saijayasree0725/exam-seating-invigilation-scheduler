"""Invigilation Duties view: Room supervisors, workload balance, and duty allocations."""
import streamlit as st
import pandas as pd
from data.storage import DataStorage
from csp.models import ScheduleResult
from ui.components import render_header, render_metric_card


def render_invigilation_duties(storage: DataStorage):
    render_header(
        title="Invigilation Duties & Faculty Allocations",
        subtitle="Manage room supervisors, verify workload equity, and review duty distribution",
        icon="👨‍🏫",
    )

    if "schedule_result" not in st.session_state or st.session_state.schedule_result is None or not st.session_state.schedule_result.success:
        st.warning("⚠️ No valid schedule has been generated yet. Please go to 'Generate Schedule' first!")
        if st.button("Go to Generate Schedule", type="primary"):
            st.session_state.nav_page = "Generate Schedule"
            st.rerun()
        return

    result: ScheduleResult = st.session_state.schedule_result
    invigilations = result.invigilation_assignments
    faculty = storage.load_faculty()
    fac_map = {f.faculty_id: f for f in faculty}

    # Summary KPIs
    tot_duties = len(invigilations)
    active_supervisors = len(set(i.faculty_id for i in invigilations))
    fac_workload_m = result.metrics.get("workload_metrics", {})

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(render_metric_card("Total Exam Duties", tot_duties, "Across all exam rooms"), unsafe_allow_html=True)
    with k2:
        st.markdown(render_metric_card("Assigned Faculty", active_supervisors, f"Out of {len(faculty)} faculty"), unsafe_allow_html=True)
    with k3:
        st.markdown(render_metric_card("Fairness Score", f"{fac_workload_m.get('score', 100)}%", "StdDev: " + str(fac_workload_m.get("std_dev", 0))), unsafe_allow_html=True)
    with k4:
        st.markdown(render_metric_card("Avg Workload", f"{fac_workload_m.get('mean_duties', 0)}", "Duties per faculty"), unsafe_allow_html=True)

    st.markdown("---")

    # Slot-wise Room Supervisor Duty Table
    st.subheader("📅 Examination Slot Duty Schedule")
    duty_data = [inv.to_dict() for inv in invigilations]
    df_duties = pd.DataFrame(duty_data)

    df_duties_display = df_duties.rename(columns={
        "slot_key": "Date & Time Slot",
        "room_id": "Examination Hall",
        "faculty_id": "Faculty ID",
        "faculty_name": "Supervisor Name",
        "department": "Department",
    })

    st.dataframe(df_duties_display, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Faculty Workload Distribution & Fairness Chart
    st.subheader("⚖️ Faculty Workload Distribution & Equity")

    duty_counts = {f.faculty_id: 0 for f in faculty}
    for inv in invigilations:
        if inv.faculty_id in duty_counts:
            duty_counts[inv.faculty_id] += 1

    chart_data = []
    for f in faculty:
        assigned = duty_counts.get(f.faculty_id, 0)
        chart_data.append({
            "Faculty": f"{f.name} ({f.faculty_id})",
            "Assigned Duties": assigned,
            "Max Duties Allowed": f.max_duties,
            "Department": f.department,
            "Utilization": f"{round((assigned / f.max_duties) * 100, 1)}%",
        })

    df_chart = pd.DataFrame(chart_data)

    c1, c2 = st.columns([2, 1.2])
    with c1:
        st.bar_chart(df_chart.set_index("Faculty")["Assigned Duties"])
    with c2:
        st.dataframe(df_chart[["Faculty", "Assigned Duties", "Max Duties Allowed", "Utilization"]], use_container_width=True, hide_index=True)

    st.markdown("---")

    # CSV Download
    csv_bytes = df_duties.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download Invigilation Duty Roster (CSV)",
        data=csv_bytes,
        file_name="invigilation_duty_schedule.csv",
        mime="text/csv",
        use_container_width=True,
    )
