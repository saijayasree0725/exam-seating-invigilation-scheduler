"""Data models for Exam Seating and Invigilation Duty Scheduling."""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set, Tuple


@dataclass
class Student:
    student_id: str
    name: str
    department: str
    courses: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "student_id": self.student_id,
            "name": self.name,
            "department": self.department,
            "courses": ";".join(self.courses),
        }


@dataclass
class Exam:
    exam_code: str
    subject_name: str
    department: str
    date: str
    time_slot: str  # e.g., "Morning (09:30 - 12:30)" or "Afternoon (01:30 - 04:30)"
    duration_hours: float = 3.0

    @property
    def slot_key(self) -> str:
        """Normalized unique key for date and time slot."""
        return f"{self.date.strip()} | {self.time_slot.strip()}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "exam_code": self.exam_code,
            "subject_name": self.subject_name,
            "department": self.department,
            "date": self.date,
            "time_slot": self.time_slot,
            "duration_hours": self.duration_hours,
        }


@dataclass
class Room:
    room_id: str
    building: str
    rows: int
    cols: int
    capacity: int = 0
    is_active: bool = True

    def __post_init__(self):
        if self.capacity <= 0:
            self.capacity = self.rows * self.cols

    def to_dict(self) -> Dict[str, Any]:
        return {
            "room_id": self.room_id,
            "building": self.building,
            "rows": self.rows,
            "cols": self.cols,
            "capacity": self.capacity,
            "is_active": "Yes" if self.is_active else "No",
        }


@dataclass
class Faculty:
    faculty_id: str
    name: str
    department: str
    max_duties: int = 3
    unavailable_slots: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "faculty_id": self.faculty_id,
            "name": self.name,
            "department": self.department,
            "max_duties": self.max_duties,
            "unavailable_slots": ";".join(self.unavailable_slots),
        }


@dataclass
class StudentSeatAssignment:
    student_id: str
    student_name: str
    exam_code: str
    subject_name: str
    slot_key: str
    room_id: str
    row: int
    col: int
    seat_label: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "student_id": self.student_id,
            "student_name": self.student_name,
            "exam_code": self.exam_code,
            "subject_name": self.subject_name,
            "slot_key": self.slot_key,
            "room_id": self.room_id,
            "row": self.row,
            "col": self.col,
            "seat_label": self.seat_label,
        }


@dataclass
class InvigilationAssignment:
    slot_key: str
    room_id: str
    faculty_id: str
    faculty_name: str
    department: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "slot_key": self.slot_key,
            "room_id": self.room_id,
            "faculty_id": self.faculty_id,
            "faculty_name": self.faculty_name,
            "department": self.department,
        }


@dataclass
class ConflictReport:
    conflict_type: str  # e.g., 'STUDENT_EXAM_OVERLAP', 'CAPACITY_DEFICIT', 'FACULTY_DEFICIT', etc.
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    remedy: str = ""


@dataclass
class ScheduleResult:
    success: bool
    seating_assignments: List[StudentSeatAssignment] = field(default_factory=list)
    invigilation_assignments: List[InvigilationAssignment] = field(default_factory=list)
    conflicts: List[ConflictReport] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    validation_passed: bool = False
    validation_notes: List[str] = field(default_factory=list)
    validation_summary: Optional[Any] = None

    def __getattr__(self, name: str) -> Any:
        if name == "validation_summary":
            return None
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


