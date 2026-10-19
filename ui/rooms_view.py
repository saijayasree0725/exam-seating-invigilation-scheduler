"""Rooms & Examination Halls management view: Grids, rows, columns, and capacity."""
import streamlit as st
import pandas as pd
from data.storage import DataStorage
from csp.models import Room
from ui.components import render_header


def render_rooms(storage: DataStorage):
    render_header(
        title="Examination Halls & Room Capacities",
        subtitle="Manage physical room dimensions, row-column seating matrices, and active hall status",
        icon="🏢",
    )

    rooms = storage.load_rooms()
    active_rooms = [r for r in rooms if r.is_active]
    total_active_seats = sum(r.capacity for r in active_rooms)

    st.write(f"Active Examination Capacity: **{total_active_seats} seats** across **{len(active_rooms)} active halls**.")

    col_search, col_btn = st.columns([3, 1])
    with col_search:
        search_query = st.text_input("🔍 Search Room", placeholder="Search by Room ID or building...").lower().strip()
    with col_btn:
        st.write("")
        st.write("")
        add_modal = st.button("➕ Add Room", use_container_width=True, type="primary")

    if "show_add_room" not in st.session_state:
        st.session_state.show_add_room = False

    if add_modal:
        st.session_state.show_add_room = not st.session_state.show_add_room

    if st.session_state.show_add_room:
        with st.form("add_room_form", clear_on_submit=True):
            st.subheader("Add New Examination Hall")
            c1, c2 = st.columns(2)
            with c1:
                r_id = st.text_input("Room ID / Number (e.g. LH-301)", "").strip().upper()
                r_bldg = st.text_input("Building / Block", "Main Academic Block").strip()
            with c2:
                r_rows = st.number_input("Number of Rows", min_value=1, max_value=20, value=5, step=1)
                r_cols = st.number_input("Number of Columns", min_value=1, max_value=20, value=5, step=1)
                r_cap = r_rows * r_cols
                st.info(f"Calculated Seat Capacity: {r_cap} seats")

            submitted = st.form_submit_button("Save Examination Hall", type="primary")
            if submitted:
                if not r_id:
                    st.error("Room ID is required.")
                elif any(r.room_id == r_id for r in rooms):
                    st.error(f"Room ID '{r_id}' already exists!")
                else:
                    rooms.append(Room(room_id=r_id, building=r_bldg, rows=int(r_rows), cols=int(r_cols), capacity=r_cap, is_active=True))
                    storage.save_rooms(rooms)
                    st.session_state.show_add_room = False
                    st.success(f"Added room '{r_id}' ({r_cap} seats) successfully!")
                    st.rerun()

    filtered_rooms = rooms
    if search_query:
        filtered_rooms = [
            r for r in filtered_rooms
            if search_query in r.room_id.lower() or search_query in r.building.lower()
        ]

    data_rows = []
    for r in filtered_rooms:
        data_rows.append({
            "Room ID": r.room_id,
            "Building": r.building,
            "Rows": r.rows,
            "Columns": r.cols,
            "Capacity": r.capacity,
            "Active Status": "Active ✅" if r.is_active else "Disabled ❌",
        })

    if data_rows:
        df = pd.DataFrame(data_rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No rooms found.")

    st.markdown("---")

    # CSV Import / Export
    exp_col1, exp_col2 = st.columns(2)
    with exp_col1:
        st.subheader("📥 Export Rooms (CSV)")
        export_csv_data = pd.DataFrame([r.to_dict() for r in rooms]).to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download rooms.csv",
            data=export_csv_data,
            file_name="rooms.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with exp_col2:
        st.subheader("📤 Import Rooms (CSV)")
        uploaded_file = st.file_uploader("Upload CSV file", type=["csv"], key="upload_rooms_csv")
        if uploaded_file is not None:
            try:
                uploaded_df = pd.read_csv(uploaded_file)
                required_cols = {"room_id", "building", "rows", "cols"}
                if not required_cols.issubset(set(uploaded_df.columns)):
                    st.error(f"Uploaded CSV must contain columns: {', '.join(required_cols)}")
                else:
                    imported_rooms = []
                    for _, row in uploaded_df.iterrows():
                        r = int(row["rows"])
                        c = int(row["cols"])
                        cap = int(row.get("capacity", r * c) or (r * c))
                        act = str(row.get("is_active", "Yes")).strip().lower() in ["yes", "true", "1"]
                        imported_rooms.append(
                            Room(
                                room_id=str(row["room_id"]).strip(),
                                building=str(row["building"]).strip(),
                                rows=r,
                                cols=c,
                                capacity=cap,
                                is_active=act,
                            )
                        )
                    storage.save_rooms(imported_rooms)
                    st.success(f"Successfully imported {len(imported_rooms)} rooms!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error parsing CSV: {e}")
