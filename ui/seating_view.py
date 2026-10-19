"""Seating Plan view: Interactive 2D room layouts, student seat locator, and rosters."""
import streamlit as st
import pandas as pd
from data.storage import DataStorage
from csp.models import ScheduleResult, Room
from ui.components import render_header, render_interactive_grid, get_subject_badge_class


def render_seating_plan(storage: DataStorage):
    render_header(
        title="Interactive Examination Seating Plan",
        subtitle="Visual 2D room layouts, anti-cheating subject interleaving, and student desk locator",
        icon="🪑",
    )

    if "schedule_result" not in st.session_state or st.session_state.schedule_result is None or not st.session_state.schedule_result.success:
        st.warning("⚠️ No valid schedule has been generated yet. Please go to 'Generate Schedule' first!")
        if st.button("Go to Generate Schedule", type="primary"):
            st.session_state.nav_page = "Generate Schedule"
            st.rerun()
        return

    result: ScheduleResult = st.session_state.schedule_result
    seating = result.seating_assignments
    rooms = storage.load_rooms()
    room_map = {r.room_id: r for r in rooms}

    # Distinct slots
    slots = sorted(list(set(a.slot_key for a in seating)))

    # -------------------------------------------------------------------------
    # Feature 1: "Find My Seat" Student Desk Locator
    # -------------------------------------------------------------------------
    st.subheader("🔍 Find My Seat (Student Exam Desk Locator)")
    with st.container():
        loc_col1, loc_col2 = st.columns([2.5, 1])
        with loc_col1:
            search_query = st.text_input(
                "Enter Student ID or Full Name",
                placeholder="e.g. CS-01 or Aarav Sharma",
            ).strip().lower()

        if search_query:
            matches = [
                a for a in seating
                if search_query in a.student_id.lower() or search_query in a.student_name.lower()
            ]
            if matches:
                st.success(f"Found {len(matches)} scheduled exam(s):")
                m_cols = st.columns(min(len(matches), 3))
                for idx, match in enumerate(matches):
                    col = m_cols[idx % len(m_cols)]
                    with col:
                        st.markdown(
                            f"""
                            <div style="background:#FFFFFF; border:2px solid #5B21B6; border-radius:10px; padding:14px; box-shadow:0 3px 8px rgba(91,33,182,0.1);">
                                <div style="font-size:0.75rem; text-transform:uppercase; color:#6B7280; font-weight:700;">Student Desk Slip</div>
                                <div style="font-size:1.15rem; font-weight:800; color:#5B21B6; margin:4px 0;">{match.student_name}</div>
                                <div style="font-size:0.85rem; color:#4B5563;"><strong>ID:</strong> {match.student_id}</div>
                                <hr style="margin:8px 0; border:none; border-top:1px dashed #E5E7EB;"/>
                                <div style="font-size:0.9rem; font-weight:700; color:#0D9488;">{match.exam_code} - {match.subject_name}</div>
                                <div style="font-size:0.82rem; color:#4B5563; margin-top:2px;">📅 {match.slot_key}</div>
                                <div style="margin-top:10px; background:#F3E8FF; border-radius:6px; padding:8px; text-align:center;">
                                    <span style="font-size:0.8rem; color:#5B21B6; font-weight:600;">ASSIGNED SEAT</span><br/>
                                    <strong style="font-size:1.25rem; color:#4C1D95;">{match.room_id} &bull; {match.seat_label}</strong>
                                    <div style="font-size:0.75rem; color:#6B21A8;">Row {match.row}, Column {match.col}</div>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
            else:
                st.info(f"No scheduled seats found matching '{search_query}'.")

    st.markdown("---")

    # -------------------------------------------------------------------------
    # Feature 2: 2D Visual Seating Grid by Slot and Room
    # -------------------------------------------------------------------------
    st.subheader("🗺️ 2D Interactive Room Seating Layout")

    f_col1, f_col2 = st.columns([2, 2])
    with f_col1:
        selected_slot = st.selectbox("Select Exam Date & Time Slot", slots)

    # Active rooms in selected slot
    slot_assignments = [a for a in seating if a.slot_key == selected_slot]
    slot_room_ids = sorted(list(set(a.room_id for a in slot_assignments)))

    with f_col2:
        selected_room_id = st.selectbox("Select Examination Hall", slot_room_ids) if slot_room_ids else None

    if selected_room_id and selected_room_id in room_map:
        room_obj = room_map[selected_room_id]
        room_seatings = [a for a in slot_assignments if a.room_id == selected_room_id]

        # Subject legend for this room
        room_exams = sorted(list(set(a.exam_code for a in room_seatings)))
        legend_html = ['<div style="display:flex; gap:10px; flex-wrap:wrap; margin-bottom:12px;"><strong>Subject Cohorts:</strong>']
        for ex in room_exams:
            cls = get_subject_badge_class(ex)
            legend_html.append(f'<span class="seat-tag {cls}" style="padding:4px 10px; font-size:0.8rem;">{ex}</span>')
        legend_html.append('</div>')
        st.markdown("".join(legend_html), unsafe_allow_html=True)

        render_interactive_grid(room_obj, room_seatings)
    else:
        st.info("No active examination halls for this slot.")

    st.markdown("---")

    # -------------------------------------------------------------------------
    # Feature 3: Full Seating Roster Table & CSV Export
    # -------------------------------------------------------------------------
    st.subheader("📋 Complete Master Seating Roster")

    table_data = [a.to_dict() for a in seating]
    df = pd.DataFrame(table_data)

    df_display = df.rename(columns={
        "student_id": "Student ID",
        "student_name": "Student Name",
        "exam_code": "Exam Code",
        "subject_name": "Subject Name",
        "slot_key": "Slot Key",
        "room_id": "Room",
        "row": "Row",
        "col": "Col",
        "seat_label": "Seat Label",
    })

    st.dataframe(df_display, use_container_width=True, hide_index=True)

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download Seating Roster (CSV)",
        data=csv_bytes,
        file_name="master_seating_schedule.csv",
        mime="text/csv",
        use_container_width=True,
    )
