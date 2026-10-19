"""Individual unit tests for each Hard Constraint and Soft Preference metric."""
import pytest
from csp.models import (
    Student,
    Exam,
    Room,
    Faculty,
    StudentSeatAssignment,
    InvigilationAssignment,
)
from csp.constraints import ConstraintValidator, SoftPreferenceEvaluator
from csp.explainer import ScheduleExplainer


def test_seat_uniqueness_validator():
    """Seats cannot be assigned to more than one student."""
    # Two students assigned to same seat in same slot
    assignments = [
        StudentSeatAssignment("S1", "Alice", "CS101", "AI", "2026-11-10 | Morning", "LH-101", 1, 1, "LH-101-R1C1"),
        StudentSeatAssignment("S2", "Bob", "CS101", "AI", "2026-11-10 | Morning", "LH-101", 1, 1, "LH-101-R1C1"),
    ]
    conflicts = ConstraintValidator.validate_seat_uniqueness(assignments)
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == "SEAT_COLLISION"


def test_room_capacity_validator():
    """Room capacity cannot be exceeded."""
    rooms = [Room("LH-101", "Main Block", rows=2, cols=2, capacity=2)]
    assignments = [
        StudentSeatAssignment("S1", "Alice", "CS101", "AI", "2026-11-10 | Morning", "LH-101", 1, 1, "LH-101-R1C1"),
        StudentSeatAssignment("S2", "Bob", "CS101", "AI", "2026-11-10 | Morning", "LH-101", 1, 2, "LH-101-R1C2"),
        StudentSeatAssignment("S3", "Charlie", "CS101", "AI", "2026-11-10 | Morning", "LH-101", 2, 1, "LH-101-R2C1"),
    ]
    conflicts = ConstraintValidator.validate_room_capacities(assignments, rooms)
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == "ROOM_CAPACITY_EXCEEDED"


def test_invigilator_slot_conflicts_validator():
    """An invigilator cannot supervise two rooms at the same time."""
    invigilations = [
        InvigilationAssignment("2026-11-10 | Morning", "LH-101", "FAC-01", "Dr. Meera", "CS"),
        InvigilationAssignment("2026-11-10 | Morning", "LH-102", "FAC-01", "Dr. Meera", "CS"),
    ]
    conflicts = ConstraintValidator.validate_invigilator_slot_conflicts(invigilations)
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == "FACULTY_DOUBLE_BOOKING"


def test_faculty_availability_validator():
    """Unavailable faculty cannot be assigned."""
    faculty = [
        Faculty("FAC-01", "Dr. Meera", "CS", max_duties=3, unavailable_slots=["2026-11-10 | Morning (09:30 - 12:30)"])
    ]
    invigilations = [
        InvigilationAssignment("2026-11-10 | Morning (09:30 - 12:30)", "LH-101", "FAC-01", "Dr. Meera", "CS")
    ]
    conflicts = ConstraintValidator.validate_faculty_availability(invigilations, faculty)
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == "FACULTY_UNAVAILABLE"


def test_faculty_workload_limits_validator():
    """Faculty workload limits must be respected."""
    faculty = [
        Faculty("FAC-01", "Dr. Meera", "CS", max_duties=1, unavailable_slots=[])
    ]
    invigilations = [
        InvigilationAssignment("Slot 1", "LH-101", "FAC-01", "Dr. Meera", "CS"),
        InvigilationAssignment("Slot 2", "LH-101", "FAC-01", "Dr. Meera", "CS"),
    ]
    conflicts = ConstraintValidator.validate_faculty_workload_limits(invigilations, faculty)
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == "WORKLOAD_LIMIT_EXCEEDED"


def test_seating_separation_soft_preference():
    """Checks separation metric calculations."""
    # Two adjacent seats with same subject vs different subjects
    same_subject_assignments = [
        StudentSeatAssignment("S1", "A", "CS101", "AI", "Slot 1", "R1", 1, 1, "R1-R1C1"),
        StudentSeatAssignment("S2", "B", "CS101", "AI", "Slot 1", "R1", 1, 2, "R1-R1C2"),
    ]
    diff_subject_assignments = [
        StudentSeatAssignment("S1", "A", "CS101", "AI", "Slot 1", "R1", 1, 1, "R1-R1C1"),
        StudentSeatAssignment("S2", "B", "EC101", "DSP", "Slot 1", "R1", 1, 2, "R1-R1C2"),
    ]
    res_same = SoftPreferenceEvaluator.evaluate_seating_separation(same_subject_assignments)
    res_diff = SoftPreferenceEvaluator.evaluate_seating_separation(diff_subject_assignments)

    assert res_same["score"] == 0.0
    assert res_diff["score"] == 100.0


def test_explainer_formatting():
    """Verify explainer generates clean readable markdown with remediation tips."""
    conflicts = [
        ScheduleExplainer.diagnose_preconditions(
            students=[Student("S1", "Alice", "CS", ["E1", "E2"])],
            exams=[
                Exam("E1", "Sub 1", "CS", "2026-11-10", "Slot A"),
                Exam("E2", "Sub 2", "CS", "2026-11-10", "Slot A"),
            ],
            rooms=[Room("R1", "Block", 5, 5, 25)],
            faculty=[Faculty("F1", "Prof", "CS", 3)],
        )
    ]
    md = ScheduleExplainer.format_explanation_markdown(conflicts[0])
    assert "Conflict Diagnosis" in md
    assert "Recommended Fix" in md
