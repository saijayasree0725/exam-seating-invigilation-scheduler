"""Reports view: Clean, printable examination hall notices, attendance rosters, and reports."""
import streamlit as st
import pandas as pd
from data.storage import DataStorage
from csp.models import ScheduleResult
from ui.components import render_header


def render_reports(storage: DataStorage):
    render_header(
        title="Official Reports & Printable Documents",
        subtitle="Generate printable room door notices, student attendance rosters, and master schedules",
        icon="📄",
    )

    if "schedule_result" not in st.session_state or st.session_state.schedule_result is None or not st.session_state.schedule_result.success:
        st.warning("⚠️ Please generate a valid schedule first under 'Generate Schedule' before viewing reports.")
        return

    result: ScheduleResult = st.session_state.schedule_result
    seating = result.seating_assignments
    invigilations = result.invigilation_assignments
    rooms = storage.load_rooms()

    # Report type selection
    report_type = st.radio(
        "Select Report Template to Preview & Print",
        [
            "🚪 Examination Room Door Notice",
            "✍️ Student Attendance & Signature Roster",
            "📜 Comprehensive Master Schedule",
        ],
        horizontal=True,
    )

    slots = sorted(list(set(a.slot_key for a in seating)))

    st.markdown("---")

    if report_type == "🚪 Examination Room Door Notice":
        st.subheader("Examination Room Door Notice (Printable)")
        col_s, col_r = st.columns(2)
        with col_s:
            sel_slot = st.selectbox("Exam Slot", slots, key="door_slot")
        slot_assigns = [a for a in seating if a.slot_key == sel_slot]
        slot_rooms = sorted(list(set(a.room_id for a in slot_assigns)))
        with col_r:
            sel_room = st.selectbox("Examination Hall", slot_rooms, key="door_room")

        room_students = [a for a in slot_assigns if a.room_id == sel_room]
        # Find invigilator for this room & slot
        inv = next((i for i in invigilations if i.slot_key == sel_slot and i.room_id == sel_room), None)
        inv_name = f"{inv.faculty_name} ({inv.department})" if inv else "Staff Assigned"

        # HTML Door Notice
        student_rows_html = "".join([
            f"<tr><td style='padding:6px 12px; border:1px solid #CBD5E1;'>{idx}</td>"
            f"<td style='padding:6px 12px; border:1px solid #CBD5E1; font-weight:700;'>{s.student_id}</td>"
            f"<td style='padding:6px 12px; border:1px solid #CBD5E1;'>{s.student_name}</td>"
            f"<td style='padding:6px 12px; border:1px solid #CBD5E1;'>{s.exam_code} ({s.subject_name})</td>"
            f"<td style='padding:6px 12px; border:1px solid #CBD5E1; text-align:center; font-weight:700; color:#5B21B6;'>{s.seat_label}</td></tr>"
            for idx, s in enumerate(room_students, 1)
        ])

        html_content = f"""
        <div style="background:#FFFFFF; border:3px solid #1E293B; border-radius:8px; padding:30px; font-family:serif; color:#0F172A; max-width:850px; margin:0 auto; box-shadow:0 4px 10px rgba(0,0,0,0.06);">
            <div style="text-align:center; border-bottom:2px solid #0F172A; padding-bottom:12px; margin-bottom:18px;">
                <h2 style="margin:0; text-transform:uppercase; letter-spacing:0.05em; color:#1E1B4B;">Office of the Controller of Examinations</h2>
                <h3 style="margin:6px 0 0 0; color:#0D9488;">EXAMINATION HALL NOTICE</h3>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:16px; font-size:1rem; border-bottom:1px solid #E2E8F0; padding-bottom:10px;">
                <div><strong>Examination Hall:</strong> <span style="font-size:1.25rem; font-weight:800; color:#5B21B6;">{sel_room}</span></div>
                <div><strong>Date & Slot:</strong> {sel_slot}</div>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:20px; font-size:0.95rem;">
                <div><strong>Total Candidates:</strong> {len(room_students)}</div>
                <div><strong>Hall Invigilator:</strong> {inv_name}</div>
            </div>
            <table style="width:100%; border-collapse:collapse; font-size:0.9rem; text-align:left;">
                <thead>
                    <tr style="background:#F1F5F9; color:#1E293B;">
                        <th style="padding:8px 12px; border:1px solid #CBD5E1;">#</th>
                        <th style="padding:8px 12px; border:1px solid #CBD5E1;">Roll No</th>
                        <th style="padding:8px 12px; border:1px solid #CBD5E1;">Candidate Name</th>
                        <th style="padding:8px 12px; border:1px solid #CBD5E1;">Subject</th>
                        <th style="padding:8px 12px; border:1px solid #CBD5E1; text-align:center;">Assigned Seat</th>
                    </tr>
                </thead>
                <tbody>
                    {student_rows_html}
                </tbody>
            </table>
            <div style="margin-top:24px; padding-top:10px; font-size:0.8rem; color:#64748B; border-top:1px dashed #CBD5E1;">
                * Notice: Mobile phones, smartwatches, and programmable devices are strictly prohibited inside the exam hall.
            </div>
        </div>
        """
        st.markdown(html_content, unsafe_allow_html=True)
        st.download_button(
            label="⬇️ Download HTML Door Notice",
            data=html_content.encode("utf-8"),
            file_name=f"door_notice_{sel_room}_{sel_slot.replace('|', '_').replace(' ', '_')}.html",
            mime="text/html",
        )

    elif report_type == "✍️ Student Attendance & Signature Roster":
        st.subheader("Candidate Attendance & Signature Roster")
        col_s, col_r = st.columns(2)
        with col_s:
            sel_slot = st.selectbox("Exam Slot", slots, key="att_slot")
        slot_assigns = [a for a in seating if a.slot_key == sel_slot]
        slot_rooms = sorted(list(set(a.room_id for a in slot_assigns)))
        with col_r:
            sel_room = st.selectbox("Examination Hall", slot_rooms, key="att_room")

        room_students = [a for a in slot_assigns if a.room_id == sel_room]
        inv = next((i for i in invigilations if i.slot_key == sel_slot and i.room_id == sel_room), None)
        inv_name = f"{inv.faculty_name} ({inv.department})" if inv else "Staff Assigned"

        att_rows_html = "".join([
            f"<tr><td style='padding:6px 10px; border:1px solid #CBD5E1;'>{idx}</td>"
            f"<td style='padding:6px 10px; border:1px solid #CBD5E1; font-weight:700;'>{s.student_id}</td>"
            f"<td style='padding:6px 10px; border:1px solid #CBD5E1;'>{s.student_name}</td>"
            f"<td style='padding:6px 10px; border:1px solid #CBD5E1;'>{s.exam_code}</td>"
            f"<td style='padding:6px 10px; border:1px solid #CBD5E1; text-align:center;'>{s.seat_label}</td>"
            f"<td style='padding:6px 10px; border:1px solid #CBD5E1; width:120px;'></td>"
            f"<td style='padding:6px 10px; border:1px solid #CBD5E1; width:120px;'></td></tr>"
            for idx, s in enumerate(room_students, 1)
        ])

        html_att = f"""
        <div style="background:#FFFFFF; border:2px solid #000; padding:25px; font-family:sans-serif; color:#000; max-width:900px; margin:0 auto;">
            <div style="text-align:center; margin-bottom:14px;">
                <h3 style="margin:0; text-transform:uppercase;">UNIVERSITY EXAMINATION BRANCH</h3>
                <h4 style="margin:4px 0 0 0; color:#333;">CANDIDATE ATTENDANCE & DESK SIGNATURE ROSTER</h4>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:14px; font-size:0.9rem; border-top:1px solid #000; border-bottom:1px solid #000; padding:8px 0;">
                <div><strong>Hall:</strong> {sel_room}</div>
                <div><strong>Slot:</strong> {sel_slot}</div>
                <div><strong>Invigilator:</strong> {inv_name}</div>
            </div>
            <table style="width:100%; border-collapse:collapse; font-size:0.85rem;">
                <thead>
                    <tr style="background:#EEE;">
                        <th style="padding:6px 10px; border:1px solid #999;">#</th>
                        <th style="padding:6px 10px; border:1px solid #999;">Roll No</th>
                        <th style="padding:6px 10px; border:1px solid #999;">Candidate Name</th>
                        <th style="padding:6px 10px; border:1px solid #999;">Exam</th>
                        <th style="padding:6px 10px; border:1px solid #999;">Seat</th>
                        <th style="padding:6px 10px; border:1px solid #999;">Booklet No.</th>
                        <th style="padding:6px 10px; border:1px solid #999;">Candidate Signature</th>
                    </tr>
                </thead>
                <tbody>
                    {att_rows_html}
                </tbody>
            </table>
            <div style="margin-top:35px; display:flex; justify-content:space-between; font-size:0.9rem;">
                <div>Candidate Present Count: _______ / {len(room_students)}</div>
                <div>Invigilator Signature: _______________________</div>
            </div>
        </div>
        """
        st.markdown(html_att, unsafe_allow_html=True)
        st.download_button(
            label="⬇️ Download Attendance Sheet (HTML)",
            data=html_att.encode("utf-8"),
            file_name=f"attendance_sheet_{sel_room}.html",
            mime="text/html",
        )

    else:
        st.subheader("Comprehensive Master Schedule")
        
        st.write(f"Total Student Seat Allocations: **{len(seating)}**")
        st.dataframe(
            pd.DataFrame([s.to_dict() for s in seating]),
            height=350,
            use_container_width=True
        )

        st.write(f"Total Invigilator Duty Allocations: **{len(invigilations)}**")
        st.dataframe(
            pd.DataFrame([i.to_dict() for i in invigilations]),
            height=300,
            use_container_width=True
        )

