# Exam Seating and Invigilation Duty Scheduling using Constraint Satisfaction (CSP)

A complete, beginner-friendly academic project that formulates and solves college examination seating arrangement and faculty invigilation duty assignment as a **Constraint Satisfaction Problem (CSP)** using Python and Streamlit.

---

## 📖 Project Overview

Scheduling examination seating and invigilator duties is a complex combinatorial problem faced by academic institutions each semester. If done manually, it is error-prone, violates student schedules, overburdens faculty, and facilitates cheating if students taking the same exam subject sit adjacent to one another.

This project implements a genuine **AI Constraint Satisfaction Problem (CSP)** solver using:
- **Depth-First Backtracking Search**
- **Minimum Remaining Values (MRV)** heuristic ("fail-first" variable selection)
- **Forward Checking & Constraint Propagation** (early branch pruning)
- **Least Constraining / Fairness Value Ordering** (workload equity)
- **Conflict Diagnostic & Explainer Engine** (pinpoints exact mathematical bottlenecks when a schedule is infeasible instead of silently violating institutional rules)

---

## 🎨 Theme & Visual Design
The user interface features a modern, accessible palette:
- **Primary Purple:** `#5B21B6` / `#7C3AED` (Royal Indigo Header & Badges)
- **Accent Teal:** `#0D9488` / `#14B8A6` (Status & Action Accents)
- **Warm Neutral:** `#FAF7F2` (Soft warm parchment background) & `#FFFFFF` (Card surfaces)

---

## 🛡️ Constraint Satisfaction Problem (CSP) Formulation

### 🔒 Hard Constraints (Strict Compliance)
A schedule is **never** declared valid unless all 6 hard constraints are strictly satisfied:
1. **No Student Overlap:** A student cannot sit for two exams at the same time slot.
2. **Unique Seat Assignment:** Every seat `(Room, Row, Col)` in an exam hall can hold at most one student per slot.
3. **Room Capacity Limits:** Total assigned students never exceed hall capacity (`Rows × Columns`).
4. **No Invigilator Double-Booking:** An invigilator cannot supervise two rooms at the same time.
5. **Faculty Availability:** Faculty members are never scheduled during their marked unavailable slots.
6. **Faculty Workload Limits:** Total assigned invigilation duties &le; `Max Duties` quota.

### ✨ Soft Preferences (Optimization Heuristics)
1. **Anti-Cheating Neighbor Separation:** Interleaves different exam cohorts so students taking the same subject do not sit orthogonally adjacent (left-right, front-back) where possible.
2. **Workload Fairness:** Balances duties equitably among faculty members (minimizing variance/standard deviation).
3. **Room Space Efficiency:** Consolidates examinees into minimum necessary rooms to conserve campus resources.

### 🔍 Non-Silent Conflict Diagnosis
If constraints are mutually contradictory (e.g., student registered for 2 simultaneous exams, room capacity smaller than enrolled examinees, or faculty availability deficit), the solver **halts and explains the root cause** with actionable remediation steps.

---

## 📂 Project Structure

```
├── app.py                     # Main Streamlit application entry point & sidebar routing
├── requirements.txt           # Python dependency specifications
├── README.md                  # Complete documentation and setup guide
├── csp/                       # Core AI / CSP Solver Package
│   ├── __init__.py
│   ├── models.py              # Data models (Student, Exam, Room, Faculty, Assignments)
│   ├── solver.py              # Backtracking solver with MRV, Forward Checking & Heuristics
│   ├── constraints.py         # 6 Hard constraint checkers & 3 Soft preference evaluators
│   └── explainer.py           # Pre-flight diagnostic & root-cause conflict explainer
├── data/                      # Local CSV storage and Demo Data Generator
│   ├── __init__.py
│   ├── storage.py             # CSV read/write and realistic demo dataset generator
│   └── storage_csv/           # Local CSV files (students.csv, exams.csv, rooms.csv, faculty.csv)
├── ui/                        # User Interface Views & Components
│   ├── __init__.py
│   ├── styles.py              # CSS styles (Purple, Teal, Warm Neutral theme)
│   ├── components.py          # 2D Interactive seat grid, KPI metric cards, conflict banners
│   ├── dashboard_view.py      # System Overview, KPIs, CSP guide, quick actions
│   ├── students_view.py       # Student management, course enrollment, CSV import/export
│   ├── exams_view.py          # Exam timetable, slot management, overlap pre-check
│   ├── rooms_view.py          # Examination halls, row × column layout, capacity calculator
│   ├── faculty_view.py        # Faculty roster, max duty limits, unavailability selector
│   ├── generate_view.py       # CSP solver controls, live progress, metric audit
│   ├── seating_view.py        # 2D interactive room layout, "Find My Seat" locator
│   ├── invigilation_view.py   # Supervisor timetable, workload distribution chart
│   └── reports_view.py        # Printable door notices, attendance sheets, master rosters
└── tests/                     # Automated Test Suites
    ├── test_csp_solver.py     # End-to-end CSP solver and constraint satisfaction tests
    └── test_constraints.py    # Unit tests for individual constraints and conflict explainer
```

---

## 🚀 Setup & Execution Instructions

### Prerequisites
- Python 3.9, 3.10, or 3.11 installed.

### 1. Clone or Open Workspace
Open your terminal in the project directory:
```bash
cd "c:\Users\vishn\Downloads\Exam Seating and Invigilation Duty Scheduling using Constraint Satisfaction"
```

### 2. (Optional) Create and Activate Virtual Environment
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
```

### 3. Install Required Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Automated Tests
Verify that all 31 automated tests pass cleanly:
```bash
python -m pytest tests/ -v
```

### 5. Launch the Streamlit Web Application
Run the Streamlit application using:
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🖥️ Application Features & Page Guide

| Page | Key Capabilities |
| :--- | :--- |
| **📊 Dashboard** | High-level metrics, CSP concept visualizer, Independent Validator PASS/FAIL audit summary, 1-click solver run. |
| **👥 Students** | View, search, add, edit, delete students. Import & export CSV rosters. |
| **📝 Exams** | Timetable slots, subject courses, instant warning if student overlap exists. |
| **🏢 Rooms** | Manage exam halls, specify rows & columns, live capacity calculator. |
| **👨‍🏫 Faculty** | Set faculty max duty quotas, mark specific unavailable exam slots. |
| **⚙️ Generate Schedule** | Configure heuristics, execute backtracking CSP, view backtracks, prunings, and Independent Audit. |
| **🪑 Seating Plan** | 2D interactive room visualizer, subject color chips, "Find My Seat" student search. |
| **🛡️ Invigilation Duties**| Room supervisor assignments, workload fairness bar chart, duty quotas. |
| **📄 Reports** | Printable Examination Hall Door Notices, Student Attendance Sheets, CSV exports. |

---

## 🧪 Automated Testing Coverage
The project includes **31 automated tests** covering:

- Baseline schedule generation on standard college demo data
- Hard Constraint 1: Student multi-exam overlap detection
- Hard Constraint 2: Seat uniqueness & single-occupancy invariant
- Hard Constraint 3: Room capacity overflow prevention
- Hard Constraint 4: Invigilator slot double-booking prevention
- Hard Constraint 5: Faculty slot unavailability compliance
- Hard Constraint 6: Faculty max workload limit enforcement
- Deliberate invalidation test: Room capacity overflow detection
- Deliberate invalidation test: Duplicate seat collision detection
- Deliberate invalidation test: Out-of-bounds room grid coordinate detection
- Deliberate invalidation test: Student exam clash detection
- Deliberate invalidation test: Invigilator double-booking detection
- Deliberate invalidation test: Faculty unavailability violation detection
- Deliberate invalidation test: Faculty workload limit violation detection
- Duty distribution fairness: Exact Jain's Fairness Index & StdDev calculations
- Explainer Engine: Diagnostic formatting and remediation advice
- Dashboard integration test: Clean initial dashboard load
- Dashboard integration test: Live audit card rendering with genuine solver results
- Dashboard regression test: Resilience when ScheduleResult lacks validation_summary
- Dashboard regression test: Explanations and FAIL status for infeasible schedules
- Multipage integration test: All 9 navigation pages render without exceptions


Run tests anytime with:
```bash
python -m pytest tests/ -v
```
