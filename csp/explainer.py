"""Diagnostic and explanation engine for CSP schedule infeasibilities and bottlenecks."""
from typing import List, Dict, Set, Tuple, Optional, Any
from collections import defaultdict
from .models import Student, Exam, Room, Faculty, ConflictReport


class ScheduleExplainer:
    """Analyzes problem inputs and search failures to generate crystal-clear diagnostic reports."""

    @classmethod
    def diagnose_preconditions(
        cls,
        students: List[Student],
        exams: List[Exam],
        rooms: List[Room],
        faculty: List[Faculty],
    ) -> List[ConflictReport]:
        """Runs pre-flight checks on all hard constraints before launching search."""
        conflicts: List[ConflictReport] = []

        # 1. Student Exam Overlaps
        exam_slot_map = {e.exam_code: e.slot_key for e in exams}
        exam_title_map = {e.exam_code: e.subject_name for e in exams}

        for st in students:
            slot_exams = defaultdict(list)
            for c in st.courses:
                if c in exam_slot_map:
                    slot_exams[exam_slot_map[c]].append(c)
            for slot, c_list in slot_exams.items():
                if len(c_list) > 1:
                    conflicts.append(
                        ConflictReport(
                            conflict_type="HARD_CONSTRAINT_STUDENT_OVERLAP",
                            description=(
                                f"Student {st.name} ({st.student_id}) is enrolled in {len(c_list)} exams "
                                f"at slot '{slot}': {', '.join(c_list)}."
                            ),
                            details={
                                "student_id": st.student_id,
                                "slot": slot,
                                "exams": c_list,
                            },
                            remedy="In the Exams page, adjust the date or time slot of one of these exams so they do not overlap.",
                        )
                    )

        # 2. Room Capacity vs Students per Slot
        # Active rooms
        active_rooms = [r for r in rooms if r.is_active and r.capacity > 0]
        total_active_capacity = sum(r.capacity for r in active_rooms)

        if not active_rooms:
            conflicts.append(
                ConflictReport(
                    conflict_type="HARD_CONSTRAINT_NO_ACTIVE_ROOMS",
                    description="No active examination rooms with positive capacity are available.",
                    details={},
                    remedy="Go to the Rooms page, enable rooms, or verify rows and columns are > 0.",
                )
            )

        # Group students by slot
        slot_students: Dict[str, Set[str]] = defaultdict(set)
        for st in students:
            for c in st.courses:
                if c in exam_slot_map:
                    slot = exam_slot_map[c]
                    slot_students[slot].add(st.student_id)

        for slot, st_set in slot_students.items():
            count = len(st_set)
            if count > total_active_capacity:
                conflicts.append(
                    ConflictReport(
                        conflict_type="HARD_CONSTRAINT_CAPACITY_DEFICIT",
                        description=(
                            f"Slot '{slot}' has {count} students appearing for exams, but the total "
                            f"available capacity of all active rooms is only {total_active_capacity} seats "
                            f"(Deficit: {count - total_active_capacity} seats)."
                        ),
                        details={
                            "slot": slot,
                            "required_seats": count,
                            "available_seats": total_active_capacity,
                            "deficit": count - total_active_capacity,
                        },
                        remedy="Add more rooms in the Rooms page or re-distribute exams across additional time slots.",
                    )
                )

        # 3. Faculty Total Duty Capacity vs Minimum Required Duties
        # For each slot, calculate how many rooms will be required (best case: pack into largest rooms)
        total_estimated_rooms_needed = 0
        slot_rooms_needed: Dict[str, int] = {}

        # Sort rooms by capacity descending for packing estimate
        sorted_rooms = sorted(active_rooms, key=lambda r: r.capacity, reverse=True)

        for slot, st_set in slot_students.items():
            st_count = len(st_set)
            needed = 0
            accum = 0
            for r in sorted_rooms:
                if accum >= st_count:
                    break
                accum += r.capacity
                needed += 1
            if accum < st_count and sorted_rooms:
                needed = len(sorted_rooms)
            needed = max(1, needed) if st_count > 0 else 0
            slot_rooms_needed[slot] = needed
            total_estimated_rooms_needed += needed

        total_faculty_capacity = sum(f.max_duties for f in faculty)
        if total_faculty_capacity < total_estimated_rooms_needed:
            conflicts.append(
                ConflictReport(
                    conflict_type="HARD_CONSTRAINT_FACULTY_WORKLOAD_DEFICIT",
                    description=(
                        f"Overall schedule requires at least {total_estimated_rooms_needed} invigilation duty assignments, "
                        f"but total faculty capacity (sum of max_duties) is only {total_faculty_capacity}."
                    ),
                    details={
                        "required_duties": total_estimated_rooms_needed,
                        "faculty_capacity": total_faculty_capacity,
                        "deficit": total_estimated_rooms_needed - total_faculty_capacity,
                    },
                    remedy="Increase 'Max Duties' per faculty in the Faculty page, or add more faculty members.",
                )
            )

        # 4. Faculty Slot-by-Slot Availability Deficit
        for slot, needed_rooms in slot_rooms_needed.items():
            if needed_rooms <= 0:
                continue
            available_fac = [
                f for f in faculty
                if slot.strip().lower() not in [u.strip().lower() for u in f.unavailable_slots if u.strip()]
                and f.max_duties > 0
            ]
            if len(available_fac) < needed_rooms:
                conflicts.append(
                    ConflictReport(
                        conflict_type="HARD_CONSTRAINT_FACULTY_SLOT_DEFICIT",
                        description=(
                            f"Slot '{slot}' requires {needed_rooms} invigilators for active exam rooms, "
                            f"but only {len(available_fac)} faculty member(s) are available."
                        ),
                        details={
                            "slot": slot,
                            "needed_invigilators": needed_rooms,
                            "available_faculty_count": len(available_fac),
                            "available_faculty_names": [f.name for f in available_fac],
                        },
                        remedy=f"Adjust faculty unavailability for slot '{slot}' or add more faculty.",
                    )
                )

        return conflicts

    @classmethod
    def format_explanation_markdown(cls, conflicts: List[ConflictReport]) -> str:
        """Generates a clean, user-friendly markdown report of all detected conflicts."""
        if not conflicts:
            return "No conflicts detected. All constraints are satisfied."

        lines = [
            f"### Conflict Diagnosis: Found {len(conflicts)} Unsatisfiable Constraint(s)\n",
            "The CSP solver halted because proceeding would violate hard institutional rules:\n",
        ]

        for i, c in enumerate(conflicts, 1):
            lines.append(f"#### {i}. {c.conflict_type.replace('_', ' ').title()}")
            lines.append(f"**Issue:** {c.description}")
            if c.remedy:
                lines.append(f"> **Recommended Fix:** {c.remedy}\n")

        return "\n".join(lines)
