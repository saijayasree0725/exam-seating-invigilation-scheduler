"""Unit and integration tests for CSP Backtracking Solver and Hard Constraints."""
import pytest
from data.storage import DataStorage
from csp.solver import ExamCSPSolver
from csp.models import Student, Exam, Room, Faculty
from csp.constraints import ConstraintValidator, SoftPreferenceEvaluator
from csp.explainer import ScheduleExplainer


@pytest.fixture
def storage(tmp_path):
    """Provides a fresh DataStorage instance in a temporary test directory."""
    test_dir = str(tmp_path / "test_csv")
    ds = DataStorage(data_dir=test_dir)
    return ds


def test_demo_dataset_schedule_generation(storage):
    """Verify solver produces a 100% valid schedule on standard college demo data."""
    students = storage.load_students()
    exams = storage.load_exams()
    rooms = storage.load_rooms()
    faculty = storage.load_faculty()

    assert len(students) > 0
    assert len(exams) > 0
    assert len(rooms) > 0
    assert len(faculty) > 0

    solver = ExamCSPSolver(
        students=students,
        exams=exams,
        rooms=rooms,
        faculty=faculty,
        enable_seating_separation=True,
        enable_workload_balance=True,
    )
    result = solver.solve()

    assert result.success is True, f"Solver failed: {[c.description for c in result.conflicts]}"
    assert result.validation_passed is True
    assert len(result.seating_assignments) > 0
    assert len(result.invigilation_assignments) > 0
    assert len(result.conflicts) == 0

    # Verify no student is double seated in same slot
    seen_seats = set()
    for a in result.seating_assignments:
        key = (a.slot_key, a.room_id, a.row, a.col)
        assert key not in seen_seats, f"Duplicate seat assignment: {key}"
        seen_seats.add(key)


def test_hard_constraint_student_overlap():
    """Verify solver detects and rejects overlapping exams for the same student."""
    students = [
        Student("S1", "Test Student", "CS", ["CS101", "CS102"])
    ]
    # Both exams in the exact same slot
    exams = [
        Exam("CS101", "Course 1", "CS", "2026-11-10", "Morning (09:30 - 12:30)"),
        Exam("CS102", "Course 2", "CS", "2026-11-10", "Morning (09:30 - 12:30)"),
    ]
    rooms = [Room("R1", "Block", 3, 3, 9)]
    faculty = [Faculty("F1", "Prof A", "CS", max_duties=2)]

    solver = ExamCSPSolver(students, exams, rooms, faculty)
    result = solver.solve()

    assert result.success is False
    assert result.validation_passed is False
    assert len(result.conflicts) > 0
    assert any("STUDENT_OVERLAP" in c.conflict_type or "OVERLAP" in c.conflict_type for c in result.conflicts)


def test_hard_constraint_room_capacity_deficit():
    """Verify solver diagnoses shortage when students exceed available room capacity."""
    # 5 students, but room has capacity only 2
    students = [
        Student(f"S{i}", f"Student {i}", "CS", ["CS101"]) for i in range(5)
    ]
    exams = [Exam("CS101", "Course 1", "CS", "2026-11-10", "Morning (09:30 - 12:30)")]
    rooms = [Room("R1", "Block", 1, 2, capacity=2)]
    faculty = [Faculty("F1", "Prof A", "CS", max_duties=2)]

    solver = ExamCSPSolver(students, exams, rooms, faculty)
    result = solver.solve()

    assert result.success is False
    assert any("CAPACITY" in c.conflict_type for c in result.conflicts)


def test_hard_constraint_faculty_double_booking_and_availability():
    """Verify invigilator cannot supervise two rooms simultaneously or during unavailable slot."""
    faculty = [
        Faculty("F1", "Prof A", "CS", max_duties=5, unavailable_slots=["2026-11-10 | Morning (09:30 - 12:30)"]),
    ]
    students = [Student("S1", "Alice", "CS", ["CS101"])]
    exams = [Exam("CS101", "Course 1", "CS", "2026-11-10", "Morning (09:30 - 12:30)")]
    rooms = [Room("R1", "Block", 5, 5, 25)]

    solver = ExamCSPSolver(students, exams, rooms, faculty)
    result = solver.solve()

    assert result.success is False
    assert any("FACULTY" in c.conflict_type for c in result.conflicts)


def test_hard_constraint_faculty_workload_limit():
    """Verify solver prevents faculty from exceeding max_duties."""
    # 2 slots, each requires 1 room (2 duties total), but F1 has max_duties=1
    faculty = [
        Faculty("F1", "Prof Single", "CS", max_duties=1, unavailable_slots=[]),
    ]
    students = [
        Student("S1", "Alice", "CS", ["CS101", "CS102"]),
    ]
    exams = [
        Exam("CS101", "Course 1", "CS", "2026-11-10", "Morning (09:30 - 12:30)"),
        Exam("CS102", "Course 2", "CS", "2026-11-11", "Morning (09:30 - 12:30)"),
    ]
    rooms = [Room("R1", "Block", 4, 4, 16)]

    solver = ExamCSPSolver(students, exams, rooms, faculty)
    result = solver.solve()

    assert result.success is False
    assert any("WORKLOAD" in c.conflict_type or "FACULTY" in c.conflict_type for c in result.conflicts)


def test_soft_preference_scoring(storage):
    """Verify soft preference metrics calculate valid ranges (0-100%)."""
    students = storage.load_students()
    exams = storage.load_exams()
    rooms = storage.load_rooms()
    faculty = storage.load_faculty()

    solver = ExamCSPSolver(students, exams, rooms, faculty)
    result = solver.solve()

    assert result.success is True
    soft_score = result.metrics.get("soft_score", 0)
    assert 0 <= soft_score <= 100
    assert "separation_metrics" in result.metrics
    assert "workload_metrics" in result.metrics
    assert "room_efficiency_metrics" in result.metrics


def test_schedule_result_validation_summary_always_present(storage):
    """Verify solver always attaches a structured validation_summary to ScheduleResult."""
    students = storage.load_students()
    exams = storage.load_exams()
    rooms = storage.load_rooms()
    faculty = storage.load_faculty()

    solver = ExamCSPSolver(students, exams, rooms, faculty)
    result = solver.solve()

    assert hasattr(result, "validation_summary")
    assert result.validation_summary is not None
    assert result.validation_summary.overall_passed is True
    assert len(result.validation_summary.check_results) >= 7
    assert result.validation_summary.failed_hard_checks == 0


def test_schedule_result_attribute_safety():
    """Verify ScheduleResult never raises AttributeError for validation_summary even if initialized without it."""
    from csp.models import ScheduleResult
    res = ScheduleResult(success=True)
    # Accessing .validation_summary must not raise AttributeError
    assert res.validation_summary is None


def test_infeasible_solver_returns_structured_validation_summary():
    """Verify infeasible problem inputs return a ScheduleResult with structured validation_summary and FAIL status."""
    # Student has overlapping exams in the same slot
    students = [Student("S1", "Alice", "CS", ["CS101", "CS102"])]
    exams = [
        Exam("CS101", "Sub 1", "CS", "2026-11-10", "Morning (09:30 - 12:30)"),
        Exam("CS102", "Sub 2", "CS", "2026-11-10", "Morning (09:30 - 12:30)"),
    ]
    rooms = [Room("R1", "Block", 5, 5, 25)]
    faculty = [Faculty("F1", "Prof", "CS", 3)]

    solver = ExamCSPSolver(students, exams, rooms, faculty)
    result = solver.solve()

    assert result.success is False
    assert result.validation_summary is not None
    assert result.validation_summary.overall_passed is False
    assert result.validation_summary.failed_hard_checks >= 1
    assert len(result.validation_summary.all_violations) >= 1

