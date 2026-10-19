"""End-to-end regression tests exercising dashboard rendering with actual ScheduleResult objects."""
import os
import pytest
from streamlit.testing.v1 import AppTest
from data.storage import DataStorage
from csp.solver import ExamCSPSolver
from csp.models import ScheduleResult, ConflictReport

APP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app.py"))


@pytest.fixture
def solved_schedule():
    """Generates an actual solved schedule result from demo data."""
    ds = DataStorage()
    students = ds.load_students()
    exams = ds.load_exams()
    rooms = ds.load_rooms()
    faculty = ds.load_faculty()
    solver = ExamCSPSolver(students, exams, rooms, faculty)
    return solver.solve()


def test_dashboard_renders_without_schedule():
    """Regression test: Dashboard loads cleanly when no schedule has been generated yet."""
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.run()
    assert len(at.exception) == 0, f"Exceptions occurred: {[e.value for e in at.exception]}"
    # Verify dashboard header text is present
    assert any("Exam Seating & Invigilation" in str(m.value) for m in at.markdown)


def test_dashboard_renders_with_actual_solver_result(solved_schedule):
    """Regression test: Dashboard renders cleanly with genuine solver-generated ScheduleResult."""
    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.session_state["schedule_result"] = solved_schedule
    at.session_state["nav_page"] = "Dashboard"
    at.run()

    assert len(at.exception) == 0, f"Exceptions occurred: {[e.value for e in at.exception]}"
    # Verify the independent validator audit card rendered with PASS
    markdown_texts = [str(m.value) for m in at.markdown]
    assert any("PASS" in text for text in markdown_texts), "PASS status badge missing from dashboard audit."
    assert any("Independent Verification Checklist" in text for text in markdown_texts)


def test_dashboard_renders_with_bare_legacy_scheduleresult_regression():
    """Regression test: Dashboard must NOT crash if ScheduleResult lacks validation_summary."""
    # Create a bare ScheduleResult without setting validation_summary
    bare_result = ScheduleResult(
        success=True,
        seating_assignments=[],
        invigilation_assignments=[],
        conflicts=[],
        metrics={},
        validation_passed=True,
    )
    # Explicitly remove validation_summary if present in instance dict to simulate unpickled legacy object
    if "validation_summary" in bare_result.__dict__:
        del bare_result.__dict__["validation_summary"]

    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.session_state["schedule_result"] = bare_result
    at.session_state["nav_page"] = "Dashboard"
    at.run()

    # Zero AttributeError allowed!
    assert len(at.exception) == 0, f"Dashboard crashed on legacy ScheduleResult: {[e.value for e in at.exception]}"


def test_dashboard_renders_with_infeasible_scheduleresult():
    """Regression test: Dashboard displays FAIL status and explanations when schedule is infeasible."""
    failed_result = ScheduleResult(
        success=False,
        seating_assignments=[],
        invigilation_assignments=[],
        conflicts=[
            ConflictReport(
                conflict_type="HARD_CONSTRAINT_CAPACITY_DEFICIT",
                description="Insufficient physical exam hall capacity for Morning slot.",
                remedy="Add an additional examination hall.",
            )
        ],
        metrics={},
        validation_passed=False,
    )

    at = AppTest.from_file(APP_PATH, default_timeout=15)
    at.session_state["schedule_result"] = failed_result
    at.session_state["nav_page"] = "Dashboard"
    at.run()

    assert len(at.exception) == 0, f"Dashboard crashed on failed ScheduleResult: {[e.value for e in at.exception]}"
    markdown_texts = [str(m.value) for m in at.markdown]
    assert any("FAIL" in text for text in markdown_texts)
    assert any("Insufficient physical exam hall capacity" in text for text in markdown_texts)


def test_all_pages_render_without_exceptions(solved_schedule):
    """End-to-end integration test: Every single page in the navigation menu renders without crashing."""
    pages = [
        "Dashboard",
        "Students",
        "Exams",
        "Rooms",
        "Faculty",
        "Generate Schedule",
        "Seating Plan",
        "Invigilation Duties",
        "Reports",
    ]

    for page_name in pages:
        at = AppTest.from_file(APP_PATH, default_timeout=15)
        at.session_state["schedule_result"] = solved_schedule
        at.session_state["nav_page"] = page_name
        at.run()
        assert len(at.exception) == 0, f"Page '{page_name}' crashed: {[e.value for e in at.exception]}"
