"""Hard constraints and soft preference definitions for Exam Seating and Invigilation."""
from typing import List, Dict, Set, Tuple, Optional, Any
from collections import defaultdict
import math
from .models import (
    Student,
    Exam,
    Room,
    Faculty,
    StudentSeatAssignment,
    InvigilationAssignment,
    ConflictReport,
)


class ConstraintValidator:
    """Rigorous validator checking every hard constraint and scoring soft preferences."""

    @staticmethod
    def validate_student_exam_conflicts(
        students: List[Student], exams: List[Exam]
    ) -> List[ConflictReport]:
        """Hard Constraint 1: A student cannot be assigned to overlapping exams in the same slot."""
        conflicts = []
        exam_slot_map = {e.exam_code: e.slot_key for e in exams}
        exam_name_map = {e.exam_code: e.subject_name for e in exams}

        for student in students:
            slot_to_exams: Dict[str, List[str]] = defaultdict(list)
            for course_id in student.courses:
                if course_id in exam_slot_map:
                    slot = exam_slot_map[course_id]
                    slot_to_exams[slot].append(course_id)

            for slot, course_list in slot_to_exams.items():
                if len(course_list) > 1:
                    exam_titles = [f"{c} ({exam_name_map.get(c, c)})" for c in course_list]
                    conflicts.append(
                        ConflictReport(
                            conflict_type="STUDENT_EXAM_OVERLAP",
                            description=(
                                f"Student {student.name} ({student.student_id}) is enrolled in multiple exams "
                                f"scheduled at the exact same slot [{slot}]: {', '.join(exam_titles)}."
                            ),
                            details={
                                "student_id": student.student_id,
                                "student_name": student.name,
                                "slot": slot,
                                "exams": course_list,
                            },
                            remedy=(
                                f"Move one of the overlapping exams ({', '.join(course_list)}) "
                                f"to a different date or time slot in the Exams page."
                            ),
                        )
                    )
        return conflicts

    @staticmethod
    def validate_seat_uniqueness(
        assignments: List[StudentSeatAssignment],
    ) -> List[ConflictReport]:
        """Hard Constraint 2: Seats cannot be assigned to more than one student in the same slot."""
        conflicts = []
        # Key: (slot_key, room_id, row, col) -> List[StudentSeatAssignment]
        seat_occupancy: Dict[Tuple[str, str, int, int], List[StudentSeatAssignment]] = defaultdict(list)

        for assign in assignments:
            key = (assign.slot_key, assign.room_id, assign.row, assign.col)
            seat_occupancy[key].append(assign)

        for (slot, room, r, c), occupant_list in seat_occupancy.items():
            if len(occupant_list) > 1:
                names = [f"{a.student_name} ({a.student_id})" for a in occupant_list]
                conflicts.append(
                    ConflictReport(
                        conflict_type="SEAT_COLLISION",
                        description=(
                            f"Room {room} Seat (Row {r}, Col {c}) at slot [{slot}] was assigned to "
                            f"{len(occupant_list)} students: {', '.join(names)}."
                        ),
                        details={
                            "room_id": room,
                            "row": r,
                            "col": c,
                            "slot": slot,
                            "students": [a.student_id for a in occupant_list],
                        },
                        remedy="Each physical seat must hold at most one student per slot.",
                    )
                )
        return conflicts

    @staticmethod
    def validate_room_capacities(
        assignments: List[StudentSeatAssignment], rooms: List[Room]
    ) -> List[ConflictReport]:
        """Hard Constraint 3: Room capacity cannot be exceeded."""
        conflicts = []
        room_cap_map = {r.room_id: r.capacity for r in rooms}
        # Key: (slot_key, room_id) -> count
        room_slot_counts: Dict[Tuple[str, str], int] = defaultdict(int)

        for a in assignments:
            room_slot_counts[(a.slot_key, a.room_id)] += 1

        for (slot, room_id), count in room_slot_counts.items():
            cap = room_cap_map.get(room_id, 0)
            if count > cap:
                conflicts.append(
                    ConflictReport(
                        conflict_type="ROOM_CAPACITY_EXCEEDED",
                        description=(
                            f"Room {room_id} has capacity {cap}, but {count} students were assigned "
                            f"for slot [{slot}]."
                        ),
                        details={
                            "room_id": room_id,
                            "capacity": cap,
                            "assigned_count": count,
                            "slot": slot,
                        },
                        remedy="Add more rooms or expand room rows/columns in Rooms page.",
                    )
                )
        return conflicts

    @staticmethod
    def validate_invigilator_slot_conflicts(
        invigilations: List[InvigilationAssignment],
    ) -> List[ConflictReport]:
        """Hard Constraint 4: An invigilator cannot supervise two rooms at the same time."""
        conflicts = []
        # Key: (faculty_id, slot_key) -> List[InvigilationAssignment]
        fac_slot_rooms: Dict[Tuple[str, str], List[InvigilationAssignment]] = defaultdict(list)

        for inv in invigilations:
            fac_slot_rooms[(inv.faculty_id, inv.slot_key)].append(inv)

        for (fac_id, slot), assigned_list in fac_slot_rooms.items():
            if len(assigned_list) > 1:
                rooms_supervised = [a.room_id for a in assigned_list]
                fac_name = assigned_list[0].faculty_name
                conflicts.append(
                    ConflictReport(
                        conflict_type="FACULTY_DOUBLE_BOOKING",
                        description=(
                            f"Faculty {fac_name} ({fac_id}) is booked for multiple rooms "
                            f"({', '.join(rooms_supervised)}) simultaneously in slot [{slot}]."
                        ),
                        details={
                            "faculty_id": fac_id,
                            "faculty_name": fac_name,
                            "slot": slot,
                            "rooms": rooms_supervised,
                        },
                        remedy="Ensure each faculty supervises at most one room per time slot.",
                    )
                )
        return conflicts

    @staticmethod
    def validate_faculty_availability(
        invigilations: List[InvigilationAssignment], faculty_list: List[Faculty]
    ) -> List[ConflictReport]:
        """Hard Constraint 5: Unavailable faculty cannot be assigned to that slot."""
        conflicts = []
        fac_map = {f.faculty_id: f for f in faculty_list}

        for inv in invigilations:
            fac = fac_map.get(inv.faculty_id)
            if fac:
                # Check normalized unavailable slot strings
                unavail_set = {u.strip().lower() for u in fac.unavailable_slots if u.strip()}
                if inv.slot_key.strip().lower() in unavail_set:
                    conflicts.append(
                        ConflictReport(
                            conflict_type="FACULTY_UNAVAILABLE",
                            description=(
                                f"Faculty {fac.name} ({fac.faculty_id}) is assigned to Room {inv.room_id} "
                                f"at slot [{inv.slot_key}], but is marked unavailable for this slot."
                            ),
                            details={
                                "faculty_id": fac.faculty_id,
                                "faculty_name": fac.name,
                                "slot": inv.slot_key,
                                "room_id": inv.room_id,
                            },
                            remedy="Respect faculty availability restrictions or adjust faculty schedule.",
                        )
                    )
        return conflicts

    @staticmethod
    def validate_faculty_workload_limits(
        invigilations: List[InvigilationAssignment], faculty_list: List[Faculty]
    ) -> List[ConflictReport]:
        """Hard Constraint 6: Faculty workload limits must be respected."""
        conflicts = []
        fac_map = {f.faculty_id: f for f in faculty_list}
        fac_duties: Dict[str, int] = defaultdict(int)

        for inv in invigilations:
            fac_duties[inv.faculty_id] += 1

        for fac_id, count in fac_duties.items():
            fac = fac_map.get(fac_id)
            if fac and count > fac.max_duties:
                conflicts.append(
                    ConflictReport(
                        conflict_type="WORKLOAD_LIMIT_EXCEEDED",
                        description=(
                            f"Faculty {fac.name} ({fac.faculty_id}) assigned {count} duties, "
                            f"exceeding max limit of {fac.max_duties}."
                        ),
                        details={
                            "faculty_id": fac_id,
                            "faculty_name": fac.name,
                            "assigned_duties": count,
                            "max_duties": fac.max_duties,
                        },
                        remedy="Increase faculty max_duties or recruit additional faculty members.",
                    )
                )
        return conflicts


class SoftPreferenceEvaluator:
    """Evaluates soft preferences: seating separation, workload fairness, room efficiency."""

    @staticmethod
    def evaluate_seating_separation(
        seating_assignments: List[StudentSeatAssignment],
    ) -> Dict[str, Any]:
        """Soft Preference 1: Avoid seating students taking the same exam subject next to one another.

        Evaluates orthogonal (left-right, front-back) neighbors in the same room.
        """
        # Map: (slot_key, room_id) -> {(row, col): exam_code}
        grid_map: Dict[Tuple[str, str], Dict[Tuple[int, int], str]] = defaultdict(dict)
        for a in seating_assignments:
            grid_map[(a.slot_key, a.room_id)][(a.row, a.col)] = a.exam_code

        total_adjacent_pairs = 0
        same_subject_adjacent_pairs = 0
        diff_subject_or_spaced_pairs = 0

        # Directions: Right (row, col+1) and Down (row+1, col)
        directions = [(0, 1), (1, 0)]

        for (slot, room_id), seats in grid_map.items():
            for (r, c), exam_code in seats.items():
                for dr, dc in directions:
                    neighbor_coord = (r + dr, c + dc)
                    if neighbor_coord in seats:
                        neighbor_exam = seats[neighbor_coord]
                        total_adjacent_pairs += 1
                        if exam_code == neighbor_exam:
                            same_subject_adjacent_pairs += 1
                        else:
                            diff_subject_or_spaced_pairs += 1

        if total_adjacent_pairs == 0:
            score = 100.0
        else:
            # Score is percentage of non-same-subject adjacent pairings
            score = (diff_subject_or_spaced_pairs / total_adjacent_pairs) * 100.0

        return {
            "score": round(score, 1),
            "total_adjacent_pairs": total_adjacent_pairs,
            "same_subject_adjacent_pairs": same_subject_adjacent_pairs,
            "separated_adjacent_pairs": diff_subject_or_spaced_pairs,
            "summary": (
                f"{score:.1f}% neighbor separation achieved "
                f"({same_subject_adjacent_pairs} same-exam adjacent collisions out of {total_adjacent_pairs} borders)."
            ),
        }

    @staticmethod
    def evaluate_workload_balance(
        invigilations: List[InvigilationAssignment], faculty_list: List[Faculty]
    ) -> Dict[str, Any]:
        """Soft Preference 2: Balance invigilation duties fairly across faculty."""
        fac_duties: Dict[str, int] = {f.faculty_id: 0 for f in faculty_list}
        for inv in invigilations:
            if inv.faculty_id in fac_duties:
                fac_duties[inv.faculty_id] += 1

        duties = list(fac_duties.values())
        if not duties:
            return {"score": 100.0, "mean": 0, "std_dev": 0, "distribution": {}}

        mean_duty = sum(duties) / len(duties)
        variance = sum((d - mean_duty) ** 2 for d in duties) / len(duties)
        std_dev = math.sqrt(variance)

        # A std_dev of 0 is a perfect 100%. A std_dev of 2.0 drops score.
        score = max(0.0, min(100.0, 100.0 - (std_dev * 25.0)))

        return {
            "score": round(score, 1),
            "mean_duties": round(mean_duty, 2),
            "std_dev": round(std_dev, 2),
            "min_duties": min(duties) if duties else 0,
            "max_duties": max(duties) if duties else 0,
            "distribution": fac_duties,
            "summary": (
                f"Workload Balance Score: {score:.1f}% "
                f"(Mean: {mean_duty:.1f} duties/faculty, StdDev: {std_dev:.2f})."
            ),
        }

    @staticmethod
    def evaluate_room_efficiency(
        seating_assignments: List[StudentSeatAssignment], rooms: List[Room]
    ) -> Dict[str, Any]:
        """Soft Preference 3: Use rooms efficiently (high fill rate for utilized rooms)."""
        room_cap_map = {r.room_id: r.capacity for r in rooms}
        slot_room_counts: Dict[Tuple[str, str], int] = defaultdict(int)

        for a in seating_assignments:
            slot_room_counts[(a.slot_key, a.room_id)] += 1

        if not slot_room_counts:
            return {"score": 100.0, "utilized_rooms": 0, "average_fill_rate": 0}

        fill_percentages = []
        for (slot, room_id), count in slot_room_counts.items():
            cap = room_cap_map.get(room_id, 1)
            pct = (count / cap) * 100.0
            fill_percentages.append(pct)

        avg_fill = sum(fill_percentages) / len(fill_percentages)
        return {
            "score": round(avg_fill, 1),
            "utilized_rooms_count": len(slot_room_counts),
            "average_fill_rate": round(avg_fill, 1),
            "summary": f"Average Active Room Fill Rate: {avg_fill:.1f}%.",
        }
