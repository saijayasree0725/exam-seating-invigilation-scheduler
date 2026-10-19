"""Constraint Satisfaction Problem (CSP) Solver for Exam Seating and Invigilation Duties.

Implements genuine Backtracking Search with MRV heuristic, Forward Checking /
Constraint Propagation, and Least-Constraining / Soft-Preference ordering.
"""
from typing import List, Dict, Set, Tuple, Optional, Any
from collections import defaultdict
import time
import copy

from .models import (
    Student,
    Exam,
    Room,
    Faculty,
    StudentSeatAssignment,
    InvigilationAssignment,
    ConflictReport,
    ScheduleResult,
)
from .constraints import ConstraintValidator, SoftPreferenceEvaluator
from .explainer import ScheduleExplainer
from .validator import IndependentScheduleValidator, ValidationSummary


class ExamCSPSolver:
    """Full-featured Constraint Satisfaction Problem Solver."""

    def __init__(
        self,
        students: List[Student],
        exams: List[Exam],
        rooms: List[Room],
        faculty: List[Faculty],
        enable_seating_separation: bool = True,
        enable_workload_balance: bool = True,
        enable_room_packing: bool = True,
    ):
        self.students = students
        self.exams = exams
        self.rooms = [r for r in rooms if r.is_active and r.capacity > 0]
        self.faculty = faculty

        # Soft preference toggles
        self.enable_seating_separation = enable_seating_separation
        self.enable_workload_balance = enable_workload_balance
        self.enable_room_packing = enable_room_packing

        # Metrics tracking
        self.metrics: Dict[str, Any] = {
            "start_time": 0.0,
            "end_time": 0.0,
            "runtime_seconds": 0.0,
            "seating_nodes_visited": 0,
            "seating_backtracks": 0,
            "invigilation_nodes_visited": 0,
            "invigilation_backtracks": 0,
            "forward_checking_prunings": 0,
        }

    def solve(self) -> ScheduleResult:
        """Executes full CSP solving pipeline with constraint checking and diagnostics."""
        t0 = time.time()
        self.metrics["start_time"] = t0

        # Step 1: Precondition & Hard Constraint Sanity Diagnosis
        pre_conflicts = ScheduleExplainer.diagnose_preconditions(
            self.students, self.exams, self.rooms, self.faculty
        )
        if pre_conflicts:
            self.metrics["runtime_seconds"] = round(time.time() - t0, 4)
            val_summary = IndependentScheduleValidator.validate_schedule(
                self.students, self.exams, self.rooms, self.faculty, [], []
            )
            for pc in pre_conflicts:
                if not any(v.description == pc.description for v in val_summary.all_violations):
                    val_summary.all_violations.append(pc)
            val_summary.overall_passed = False
            val_summary.failed_hard_checks = max(1, val_summary.failed_hard_checks)
            return ScheduleResult(
                success=False,
                conflicts=pre_conflicts,
                metrics=self.metrics,
                validation_passed=False,
                validation_notes=["Schedule generation halted due to pre-flight hard constraint violations."],
                validation_summary=val_summary,
            )

        # Step 2: Solve Seating Allocation CSP by Slot
        seating_assignments, seating_conflicts, used_rooms_per_slot = self._solve_seating_csp()
        if seating_conflicts:
            self.metrics["runtime_seconds"] = round(time.time() - t0, 4)
            val_summary = IndependentScheduleValidator.validate_schedule(
                self.students, self.exams, self.rooms, self.faculty, seating_assignments, []
            )
            for sc in seating_conflicts:
                if not any(v.description == sc.description for v in val_summary.all_violations):
                    val_summary.all_violations.append(sc)
            val_summary.overall_passed = False
            val_summary.failed_hard_checks = max(1, val_summary.failed_hard_checks)
            return ScheduleResult(
                success=False,
                seating_assignments=seating_assignments,
                conflicts=seating_conflicts,
                metrics=self.metrics,
                validation_passed=False,
                validation_notes=["Seating assignment CSP could not find a valid assignment."],
                validation_summary=val_summary,
            )

        # Step 3: Solve Invigilation Duty CSP across slots and active rooms
        invigilation_assignments, invig_conflicts = self._solve_invigilation_csp(used_rooms_per_slot)
        if invig_conflicts:
            self.metrics["runtime_seconds"] = round(time.time() - t0, 4)
            val_summary = IndependentScheduleValidator.validate_schedule(
                self.students, self.exams, self.rooms, self.faculty, seating_assignments, invigilation_assignments
            )
            for ic in invig_conflicts:
                if not any(v.description == ic.description for v in val_summary.all_violations):
                    val_summary.all_violations.append(ic)
            val_summary.overall_passed = False
            val_summary.failed_hard_checks = max(1, val_summary.failed_hard_checks)
            return ScheduleResult(
                success=False,
                seating_assignments=seating_assignments,
                invigilation_assignments=invigilation_assignments,
                conflicts=invig_conflicts,
                metrics=self.metrics,
                validation_passed=False,
                validation_notes=["Invigilation assignment CSP failed to satisfy faculty constraints."],
                validation_summary=val_summary,
            )

        self.metrics["end_time"] = time.time()
        self.metrics["runtime_seconds"] = round(self.metrics["end_time"] - t0, 4)

        # Step 4: Full Independent Post-Verification
        validation_summary = IndependentScheduleValidator.validate_schedule(
            students=self.students,
            exams=self.exams,
            rooms=self.rooms,
            faculty=self.faculty,
            seating_assignments=seating_assignments,
            invigilation_assignments=invigilation_assignments,
        )

        if not validation_summary.overall_passed:
            return ScheduleResult(
                success=False,
                seating_assignments=seating_assignments,
                invigilation_assignments=invigilation_assignments,
                conflicts=validation_summary.all_violations,
                metrics=self.metrics,
                validation_passed=False,
                validation_notes=["Independent post-verification failed: Hard constraint violation detected!"],
                validation_summary=validation_summary,
            )

        # Step 5: Soft Preference Scoring & Actual Duty Fairness
        separation_score = SoftPreferenceEvaluator.evaluate_seating_separation(seating_assignments)
        workload_score = validation_summary.fairness_metrics
        room_eff_score = SoftPreferenceEvaluator.evaluate_room_efficiency(seating_assignments, self.rooms)

        composite_soft_score = round(
            (separation_score["score"] * 0.45)
            + (workload_score["fairness_score"] * 0.35)
            + (room_eff_score["score"] * 0.20),
            1,
        )

        self.metrics["separation_metrics"] = separation_score
        self.metrics["workload_metrics"] = workload_score
        self.metrics["room_efficiency_metrics"] = room_eff_score
        self.metrics["soft_score"] = composite_soft_score

        validation_notes = [
            f"All {validation_summary.total_hard_checks} Hard Constraints strictly verified by Independent Validator.",
            f"Seating Anti-Cheating Separation: {separation_score['score']}%",
            f"Faculty Workload Balance (Actual Duty Distribution): {workload_score['fairness_score']}% (Jain's Index: {workload_score['jains_fairness_index']})",
            f"Room Space Efficiency: {room_eff_score['score']}%",
            f"Overall Composite Quality Score: {composite_soft_score}/100",
        ]

        return ScheduleResult(
            success=True,
            seating_assignments=seating_assignments,
            invigilation_assignments=invigilation_assignments,
            conflicts=[],
            metrics=self.metrics,
            validation_passed=True,
            validation_notes=validation_notes,
            validation_summary=validation_summary,
        )

    # -------------------------------------------------------------------------
    # PART A: Seating Plan CSP Solver
    # -------------------------------------------------------------------------
    def _solve_seating_csp(
        self,
    ) -> Tuple[List[StudentSeatAssignment], List[ConflictReport], Dict[str, List[str]]]:
        """Solves student seating allocation per slot using CSP backtracking and propagation."""
        exam_slot_map = {e.exam_code: e.slot_key for e in self.exams}
        exam_obj_map = {e.exam_code: e for e in self.exams}
        student_obj_map = {s.student_id: s for s in self.students}

        # Group student appearances by slot: slot_key -> List[(student_id, exam_code)]
        slot_attendees: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
        for st in self.students:
            for course in st.courses:
                if course in exam_slot_map:
                    slot = exam_slot_map[course]
                    slot_attendees[slot].append((st.student_id, course))

        all_seating: List[StudentSeatAssignment] = []
        used_rooms_per_slot: Dict[str, List[str]] = {}

        # Available rooms sorted by capacity (efficient packing)
        available_rooms = sorted(self.rooms, key=lambda r: r.capacity, reverse=True)

        for slot_key, attendees in slot_attendees.items():
            if not attendees:
                continue

            # Check capacity
            total_students = len(attendees)
            total_room_cap = sum(r.capacity for r in available_rooms)
            if total_students > total_room_cap:
                return (
                    [],
                    [
                        ConflictReport(
                            conflict_type="ROOM_CAPACITY_DEFICIT",
                            description=(
                                f"In slot [{slot_key}], {total_students} students need seats, "
                                f"but total active room capacity is {total_room_cap}."
                            ),
                            details={"slot": slot_key, "students": total_students, "capacity": total_room_cap},
                            remedy="Add more exam rooms or reduce student load for this slot.",
                        )
                    ],
                    {},
                )

            # Determine minimal rooms required to hold total_students
            selected_rooms: List[Room] = []
            running_cap = 0
            for r in available_rooms:
                selected_rooms.append(r)
                running_cap += r.capacity
                if running_cap >= total_students:
                    break

            used_rooms_per_slot[slot_key] = [r.room_id for r in selected_rooms]

            # Generate candidate seat list: List[(room_id, row, col)]
            # We create an interleaved seat grid to maximize subject distance if enabled
            all_seats: List[Tuple[str, int, int]] = []
            for r in selected_rooms:
                for row in range(1, r.rows + 1):
                    for col in range(1, r.cols + 1):
                        all_seats.append((r.room_id, row, col))

            # Group attendees by exam code for interleaved / checkerboard placement
            attendees_by_exam: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
            for st_id, ex_code in attendees:
                attendees_by_exam[ex_code].append((st_id, ex_code))

            # Order attendees to alternate exam subjects (soft preference: avoid adjacent same subject)
            ordered_attendees: List[Tuple[str, str]] = []
            if self.enable_seating_separation and len(attendees_by_exam) > 1:
                # Round-robin interleaving among exam cohorts
                cohort_lists = list(attendees_by_exam.values())
                max_len = max(len(c) for c in cohort_lists)
                for i in range(max_len):
                    for cohort in cohort_lists:
                        if i < len(cohort):
                            ordered_attendees.append(cohort[i])
            else:
                ordered_attendees = attendees

            # Backtracking assignment of seats to students in this slot
            slot_assignments = self._backtrack_seating(
                slot_key=slot_key,
                attendees=ordered_attendees,
                available_seats=all_seats,
                student_obj_map=student_obj_map,
                exam_obj_map=exam_obj_map,
            )

            if slot_assignments is None:
                return (
                    [],
                    [
                        ConflictReport(
                            conflict_type="SEATING_BACKTRACK_FAILURE",
                            description=f"Could not find a collision-free seating arrangement for slot [{slot_key}].",
                            details={"slot": slot_key},
                            remedy="Check room dimensions and student counts.",
                        )
                    ],
                    {},
                )

            all_seating.extend(slot_assignments)

        return all_seating, [], used_rooms_per_slot

    def _backtrack_seating(
        self,
        slot_key: str,
        attendees: List[Tuple[str, str]],
        available_seats: List[Tuple[str, int, int]],
        student_obj_map: Dict[str, Student],
        exam_obj_map: Dict[str, Exam],
    ) -> Optional[List[StudentSeatAssignment]]:
        """Performs backtracking search to assign seats with forward checking and separation."""
        assigned: List[StudentSeatAssignment] = []
        assigned_seats: Set[Tuple[str, int, int]] = set()
        occupied_grid: Dict[Tuple[str, int, int], str] = {}  # (room, r, c) -> exam_code

        # Domain for each student index is available_seats
        # Since number of seats >= number of students, we search systematically
        def backtrack(index: int) -> bool:
            self.metrics["seating_nodes_visited"] += 1
            if index == len(attendees):
                return True

            student_id, exam_code = attendees[index]
            student_obj = student_obj_map[student_id]
            exam_obj = exam_obj_map[exam_code]

            # Heuristic value ordering for seat selection:
            # Prefer seats whose orthogonal neighbors are empty or of a different exam code
            candidate_seats = [s for s in available_seats if s not in assigned_seats]

            if self.enable_seating_separation:
                # Rank seats by penalty (number of adjacent seats with SAME exam_code)
                def seat_penalty(seat: Tuple[str, int, int]) -> int:
                    room, r, c = seat
                    penalty = 0
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nbr = (room, r + dr, c + dc)
                        if nbr in occupied_grid and occupied_grid[nbr] == exam_code:
                            penalty += 1
                    return penalty

                # Sort candidate seats: lowest penalty first
                candidate_seats.sort(key=seat_penalty)

            for seat in candidate_seats:
                room_id, r, c = seat

                # Forward checking / constraint validation:
                # Seat must not already be taken (Hard constraint 2)
                if seat in assigned_seats:
                    continue

                # Make assignment
                assigned_seats.add(seat)
                occupied_grid[seat] = exam_code
                label = f"{room_id}-R{r}C{c}"
                assignment = StudentSeatAssignment(
                    student_id=student_id,
                    student_name=student_obj.name,
                    exam_code=exam_code,
                    subject_name=exam_obj.subject_name,
                    slot_key=slot_key,
                    room_id=room_id,
                    row=r,
                    col=c,
                    seat_label=label,
                )
                assigned.append(assignment)

                # Recurse
                if backtrack(index + 1):
                    return True

                # Undo assignment (Backtrack)
                self.metrics["seating_backtracks"] += 1
                assigned.pop()
                assigned_seats.remove(seat)
                del occupied_grid[seat]

            return False

        if backtrack(0):
            return assigned
        return None

    # -------------------------------------------------------------------------
    # PART B: Invigilation Duty CSP Solver
    # -------------------------------------------------------------------------
    def _solve_invigilation_csp(
        self, used_rooms_per_slot: Dict[str, List[str]]
    ) -> Tuple[List[InvigilationAssignment], List[ConflictReport]]:
        """Solves faculty invigilation duty assignment using CSP backtracking with MRV & forward checking."""
        faculty_map = {f.faculty_id: f for f in self.faculty}

        # Build list of duty variables: (slot_key, room_id)
        variables: List[Tuple[str, str]] = []
        for slot_key, room_list in used_rooms_per_slot.items():
            for room_id in room_list:
                variables.append((slot_key, room_id))

        if not variables:
            return [], []

        # Domains: variable -> List[faculty_id]
        # Initial domain filtering based on availability & max_duties > 0
        domains: Dict[Tuple[str, str], List[str]] = {}
        for var in variables:
            slot, room = var
            valid_fac = []
            for f in self.faculty:
                if f.max_duties <= 0:
                    continue
                # Hard Constraint 5: Unavailable faculty cannot be assigned
                unavail = {u.strip().lower() for u in f.unavailable_slots if u.strip()}
                if slot.strip().lower() not in unavail:
                    valid_fac.append(f.faculty_id)
            domains[var] = valid_fac

            if not valid_fac:
                return (
                    [],
                    [
                        ConflictReport(
                            conflict_type="NO_FACULTY_AVAILABLE_FOR_SLOT",
                            description=(
                                f"Zero available faculty members for Room {room} at slot [{slot}]. "
                                f"All faculty are either unavailable or have 0 max duties."
                            ),
                            details={"slot": slot, "room": room},
                            remedy=f"Mark at least one faculty member available for slot '{slot}'.",
                        )
                    ],
                )

        assignments: Dict[Tuple[str, str], str] = {}
        duty_counts: Dict[str, int] = {f.faculty_id: 0 for f in self.faculty}
        # Key: slot_key -> Set[faculty_id] assigned in that slot
        slot_assigned_faculty: Dict[str, Set[str]] = defaultdict(set)

        # Backtracking with MRV (Minimum Remaining Values) heuristic & Forward Checking
        def select_unassigned_variable(
            current_domains: Dict[Tuple[str, str], List[str]],
        ) -> Optional[Tuple[str, str]]:
            """MRV Heuristic: Choose variable with the smallest number of legal values."""
            unassigned = [v for v in variables if v not in assignments]
            if not unassigned:
                return None
            # MRV: min domain length
            return min(unassigned, key=lambda v: len(current_domains[v]))

        def order_domain_values(var: Tuple[str, str], domain_vals: List[str]) -> List[str]:
            """Least Constraining / Fairness ordering: Choose faculty with the lowest current workload."""
            if not self.enable_workload_balance:
                return domain_vals
            # Sort faculty by current duty count ascending to balance workload
            return sorted(domain_vals, key=lambda fid: duty_counts[fid])

        def forward_check(
            assigned_var: Tuple[str, str],
            assigned_fac_id: str,
            curr_domains: Dict[Tuple[str, str], List[str]],
        ) -> Optional[Dict[Tuple[str, str], List[str]]]:
            """Prunes domains of remaining variables and returns updated domains or None if domain wipeout."""
            slot_curr, room_curr = assigned_var
            new_domains = {}

            for v in variables:
                if v in assignments or v == assigned_var:
                    continue
                v_slot, v_room = v
                cur_list = curr_domains[v]

                # Hard Constraint 4: An invigilator cannot supervise two rooms at the same time
                if v_slot == slot_curr and assigned_fac_id in cur_list:
                    filtered = [f for f in cur_list if f != assigned_fac_id]
                    self.metrics["forward_checking_prunings"] += 1
                else:
                    filtered = list(cur_list)

                # Hard Constraint 6: Faculty workload limits must be respected
                # If assigned_fac_id just reached their max limit, prune from all remaining variables
                fac_obj = faculty_map[assigned_fac_id]
                if duty_counts[assigned_fac_id] >= fac_obj.max_duties:
                    if assigned_fac_id in filtered:
                        filtered = [f for f in filtered if f != assigned_fac_id]
                        self.metrics["forward_checking_prunings"] += 1

                # If any domain becomes empty, forward check fails!
                if not filtered:
                    return None

                new_domains[v] = filtered

            return new_domains

        def backtrack(curr_domains: Dict[Tuple[str, str], List[str]]) -> bool:
            self.metrics["invigilation_nodes_visited"] += 1

            var = select_unassigned_variable(curr_domains)
            if var is None:
                return True  # All variables assigned successfully!

            slot, room = var
            ordered_fac = order_domain_values(var, curr_domains[var])

            for fac_id in ordered_fac:
                fac_obj = faculty_map[fac_id]

                # Hard Constraint Check:
                # 1. Not already assigned in this slot (Hard Constraint 4)
                if fac_id in slot_assigned_faculty[slot]:
                    continue

                # 2. Max duties limit (Hard Constraint 6)
                if duty_counts[fac_id] >= fac_obj.max_duties:
                    continue

                # Assign
                assignments[var] = fac_id
                duty_counts[fac_id] += 1
                slot_assigned_faculty[slot].add(fac_id)

                # Forward Checking / Constraint Propagation
                pruned_domains = forward_check(var, fac_id, curr_domains)

                if pruned_domains is not None:
                    # Recursive step
                    if backtrack(pruned_domains):
                        return True

                # Undo Assignment (Backtrack)
                self.metrics["invigilation_backtracks"] += 1
                del assignments[var]
                duty_counts[fac_id] -= 1
                slot_assigned_faculty[slot].remove(fac_id)

            return False

        if not backtrack(domains):
            return (
                [],
                [
                    ConflictReport(
                        conflict_type="INVIGILATION_CSP_INFEASIBLE",
                        description=(
                            "The CSP solver exhausted all backtracking branches: unable to assign "
                            "invigilators without violating faculty availability, slot overlaps, "
                            "or workload limits."
                        ),
                        details={
                            "total_duties_required": len(variables),
                            "faculty_roster_count": len(self.faculty),
                        },
                        remedy="Increase 'Max Duties' for available faculty or mark faculty available for congested slots.",
                    )
                ],
            )

        # Convert assignments dictionary to InvigilationAssignment objects
        invigilation_results: List[InvigilationAssignment] = []
        for (slot, room), fac_id in assignments.items():
            fac = faculty_map[fac_id]
            invigilation_results.append(
                InvigilationAssignment(
                    slot_key=slot,
                    room_id=room,
                    faculty_id=fac_id,
                    faculty_name=fac.name,
                    department=fac.department,
                )
            )

        return invigilation_results, []
