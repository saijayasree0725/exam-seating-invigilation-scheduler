"""Data persistence and CSV management with realistic demo dataset generation."""
import os
import csv
from typing import List, Tuple, Dict, Any, Optional
from csp.models import Student, Exam, Room, Faculty


DEMO_DIR = os.path.join(os.path.dirname(__file__), "storage_csv")


class DataStorage:
    """Manages reading, writing, importing, and exporting CSV datasets."""

    def __init__(self, data_dir: str = DEMO_DIR):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.students_file = os.path.join(self.data_dir, "students.csv")
        self.exams_file = os.path.join(self.data_dir, "exams.csv")
        self.rooms_file = os.path.join(self.data_dir, "rooms.csv")
        self.faculty_file = os.path.join(self.data_dir, "faculty.csv")

        # Initialize with demo data if files don't exist
        if not self._all_files_exist():
            self.reset_to_demo_data()

    def _all_files_exist(self) -> bool:
        return (
            os.path.exists(self.students_file)
            and os.path.exists(self.exams_file)
            and os.path.exists(self.rooms_file)
            and os.path.exists(self.faculty_file)
        )

    # -------------------------------------------------------------------------
    # Students CSV
    # -------------------------------------------------------------------------
    def load_students(self) -> List[Student]:
        students = []
        if not os.path.exists(self.students_file):
            return students
        with open(self.students_file, mode="r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                courses_raw = row.get("courses", "")
                course_list = [c.strip() for c in courses_raw.split(";") if c.strip()]
                students.append(
                    Student(
                        student_id=row.get("student_id", "").strip(),
                        name=row.get("name", "").strip(),
                        department=row.get("department", "").strip(),
                        courses=course_list,
                    )
                )
        return students

    def save_students(self, students: List[Student]):
        with open(self.students_file, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["student_id", "name", "department", "courses"])
            writer.writeheader()
            for s in students:
                writer.writerow(s.to_dict())

    # -------------------------------------------------------------------------
    # Exams CSV
    # -------------------------------------------------------------------------
    def load_exams(self) -> List[Exam]:
        exams = []
        if not os.path.exists(self.exams_file):
            return exams
        with open(self.exams_file, mode="r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                exams.append(
                    Exam(
                        exam_code=row.get("exam_code", "").strip(),
                        subject_name=row.get("subject_name", "").strip(),
                        department=row.get("department", "").strip(),
                        date=row.get("date", "").strip(),
                        time_slot=row.get("time_slot", "").strip(),
                        duration_hours=float(row.get("duration_hours", 3.0) or 3.0),
                    )
                )
        return exams

    def save_exams(self, exams: List[Exam]):
        with open(self.exams_file, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["exam_code", "subject_name", "department", "date", "time_slot", "duration_hours"],
            )
            writer.writeheader()
            for e in exams:
                writer.writerow(e.to_dict())

    # -------------------------------------------------------------------------
    # Rooms CSV
    # -------------------------------------------------------------------------
    def load_rooms(self) -> List[Room]:
        rooms = []
        if not os.path.exists(self.rooms_file):
            return rooms
        with open(self.rooms_file, mode="r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                r = int(row.get("rows", 5) or 5)
                c = int(row.get("cols", 6) or 6)
                cap = int(row.get("capacity", r * c) or (r * c))
                active_str = str(row.get("is_active", "Yes")).strip().lower()
                is_act = active_str in ["yes", "true", "1"]
                rooms.append(
                    Room(
                        room_id=row.get("room_id", "").strip(),
                        building=row.get("building", "").strip(),
                        rows=r,
                        cols=c,
                        capacity=cap,
                        is_active=is_act,
                    )
                )
        return rooms

    def save_rooms(self, rooms: List[Room]):
        with open(self.rooms_file, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["room_id", "building", "rows", "cols", "capacity", "is_active"],
            )
            writer.writeheader()
            for r in rooms:
                writer.writerow(r.to_dict())

    # -------------------------------------------------------------------------
    # Faculty CSV
    # -------------------------------------------------------------------------
    def load_faculty(self) -> List[Faculty]:
        faculty_list = []
        if not os.path.exists(self.faculty_file):
            return faculty_list
        with open(self.faculty_file, mode="r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                unavail_raw = row.get("unavailable_slots", "")
                unavail_list = [u.strip() for u in unavail_raw.split(";") if u.strip()]
                faculty_list.append(
                    Faculty(
                        faculty_id=row.get("faculty_id", "").strip(),
                        name=row.get("name", "").strip(),
                        department=row.get("department", "").strip(),
                        max_duties=int(row.get("max_duties", 3) or 3),
                        unavailable_slots=unavail_list,
                    )
                )
        return faculty_list

    def save_faculty(self, faculty_list: List[Faculty]):
        with open(self.faculty_file, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["faculty_id", "name", "department", "max_duties", "unavailable_slots"],
            )
            writer.writeheader()
            for fac in faculty_list:
                writer.writerow(fac.to_dict())

    # -------------------------------------------------------------------------
    # Realistic Sample Demo Dataset
    # -------------------------------------------------------------------------
    def reset_to_demo_data(self):
        """Generates realistic college dataset clearly marked as demo data."""
        # 1. Realistic Exams
        demo_exams = [
            Exam("CS301", "Artificial Intelligence & CSP", "Computer Science", "2026-11-10", "Morning (09:30 - 12:30)", 3.0),
            Exam("EC301", "Digital Signal Processing", "Electronics", "2026-11-10", "Morning (09:30 - 12:30)", 3.0),
            Exam("CS302", "Database Management Systems", "Computer Science", "2026-11-11", "Morning (09:30 - 12:30)", 3.0),
            Exam("ME301", "Thermodynamics & Heat Transfer", "Mechanical", "2026-11-11", "Morning (09:30 - 12:30)", 3.0),
            Exam("MA301", "Applied Probability & Statistics", "Mathematics", "2026-11-12", "Morning (09:30 - 12:30)", 3.0),
            Exam("EC302", "VLSI Circuit Design", "Electronics", "2026-11-12", "Afternoon (01:30 - 04:30)", 3.0),
        ]

        # 2. Realistic Rooms
        demo_rooms = [
            Room("LH-101", "Aryabhata Academic Block", rows=5, cols=5, capacity=25, is_active=True),
            Room("LH-102", "Aryabhata Academic Block", rows=5, cols=5, capacity=25, is_active=True),
            Room("LH-201", "Ramanujan Science Center", rows=4, cols=5, capacity=20, is_active=True),
            Room("LH-202", "Ramanujan Science Center", rows=4, cols=4, capacity=16, is_active=True),
        ]

        # 3. Realistic Faculty
        demo_faculty = [
            Faculty("FAC-01", "Dr. Meera Nambiar", "Computer Science", max_duties=3, unavailable_slots=["2026-11-12 | Afternoon (01:30 - 04:30)"]),
            Faculty("FAC-02", "Prof. Rajesh Verma", "Electronics", max_duties=3, unavailable_slots=[]),
            Faculty("FAC-03", "Dr. Sunita Kulkarni", "Mathematics", max_duties=2, unavailable_slots=["2026-11-10 | Morning (09:30 - 12:30)"]),
            Faculty("FAC-04", "Prof. Amit Banerjee", "Mechanical", max_duties=3, unavailable_slots=[]),
            Faculty("FAC-05", "Dr. Vikram Joshi", "Computer Science", max_duties=2, unavailable_slots=[]),
            Faculty("FAC-06", "Dr. Ananya Ray", "Electronics", max_duties=3, unavailable_slots=[]),
            Faculty("FAC-07", "Prof. Karthik Iyer", "Mechanical", max_duties=2, unavailable_slots=[]),
            Faculty("FAC-08", "Dr. Priya Deshmukh", "Humanities", max_duties=2, unavailable_slots=[]),
        ]

        # 4. Realistic Students (42 students across CS, EC, ME with non-overlapping course registrations)
        demo_students = [
            # CS Cohort (taking CS301, CS302, MA301)
            Student("CS-01", "Aarav Sharma", "Computer Science", ["CS301", "CS302", "MA301"]),
            Student("CS-02", "Diya Patel", "Computer Science", ["CS301", "CS302", "MA301"]),
            Student("CS-03", "Rohan Gupta", "Computer Science", ["CS301", "CS302", "MA301"]),
            Student("CS-04", "Ananya Singh", "Computer Science", ["CS301", "CS302", "MA301"]),
            Student("CS-05", "Ishaan Roy", "Computer Science", ["CS301", "CS302", "MA301"]),
            Student("CS-06", "Sneha Nair", "Computer Science", ["CS301", "CS302", "MA301"]),
            Student("CS-07", "Kabir Mehta", "Computer Science", ["CS301", "CS302"]),
            Student("CS-08", "Pooja Reddy", "Computer Science", ["CS301", "CS302"]),
            Student("CS-09", "Arjun Das", "Computer Science", ["CS301", "CS302"]),
            Student("CS-10", "Neha Chawla", "Computer Science", ["CS301", "CS302"]),
            Student("CS-11", "Aditya Bose", "Computer Science", ["CS301", "CS302"]),
            Student("CS-12", "Riya Sen", "Computer Science", ["CS301", "CS302"]),
            Student("CS-13", "Siddharth Rao", "Computer Science", ["CS301", "CS302"]),
            Student("CS-14", "Kavya Menon", "Computer Science", ["CS301", "CS302"]),
            # EC Cohort (taking EC301, EC302, MA301)
            Student("EC-01", "Varun Bhat", "Electronics", ["EC301", "EC302", "MA301"]),
            Student("EC-02", "Tanvi Joshi", "Electronics", ["EC301", "EC302", "MA301"]),
            Student("EC-03", "Yash Malhotra", "Electronics", ["EC301", "EC302", "MA301"]),
            Student("EC-04", "Isha Mukherjee", "Electronics", ["EC301", "EC302", "MA301"]),
            Student("EC-05", "Manish Saxena", "Electronics", ["EC301", "EC302", "MA301"]),
            Student("EC-06", "Shruti Pillai", "Electronics", ["EC301", "EC302", "MA301"]),
            Student("EC-07", "Nikhil Hegde", "Electronics", ["EC301", "EC302"]),
            Student("EC-08", "Bhavna Iyer", "Electronics", ["EC301", "EC302"]),
            Student("EC-09", "Harsh Vardhan", "Electronics", ["EC301", "EC302"]),
            Student("EC-10", "Meera Krishnan", "Electronics", ["EC301", "EC302"]),
            Student("EC-11", "Gaurav Kapoor", "Electronics", ["EC301", "EC302"]),
            Student("EC-12", "Deepika Bhatt", "Electronics", ["EC301", "EC302"]),
            Student("EC-13", "Devendra Kumar", "Electronics", ["EC301", "EC302"]),
            Student("EC-14", "Anushka Ghosh", "Electronics", ["EC301", "EC302"]),
            # ME Cohort (taking ME301, MA301)
            Student("ME-01", "Kunal Thakur", "Mechanical", ["ME301", "MA301"]),
            Student("ME-02", "Preeti Kulkarni", "Mechanical", ["ME301", "MA301"]),
            Student("ME-03", "Sameer Deshmukh", "Mechanical", ["ME301", "MA301"]),
            Student("ME-04", "Gayatri Chauhan", "Mechanical", ["ME301", "MA301"]),
            Student("ME-05", "Aakash Pandey", "Mechanical", ["ME301", "MA301"]),
            Student("ME-06", "Shweta Tiwari", "Mechanical", ["ME301", "MA301"]),
            Student("ME-07", "Rahul Aggarwal", "Mechanical", ["ME301"]),
            Student("ME-08", "Sonali Mishra", "Mechanical", ["ME301"]),
            Student("ME-09", "Vikas Dubey", "Mechanical", ["ME301"]),
            Student("ME-10", "Swati Namboodiri", "Mechanical", ["ME301"]),
            Student("ME-11", "Prateek Yadav", "Mechanical", ["ME301"]),
            Student("ME-12", "Monika Jain", "Mechanical", ["ME301"]),
            Student("ME-13", "Tarun Goel", "Mechanical", ["ME301"]),
            Student("ME-14", "Simran Gill", "Mechanical", ["ME301"]),
        ]

        self.save_exams(demo_exams)
        self.save_rooms(demo_rooms)
        self.save_faculty(demo_faculty)
        self.save_students(demo_students)
