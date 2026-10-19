"""Automated tests for Independent Schedule Validator and Deliberately Invalid Schedules."""
import pytest
from data.storage import DataStorage
from csp.models import (
    Student,
    Exam,
    Room,
    Faculty,
    StudentSeatAssignment,
    InvigilationAssignment,
)
from csp.solver import ExamCSPSolver
from csp.validator import IndependentScheduleValidator


@pytest.fixture
def base_test_data(tmp_path):
    """Provides a fresh data environment with baseline valid entities."""
    test_dir = str(tmp_path / "validator_test_csv")
    ds = DataStorage(data_dir=test_dir)
    return {
        "students": ds.load_students(),
        "exams": ds.load_exams(),
        "rooms": ds.load_rooms(),
        "faculty": ds.load_faculty(),
    }


# =============================================================================
# 1. Valid Schedule Verification
# =============================================================================
def test_valid_schedule_passes_all_checks(base_test_data):
    """Verify that a validly solved schedule passes 100% of independent validator checks."""
    students = base_test_data["students"]
    exams = base_test_data["exams"]
    rooms = base_test_data["rooms"]
    faculty = base_test_data["faculty"]

    solver = ExamCSPSolver(students, exams, rooms, faculty)
    result = solver.solve()

    assert result.success is True, f"Solver failed: {[c.description for c in result.conflicts]}"
    assert result.validation_summary is not None
    assert result.validation_summary.overall_passed is True
    assert result.validation_summary.failed_hard_checks == 0
    assert result.validation_summary.passed_hard_checks == result.validation_summary.total_hard_checks
    assert len(result.validation_summary.all_violations) == 0


# =============================================================================
# 2. Deliberate Invalidation Tests
# =============================================================================
def test_deliberate_room_capacity_violation(base_test_data):
    """Deliberately assign more students than room capacity and verify validator catches it."""
    rooms = [Room(room_id="LH-TEST", building="Block A", rows=2, cols=2, capacity=3)]  # Max 3
    slot = "2026-11-10 | Morning"

    # Assign 4 students to LH-TEST
    invalid_seating = [
        StudentSeatAssignment(f"S{i}", f"Student {i}", "CS101", "AI", slot, "LH-TEST", (i // 2) + 1, (i % 2) + 1, f"LH-TEST-R{(i//2)+1}C{(i%2)+1}")
        for i in range(4)
    ]

    summary = IndependentScheduleValidator.validate_schedule(
        students=[],
        exams=[],
        rooms=rooms,
        faculty=[],
        seating_assignments=invalid_seating,
        invigilation_assignments=[],
    )

    assert summary.overall_passed is False
    assert summary.failed_hard_checks >= 1
    assert any(v.conflict_type == "ROOM_CAPACITY_EXCEEDED" for v in summary.all_violations)


def test_deliberate_duplicate_seat_violation():
    """Deliberately assign two students to the exact same seat coordinate and verify detection."""
    slot = "2026-11-10 | Morning"
    rooms = [Room("LH-101", "Main Block", 3, 3, 9)]

    # Two students assigned to same Row 1, Col 1
    colliding_seating = [
        StudentSeatAssignment("S1", "Alice", "CS101", "AI", slot, "LH-101", 1, 1, "LH-101-R1C1"),
        StudentSeatAssignment("S2", "Bob", "CS101", "AI", slot, "LH-101", 1, 1, "LH-101-R1C1"),
    ]

    summary = IndependentScheduleValidator.validate_schedule(
        students=[],
        exams=[],
        rooms=rooms,
        faculty=[],
        seating_assignments=colliding_seating,
        invigilation_assignments=[],
    )

    assert summary.overall_passed is False
    assert any(v.conflict_type == "DUPLICATE_SEAT_ASSIGNMENT" for v in summary.all_violations)


def test_deliberate_out_of_bounds_seat_violation():
    """Deliberately assign a seat beyond the room's row/column boundaries."""
    slot = "2026-11-10 | Morning"
    rooms = [Room("LH-101", "Main Block", rows=3, cols=3, capacity=9)]

    # Seat row 5 in a 3-row room
    out_of_bounds_seating = [
        StudentSeatAssignment("S1", "Alice", "CS101", "AI", slot, "LH-101", row=5, col=1, seat_label="LH-101-R5C1"),
    ]

    summary = IndependentScheduleValidator.validate_schedule(
        students=[],
        exams=[],
        rooms=rooms,
        faculty=[],
        seating_assignments=out_of_bounds_seating,
        invigilation_assignments=[],
    )

    assert summary.overall_passed is False
    assert any(v.conflict_type == "OUT_OF_BOUNDS_SEAT" for v in summary.all_violations)


def test_deliberate_student_exam_overlap_violation():
    """Deliberately schedule a student for 2 distinct exams in the same slot."""
    slot = "2026-11-10 | Morning"
    rooms = [Room("LH-101", "Main Block", 5, 5, 25), Room("LH-102", "Main Block", 5, 5, 25)]

    # Student S1 assigned to both CS101 in LH-101 and EC201 in LH-102 at the same slot
    overlapping_seating = [
        StudentSeatAssignment("S1", "Alice", "CS101", "AI", slot, "LH-101", 1, 1, "LH-101-R1C1"),
        StudentSeatAssignment("S1", "Alice", "EC201", "DSP", slot, "LH-102", 1, 1, "LH-102-R1C1"),
    ]

    summary = IndependentScheduleValidator.validate_schedule(
        students=[Student("S1", "Alice", "CS", ["CS101", "EC201"])],
        exams=[
            Exam("CS101", "AI", "CS", "2026-11-10", "Morning"),
            Exam("EC201", "DSP", "EC", "2026-11-10", "Morning"),
        ],
        rooms=rooms,
        faculty=[],
        seating_assignments=overlapping_seating,
        invigilation_assignments=[],
    )

    assert summary.overall_passed is False
    assert any("COLLISION" in v.conflict_type or "OVERLAP" in v.conflict_type for v in summary.all_violations)


def test_deliberate_invigilator_double_booking_violation():
    """Deliberately assign one faculty member to supervise two rooms simultaneously."""
    slot = "2026-11-10 | Morning"
    faculty = [Faculty("FAC-01", "Dr. Meera", "CS", max_duties=5)]

    # FAC-01 assigned to both LH-101 and LH-102 in slot
    double_booked_invig = [
        InvigilationAssignment(slot, "LH-101", "FAC-01", "Dr. Meera", "CS"),
        InvigilationAssignment(slot, "LH-102", "FAC-01", "Dr. Meera", "CS"),
    ]

    summary = IndependentScheduleValidator.validate_schedule(
        students=[],
        exams=[],
        rooms=[Room("LH-101", "Block", 5, 5, 25), Room("LH-102", "Block", 5, 5, 25)],
        faculty=faculty,
        seating_assignments=[],
        invigilation_assignments=double_booked_invig,
    )

    assert summary.overall_passed is False
    assert any(v.conflict_type == "INVIGILATOR_DOUBLE_BOOKING" for v in summary.all_violations)


def test_deliberate_faculty_unavailability_violation():
    """Deliberately assign faculty during a slot marked as unavailable."""
    unavailable_slot = "2026-11-10 | Morning (09:30 - 12:30)"
    faculty = [
        Faculty("FAC-01", "Dr. Meera", "CS", max_duties=3, unavailable_slots=[unavailable_slot]),
    ]

    violating_invig = [
        InvigilationAssignment(unavailable_slot, "LH-101", "FAC-01", "Dr. Meera", "CS"),
    ]

    summary = IndependentScheduleValidator.validate_schedule(
        students=[],
        exams=[],
        rooms=[Room("LH-101", "Block", 5, 5, 25)],
        faculty=faculty,
        seating_assignments=[],
        invigilation_assignments=violating_invig,
    )

    assert summary.overall_passed is False
    assert any(v.conflict_type == "FACULTY_UNAVAILABLE_SLOT" for v in summary.all_violations)


def test_deliberate_faculty_workload_limit_violation():
    """Deliberately assign more duties than max_duties quota to a faculty member."""
    faculty = [Faculty("FAC-01", "Dr. Meera", "CS", max_duties=2)]

    # Assign 3 duties to FAC-01
    excess_invig = [
        InvigilationAssignment("Slot 1", "LH-101", "FAC-01", "Dr. Meera", "CS"),
        InvigilationAssignment("Slot 2", "LH-101", "FAC-01", "Dr. Meera", "CS"),
        InvigilationAssignment("Slot 3", "LH-101", "FAC-01", "Dr. Meera", "CS"),
    ]

    summary = IndependentScheduleValidator.validate_schedule(
        students=[],
        exams=[],
        rooms=[Room("LH-101", "Block", 5, 5, 25)],
        faculty=faculty,
        seating_assignments=[],
        invigilation_assignments=excess_invig,
    )

    assert summary.overall_passed is False
    assert any(v.conflict_type == "MAX_DUTIES_EXCEEDED" for v in summary.all_violations)


# =============================================================================
# 3. Actual Duty Distribution Fairness Score Tests
# =============================================================================
def test_fairness_score_perfect_balance():
    """Verify that perfectly balanced duty distribution yields 100% fairness and Jain's index 1.0."""
    faculty = [
        Faculty("FAC-01", "Prof 1", "CS", 3),
        Faculty("FAC-02", "Prof 2", "CS", 3),
        Faculty("FAC-03", "Prof 3", "CS", 3),
        Faculty("FAC-04", "Prof 4", "CS", 3),
    ]
    # Each faculty receives exactly 2 duties
    invigilations = [
        InvigilationAssignment(f"Slot {i}", "LH-101", f"FAC-0{j}", f"Prof {j}", "CS")
        for j in range(1, 5)
        for i in range(1, 3)
    ]

    fairness = IndependentScheduleValidator.calculate_actual_duty_fairness(faculty, invigilations)

    assert fairness["jains_fairness_index"] == 1.0
    assert fairness["std_dev"] == 0.0
    assert fairness["mean_duties"] == 2.0
    assert fairness["fairness_score"] == 100.0


def test_fairness_score_severe_imbalance():
    """Verify that severe duty imbalance substantially drops Jain's index and fairness score."""
    faculty = [
        Faculty("FAC-01", "Prof 1", "CS", 10),
        Faculty("FAC-02", "Prof 2", "CS", 10),
        Faculty("FAC-03", "Prof 3", "CS", 10),
        Faculty("FAC-04", "Prof 4", "CS", 10),
    ]
    # Only FAC-01 is assigned all 8 duties; others receive 0 duties
    invigilations = [
        InvigilationAssignment(f"Slot {i}", "LH-101", "FAC-01", "Prof 1", "CS")
        for i in range(1, 9)
    ]

    fairness = IndependentScheduleValidator.calculate_actual_duty_fairness(faculty, invigilations)

    # In a 4-person system where 1 person has all workload, Jain's index = 1/4 = 0.25
    assert fairness["jains_fairness_index"] == 0.25
    assert fairness["std_dev"] > 3.0
    assert fairness["fairness_score"] < 40.0
