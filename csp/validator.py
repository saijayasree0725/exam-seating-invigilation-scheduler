"""Independent Schedule Validator for Exam Seating and Invigilation Duties.

Provides an external, decoupled, non-bypassable verification engine that audits
any generated or imported schedule against all hard physical & institutional rules,
as well as assessing duty fairness from actual assignments.
"""
from typing import List, Dict, Set, Tuple, Optional, Any
from collections import defaultdict
from dataclasses import dataclass, field
import datetime
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


@dataclass
class ValidationCheckResult:
    check_id: str
    check_name: str
    category: str  # "HARD" or "SOFT"
    passed: bool
    summary: str
    violations: List[ConflictReport] = field(default_factory=list)


@dataclass
class ValidationSummary:
    overall_passed: bool
    timestamp: str
    total_hard_checks: int
    passed_hard_checks: int
    failed_hard_checks: int
    check_results: List[ValidationCheckResult] = field(default_factory=list)
    all_violations: List[ConflictReport] = field(default_factory=list)
    fairness_metrics: Dict[str, Any] = field(default_factory=dict)
    summary_message: str = ""


class IndependentScheduleValidator:
    """Decoupled verification engine that independently validates schedules."""

    @classmethod
    def validate_schedule(
        cls,
        students: List[Student],
        exams: List[Exam],
        rooms: List[Room],
        faculty: List[Faculty],
        seating_assignments: List[StudentSeatAssignment],
        invigilation_assignments: List[InvigilationAssignment],
    ) -> ValidationSummary:
        """Runs the complete suite of independent validation checks."""
        check_results: List[ValidationCheckResult] = []
        all_violations: List[ConflictReport] = []

        # 1. Room Capacity Compliance
        cap_result = cls.check_room_capacity(rooms, seating_assignments)
        check_results.append(cap_result)
        all_violations.extend(cap_result.violations)

        # 2. Duplicate Seat Invariant (No 2 students in same seat at same slot)
        seat_dup_result = cls.check_duplicate_seats(seating_assignments)
        check_results.append(seat_dup_result)
        all_violations.extend(seat_dup_result.violations)

        # 3. Seat Grid Physical Bounds (Row <= room.rows, Col <= room.cols)
        bounds_result = cls.check_seat_bounds(rooms, seating_assignments)
        check_results.append(bounds_result)
        all_violations.extend(bounds_result.violations)

        # 4. Student Exam Overlaps
        overlap_result = cls.check_student_exam_overlaps(students, exams, seating_assignments)
        check_results.append(overlap_result)
        all_violations.extend(overlap_result.violations)

        # 5. Invigilator Double-Booking (Simultaneous rooms)
        double_book_result = cls.check_invigilator_double_booking(invigilation_assignments)
        check_results.append(double_book_result)
        all_violations.extend(double_book_result.violations)

        # 6. Faculty Availability Compliance
        avail_result = cls.check_faculty_availability(faculty, invigilation_assignments)
        check_results.append(avail_result)
        all_violations.extend(avail_result.violations)

        # 7. Faculty Workload Limits
        workload_result = cls.check_faculty_workload_limits(faculty, invigilation_assignments)
        check_results.append(workload_result)
        all_violations.extend(workload_result.violations)

        # 8. Examinee Seating & Room Supervision Coverage
        if students and exams and (seating_assignments or invigilation_assignments):
            coverage_result = cls.check_schedule_coverage(students, exams, seating_assignments, invigilation_assignments)
            check_results.append(coverage_result)
            all_violations.extend(coverage_result.violations)

        # Calculate actual duty distribution fairness
        fairness = cls.calculate_actual_duty_fairness(faculty, invigilation_assignments)

        # Summary counts
        hard_checks = [c for c in check_results if c.category == "HARD"]
        passed_hard = sum(1 for c in hard_checks if c.passed)
        failed_hard = sum(1 for c in hard_checks if not c.passed)
        overall_passed = (failed_hard == 0)

        timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if overall_passed:
            summary_msg = f"PASS: All {len(hard_checks)} hard constraints strictly verified."
        else:
            summary_msg = f"FAIL: {failed_hard} out of {len(hard_checks)} hard constraints violated."

        return ValidationSummary(
            overall_passed=overall_passed,
            timestamp=timestamp_str,
            total_hard_checks=len(hard_checks),
            passed_hard_checks=passed_hard,
            failed_hard_checks=failed_hard,
            check_results=check_results,
            all_violations=all_violations,
            fairness_metrics=fairness,
            summary_message=summary_msg,
        )

    # -------------------------------------------------------------------------
    # Individual Independent Checks
    # -------------------------------------------------------------------------
    @classmethod
    def check_room_capacity(
        cls, rooms: List[Room], seating: List[StudentSeatAssignment]
    ) -> ValidationCheckResult:
        """Verifies no examination room exceeds its physical capacity in any slot."""
        room_cap_map = {r.room_id: r.capacity for r in rooms}
        slot_room_counts: Dict[Tuple[str, str], int] = defaultdict(int)

        for a in seating:
            slot_room_counts[(a.slot_key, a.room_id)] += 1

        violations = []
        for (slot, room_id), count in slot_room_counts.items():
            cap = room_cap_map.get(room_id, 0)
            if count > cap:
                violations.append(
                    ConflictReport(
                        conflict_type="ROOM_CAPACITY_EXCEEDED",
                        description=(
                            f"Room '{room_id}' capacity is {cap}, but {count} students were assigned "
                            f"for slot [{slot}]."
                        ),
                        details={"room_id": room_id, "capacity": cap, "count": count, "slot": slot},
                        remedy=f"Expand capacity of {room_id} or assign overflow to an additional hall.",
                    )
                )

        passed = len(violations) == 0
        summary = (
            "All rooms strictly within physical capacity limits."
            if passed
            else f"{len(violations)} room capacity violation(s) detected!"
        )
        return ValidationCheckResult(
            check_id="CHK_ROOM_CAPACITY",
            check_name="Room Capacity Limits",
            category="HARD",
            passed=passed,
            summary=summary,
            violations=violations,
        )

    @classmethod
    def check_duplicate_seats(
        cls, seating: List[StudentSeatAssignment]
    ) -> ValidationCheckResult:
        """Verifies no two students are assigned the exact same seat in the same slot."""
        seat_map: Dict[Tuple[str, str, int, int], List[StudentSeatAssignment]] = defaultdict(list)
        for a in seating:
            key = (a.slot_key, a.room_id, a.row, a.col)
            seat_map[key].append(a)

        violations = []
        for (slot, room, r, c), assigns in seat_map.items():
            if len(assigns) > 1:
                names = [f"{x.student_name} ({x.student_id})" for x in assigns]
                violations.append(
                    ConflictReport(
                        conflict_type="DUPLICATE_SEAT_ASSIGNMENT",
                        description=(
                            f"Seat ({room}, Row {r}, Col {c}) at slot [{slot}] assigned to "
                            f"{len(assigns)} students: {', '.join(names)}."
                        ),
                        details={"room_id": room, "row": r, "col": c, "slot": slot, "students": names},
                        remedy="Each student must have an independent, unique seat.",
                    )
                )

        passed = len(violations) == 0
        summary = (
            "Every student has a distinct, collision-free physical seat."
            if passed
            else f"{len(violations)} duplicate seat collision(s) detected!"
        )
        return ValidationCheckResult(
            check_id="CHK_SEAT_UNIQUENESS",
            check_name="Seat Uniqueness & Single Occupancy",
            category="HARD",
            passed=passed,
            summary=summary,
            violations=violations,
        )

    @classmethod
    def check_seat_bounds(
        cls, rooms: List[Room], seating: List[StudentSeatAssignment]
    ) -> ValidationCheckResult:
        """Verifies that every assigned seat coordinate (row, col) is within room grid bounds."""
        room_grid_map = {r.room_id: (r.rows, r.cols) for r in rooms}
        violations = []

        for a in seating:
            if a.room_id not in room_grid_map:
                violations.append(
                    ConflictReport(
                        conflict_type="UNKNOWN_ROOM_ASSIGNMENT",
                        description=f"Seat assigned in unregistered room '{a.room_id}' for student {a.student_id}.",
                        details={"room_id": a.room_id, "student_id": a.student_id},
                        remedy="Assign seats only to valid registered examination rooms.",
                    )
                )
            else:
                max_r, max_c = room_grid_map[a.room_id]
                if a.row < 1 or a.row > max_r or a.col < 1 or a.col > max_c:
                    violations.append(
                        ConflictReport(
                            conflict_type="OUT_OF_BOUNDS_SEAT",
                            description=(
                                f"Seat ({a.row}, {a.col}) in Room '{a.room_id}' exceeds physical grid "
                                f"dimensions ({max_r} rows × {max_c} cols)."
                            ),
                            details={"room_id": a.room_id, "row": a.row, "col": a.col, "max_rows": max_r, "max_cols": max_c},
                            remedy="Ensure row and column coordinates are within room bounds.",
                        )
                    )

        passed = len(violations) == 0
        summary = (
            "All seat coordinates fall strictly within room row and column boundaries."
            if passed
            else f"{len(violations)} out-of-bounds seat assignment(s) detected!"
        )
        return ValidationCheckResult(
            check_id="CHK_SEAT_BOUNDS",
            check_name="Physical Grid Bounds Compliance",
            category="HARD",
            passed=passed,
            summary=summary,
            violations=violations,
        )

    @classmethod
    def check_student_exam_overlaps(
        cls,
        students: List[Student],
        exams: List[Exam],
        seating: List[StudentSeatAssignment],
    ) -> ValidationCheckResult:
        """Verifies no student is scheduled to take multiple exams in the exact same time slot."""
        violations = []
        exam_slot_map = {e.exam_code: e.slot_key for e in exams}

        # Check in the actual seating assignments
        # Map: (student_id, slot_key) -> List[StudentSeatAssignment]
        student_slot_assignments: Dict[Tuple[str, str], List[StudentSeatAssignment]] = defaultdict(list)
        for a in seating:
            student_slot_assignments[(a.student_id, a.slot_key)].append(a)

        for (st_id, slot), assigns in student_slot_assignments.items():
            if len(assigns) > 1:
                exams_list = [f"{a.exam_code} in {a.room_id}" for a in assigns]
                st_name = assigns[0].student_name
                violations.append(
                    ConflictReport(
                        conflict_type="STUDENT_SLOT_COLLISION",
                        description=(
                            f"Student {st_name} ({st_id}) has multiple seat assignments in slot [{slot}]: "
                            f"{', '.join(exams_list)}."
                        ),
                        details={"student_id": st_id, "slot": slot, "assignments": exams_list},
                        remedy="Exams must be scheduled in non-overlapping time slots.",
                    )
                )

        # Also check course registration clash
        for st in students:
            slot_exams: Dict[str, List[str]] = defaultdict(list)
            for c in st.courses:
                if c in exam_slot_map:
                    slot = exam_slot_map[c]
                    slot_exams[slot].append(c)
            for slot, c_list in slot_exams.items():
                if len(c_list) > 1:
                    # Only add if not already captured in actual seating assignments
                    if (st.student_id, slot) not in student_slot_assignments or len(student_slot_assignments[(st.student_id, slot)]) <= 1:
                        violations.append(
                            ConflictReport(
                                conflict_type="STUDENT_COURSE_ENROLLMENT_OVERLAP",
                                description=(
                                    f"Student {st.name} ({st.student_id}) enrolled in multiple courses "
                                    f"scheduled at same slot [{slot}]: {', '.join(c_list)}."
                                ),
                                details={"student_id": st.student_id, "slot": slot, "courses": c_list},
                                remedy="Reschedule one of the conflicting exams to a separate time slot.",
                            )
                        )

        passed = len(violations) == 0
        summary = (
            "Zero student exam timetable clashes detected."
            if passed
            else f"{len(violations)} student timetable collision(s) detected!"
        )
        return ValidationCheckResult(
            check_id="CHK_STUDENT_OVERLAP",
            check_name="Student Exam Overlap Prevention",
            category="HARD",
            passed=passed,
            summary=summary,
            violations=violations,
        )

    @classmethod
    def check_invigilator_double_booking(
        cls, invigilations: List[InvigilationAssignment]
    ) -> ValidationCheckResult:
        """Verifies that no faculty member is booked to supervise more than one room at the same time slot."""
        fac_slot_rooms: Dict[Tuple[str, str], List[InvigilationAssignment]] = defaultdict(list)
        for inv in invigilations:
            fac_slot_rooms[(inv.faculty_id, inv.slot_key)].append(inv)

        violations = []
        for (fac_id, slot), assigns in fac_slot_rooms.items():
            if len(assigns) > 1:
                rooms = [a.room_id for a in assigns]
                fac_name = assigns[0].faculty_name
                violations.append(
                    ConflictReport(
                        conflict_type="INVIGILATOR_DOUBLE_BOOKING",
                        description=(
                            f"Faculty member {fac_name} ({fac_id}) is double-booked for {len(assigns)} rooms "
                            f"({', '.join(rooms)}) simultaneously in slot [{slot}]."
                        ),
                        details={"faculty_id": fac_id, "faculty_name": fac_name, "slot": slot, "rooms": rooms},
                        remedy="An invigilator can only supervise one examination room per time slot.",
                    )
                )

        passed = len(violations) == 0
        summary = (
            "Zero invigilator double-booking collisions detected."
            if passed
            else f"{len(violations)} invigilator double-booking conflict(s) detected!"
        )
        return ValidationCheckResult(
            check_id="CHK_INVIGILATOR_COLLISION",
            check_name="Invigilator Double-Booking Prevention",
            category="HARD",
            passed=passed,
            summary=summary,
            violations=violations,
        )

    @classmethod
    def check_faculty_availability(
        cls, faculty: List[Faculty], invigilations: List[InvigilationAssignment]
    ) -> ValidationCheckResult:
        """Verifies no faculty is scheduled to invigilate during their unavailable slots."""
        fac_map = {f.faculty_id: f for f in faculty}
        violations = []

        for inv in invigilations:
            fac = fac_map.get(inv.faculty_id)
            if fac:
                unavail_normalized = {u.strip().lower() for u in fac.unavailable_slots if u.strip()}
                if inv.slot_key.strip().lower() in unavail_normalized:
                    violations.append(
                        ConflictReport(
                            conflict_type="FACULTY_UNAVAILABLE_SLOT",
                            description=(
                                f"Faculty {fac.name} ({fac.faculty_id}) is assigned to Room '{inv.room_id}' "
                                f"at slot [{inv.slot_key}], but is explicitly registered as unavailable."
                            ),
                            details={"faculty_id": fac.faculty_id, "slot": inv.slot_key, "room_id": inv.room_id},
                            remedy="Reassign duty to an available faculty member or modify availability.",
                        )
                    )

        passed = len(violations) == 0
        summary = (
            "All faculty assignments strictly respect faculty availability preferences."
            if passed
            else f"{len(violations)} faculty availability violation(s) detected!"
        )
        return ValidationCheckResult(
            check_id="CHK_FACULTY_AVAILABILITY",
            check_name="Faculty Availability Enforcement",
            category="HARD",
            passed=passed,
            summary=summary,
            violations=violations,
        )

    @classmethod
    def check_faculty_workload_limits(
        cls, faculty: List[Faculty], invigilations: List[InvigilationAssignment]
    ) -> ValidationCheckResult:
        """Verifies that no faculty member's assigned duties exceed their configured max_duties."""
        fac_map = {f.faculty_id: f for f in faculty}
        duty_counts: Dict[str, int] = defaultdict(int)

        for inv in invigilations:
            duty_counts[inv.faculty_id] += 1

        violations = []
        for fac_id, count in duty_counts.items():
            fac = fac_map.get(fac_id)
            if fac and count > fac.max_duties:
                violations.append(
                    ConflictReport(
                        conflict_type="MAX_DUTIES_EXCEEDED",
                        description=(
                            f"Faculty {fac.name} ({fac.faculty_id}) assigned {count} duties, "
                            f"which exceeds the maximum quota of {fac.max_duties} duties."
                        ),
                        details={"faculty_id": fac_id, "assigned": count, "max_duties": fac.max_duties},
                        remedy="Increase max duties quota or distribute duties to other faculty members.",
                    )
                )

        passed = len(violations) == 0
        summary = (
            "All faculty assignments strictly within institutional workload quotas."
            if passed
            else f"{len(violations)} workload limit violation(s) detected!"
        )
        return ValidationCheckResult(
            check_id="CHK_WORKLOAD_LIMITS",
            check_name="Faculty Workload Quota Compliance",
            category="HARD",
            passed=passed,
            summary=summary,
            violations=violations,
        )

    @classmethod
    def check_schedule_coverage(
        cls,
        students: List[Student],
        exams: List[Exam],
        seating: List[StudentSeatAssignment],
        invigilations: List[InvigilationAssignment],
    ) -> ValidationCheckResult:
        """Verifies that every enrolled examinee is assigned a seat and every active room has a supervisor."""
        violations = []
        exam_codes = {e.exam_code for e in exams}

        # 1. Check all student course registrations have been seated
        assigned_student_exams = {(a.student_id, a.exam_code) for a in seating}
        missing_count = 0
        for st in students:
            for c in st.courses:
                if c in exam_codes:
                    if (st.student_id, c) not in assigned_student_exams:
                        missing_count += 1
                        if missing_count <= 5:
                            violations.append(
                                ConflictReport(
                                    conflict_type="UNSEATED_EXAMINEE",
                                    description=f"Student {st.name} ({st.student_id}) has no seat assigned for exam {c}.",
                                    details={"student_id": st.student_id, "exam_code": c},
                                    remedy="Generate schedule to assign physical seats for all registered examinees.",
                                )
                            )
        if missing_count > 5:
            violations.append(
                ConflictReport(
                    conflict_type="UNSEATED_EXAMINEES_OVERFLOW",
                    description=f"+ {missing_count - 5} more examinees without assigned seats.",
                    details={"total_missing": missing_count},
                    remedy="Expand room capacities or schedule additional exam slots.",
                )
            )

        # 2. Check all active halls with examinees have an assigned invigilator
        supervised_rooms = {(i.slot_key, i.room_id) for i in invigilations}
        active_room_slots = {(a.slot_key, a.room_id) for a in seating}
        for slot, room in active_room_slots:
            if (slot, room) not in supervised_rooms:
                violations.append(
                    ConflictReport(
                        conflict_type="UNSUPERVISED_EXAM_ROOM",
                        description=f"Active examination hall '{room}' at slot [{slot}] has examinees but no assigned invigilator.",
                        details={"slot": slot, "room_id": room},
                        remedy="Assign an available faculty member to supervise this examination hall.",
                    )
                )

        passed = len(violations) == 0
        summary = (
            "100% of enrolled examinees are seated and all active exam halls are supervised."
            if passed
            else f"{missing_count} unseated examinee(s) or unsupervised hall(s) detected!"
        )
        return ValidationCheckResult(
            check_id="CHK_SCHEDULE_COMPLETENESS",
            check_name="Examinee Seating & Supervision Coverage",
            category="HARD",
            passed=passed,
            summary=summary,
            violations=violations,
        )


    # -------------------------------------------------------------------------
    # Fairness Calculation from Actual Duties
    # -------------------------------------------------------------------------
    @classmethod
    def calculate_actual_duty_fairness(
        cls, faculty: List[Faculty], invigilations: List[InvigilationAssignment]
    ) -> Dict[str, Any]:
        """Calculates workload fairness directly from the actual duty distribution.

        Includes:
        - Duty count per faculty
        - Mean, Standard Deviation, Min, Max
        - Jain's Fairness Index: (sum(x_i))^2 / (n * sum(x_i^2))
        - Capacity-adjusted workload utilization ratio
        """
        duty_counts: Dict[str, int] = {f.faculty_id: 0 for f in faculty}
        for inv in invigilations:
            if inv.faculty_id in duty_counts:
                duty_counts[inv.faculty_id] += 1

        duties = list(duty_counts.values())
        total_faculty = len(faculty)

        if total_faculty == 0 or sum(duties) == 0:
            return {
                "fairness_score": 100.0,
                "jains_fairness_index": 1.0,
                "mean_duties": 0.0,
                "std_dev": 0.0,
                "min_duties": 0,
                "max_duties": 0,
                "distribution": duty_counts,
                "summary": "No duties to distribute.",
            }

        n = len(duties)
        sum_x = sum(duties)
        sum_sq_x = sum(d ** 2 for d in duties)
        mean_d = sum_x / n
        var = sum((d - mean_d) ** 2 for d in duties) / n
        std_d = math.sqrt(var)

        # Jain's Fairness Index: Range is [1/n, 1.0], where 1.0 is totally equal distribution
        jfi = (sum_x ** 2) / (n * sum_sq_x) if sum_sq_x > 0 else 1.0
        jfi_pct = round(jfi * 100.0, 1)

        # Score penalized by standard deviation (std_dev = 0 -> 100%)
        sd_score = max(0.0, min(100.0, 100.0 - (std_d * 25.0)))
        fairness_score = round((jfi_pct * 0.5) + (sd_score * 0.5), 1)

        return {
            "fairness_score": fairness_score,
            "jains_fairness_index": round(jfi, 3),
            "jains_pct": jfi_pct,
            "mean_duties": round(mean_d, 2),
            "std_dev": round(std_d, 2),
            "min_duties": min(duties),
            "max_duties": max(duties),
            "distribution": duty_counts,
            "summary": (
                f"Fairness: {fairness_score}% (Jain's Index: {jfi:.2f}, "
                f"Mean: {mean_d:.1f} duties, StdDev: {std_d:.2f})"
            ),
        }
