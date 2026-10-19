"""Reusable UI presentation components for Streamlit views."""
import streamlit as st
import streamlit.components.v1 as components
from typing import List, Dict, Any, Optional
from csp.models import ConflictReport, StudentSeatAssignment, Room


def render_header(title: str, subtitle: str, icon: str = "🎓"):
    """Renders a stylish gradient page header."""
    st.markdown(
        f"""
        <div class="page-header">
            <h1>{icon} {title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(title: str, value: Any, subtext: str = ""):
    """Renders an attractive KPI card."""
    sub_html = f'<div class="metric-sub">{subtext}</div>' if subtext else ""
    return f"""
    <div class="metric-card">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
        {sub_html}
    </div>
    """


def render_conflict_card(conflict: ConflictReport, index: int = 1):
    """Renders an explicit, non-silent constraint violation alert."""
    remedy_html = (
        f'<div class="conflict-remedy"><strong>Actionable Resolution:</strong> {conflict.remedy}</div>'
        if conflict.remedy
        else ""
    )
    st.markdown(
        f"""
        <div class="conflict-box">
            <h4>⚠️ Conflict #{index}: {conflict.conflict_type.replace('_', ' ').title()}</h4>
            <div style="font-size: 0.95rem; color: #4B1220;">{conflict.description}</div>
            {remedy_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_subject_badge_class(exam_code: str) -> str:
    """Determines CSS badge style based on exam subject prefix."""
    code = exam_code.upper()
    if code.startswith("CS"):
        return "badge-cs"
    elif code.startswith("EC"):
        return "badge-ec"
    elif code.startswith("ME"):
        return "badge-me"
    elif code.startswith("MA"):
        return "badge-ma"
    return "badge-cs"


def render_interactive_grid(room: Room, assignments: List[StudentSeatAssignment]):
    """Renders a 2D interactive physical seat map for a specific room."""
    # Build (row, col) coordinate lookup
    seat_lookup: Dict[tuple, StudentSeatAssignment] = {
        (a.row, a.col): a for a in assignments if a.room_id == room.room_id
    }

    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <h4 style="margin: 0; color: #5B21B6;">Room Layout: {room.room_id} ({room.building})</h4>
            <span style="font-size: 0.85rem; color: #6B7280;">Capacity: {len(seat_lookup)} / {room.capacity} seats filled ({room.rows} rows × {room.cols} cols)</span>
        </div>
        <div style="background: #E2E8F0; text-align: center; padding: 6px; border-radius: 6px; font-weight: 600; color: #475569; font-size: 0.8rem; margin-bottom: 12px; letter-spacing: 0.05em;">
            ◀ FRONT / BLACKBOARD / INVIGILATOR PODIUM ▶
        </div>
        """,
        unsafe_allow_html=True,
    )

    grid_html = ['<div style="overflow-x: auto; padding-bottom: 10px;">']
    for r in range(1, room.rows + 1):
        grid_html.append('<div style="display: flex; justify-content: center; margin-bottom: 6px;">')
        for c in range(1, room.cols + 1):
            if (r, c) in seat_lookup:
                assign = seat_lookup[(r, c)]
                badge_cls = get_subject_badge_class(assign.exam_code)
                pod = f"""
                <div class="seat-pod seat-pod-occupied" title="Seat R{r}C{c}: {assign.student_name} ({assign.student_id}) - {assign.subject_name}">
                    <div class="seat-code">R{r}C{c}</div>
                    <div class="seat-student" style="font-weight: 600;">{assign.student_name.split()[0]}</div>S
                    <span class="seat-tag {badge_cls}">{assign.exam_code}</span>
                </div>
                """
            else:
                pod = f"""
                <div class="seat-pod seat-pod-empty" title="Seat R{r}C{c}: Vacant">
                    <div class="seat-code">R{r}C{c}</div>
                    <div class="seat-student" style="color: #94A3B8;">Vacant</div>
                    <span class="seat-tag" style="background:#F1F5F9; color:#94A3B8;">Empty</span>
                </div>
                """
            grid_html.append(pod)
        grid_html.append("</div>")
    grid_html.append("</div>")
    components.html(
    f"""
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; }}
        .seat-pod {{
            display: inline-block;
            width: 95px;
            height: 72px;
            margin: 4px;
            padding: 6px 4px;
            box-sizing: border-box;
            border-radius: 8px;
            text-align: center;
            vertical-align: top;
            font-size: 12px;
            overflow: hidden;
        }}
        .seat-pod-occupied {{
            background: #EDE9FE;
            border: 1px solid #8B5CF6;
            color: #4C1D95;
        }}
        .seat-pod-empty {{
            background: #F8FAFC;
            border: 1px dashed #CBD5E1;
            color: #94A3B8;
        }}
        .seat-code {{ font-size: 10px; }}
        .seat-student {{ font-weight: 600; margin: 4px 0; }}
        .seat-tag {{ font-size: 10px; }}
    </style>
    {"".join(grid_html)}
    """,
    height=700,
    scrolling=True,
)
   


def render_validation_summary_card(summary, title_prefix: str = "Independent Schedule Validator Audit"):
    """Renders a comprehensive PASS/FAIL independent validation summary with explanations."""
    if summary is None:
        return

    if summary.overall_passed:
        st.markdown(
            f"""
            <div style="background: #ECFDF5; border: 2px solid #059669; border-radius: 10px; padding: 18px; margin-bottom: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-size: 1.25rem; font-weight: 800; color: #065F46;">
                        🛡️ {title_prefix}: <span style="background: #059669; color: white; padding: 2px 10px; border-radius: 6px; font-size: 0.95rem;">PASS</span>
                    </div>
                    <div style="font-size: 0.8rem; color: #047857;">Verified at: {summary.timestamp}</div>
                </div>
                <div style="margin-top: 6px; font-size: 0.92rem; color: #064E3B;">
                    <strong>{summary.passed_hard_checks} of {summary.total_hard_checks}</strong> hard physical and institutional constraints verified with ZERO violations.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div style="background: #FFF1F2; border: 2px solid #E11D48; border-radius: 10px; padding: 18px; margin-bottom: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-size: 1.25rem; font-weight: 800; color: #9F1239;">
                        🛑 {title_prefix}: <span style="background: #E11D48; color: white; padding: 2px 10px; border-radius: 6px; font-size: 0.95rem;">FAIL</span>
                    </div>
                    <div style="font-size: 0.8rem; color: #BE123C;">Verified at: {summary.timestamp}</div>
                </div>
                <div style="margin-top: 6px; font-size: 0.92rem; color: #881337;">
                    <strong>{summary.failed_hard_checks} of {summary.total_hard_checks}</strong> hard constraints violated! This schedule cannot be claimed as valid.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Detailed Checklist Table
    st.markdown("##### 📋 Independent Verification Checklist")
    checklist_rows = []
    for check in summary.check_results:
        status_badge = "✅ PASS" if check.passed else "❌ FAIL"
        checklist_rows.append({
            "Constraint Rule": check.check_name,
            "Category": check.category,
            "Status": status_badge,
            "Audit Findings": check.summary,
        })
    import pandas as pd
    df_checks = pd.DataFrame(checklist_rows)
    st.dataframe(df_checks, use_container_width=True, hide_index=True)

    # Explanations for any violations
    if summary.all_violations:
        st.markdown("##### ⚠️ Conflict Breakdown & Remediation Advice")
        for idx, viol in enumerate(summary.all_violations, 1):
            render_conflict_card(viol, index=idx)

    # Actual duty fairness breakdown
    if summary.fairness_metrics:
        fm = summary.fairness_metrics
        with st.expander("⚖️ Actual Workload Distribution & Fairness Details", expanded=False):
            f_col1, f_col2, f_col3, f_col4 = st.columns(4)
            with f_col1:
                st.metric("Fairness Score", f"{fm.get('fairness_score', 0)}%")
            with f_col2:
                st.metric("Jain's Fairness Index", f"{fm.get('jains_fairness_index', 1.0)}")
            with f_col3:
                st.metric("Mean Duties", f"{fm.get('mean_duties', 0.0)}")
            with f_col4:
                st.metric("Std Deviation", f"{fm.get('std_dev', 0.0)}")
            st.caption(f"Calculated directly from actual invigilation duty assignments across {len(fm.get('distribution', {}))} faculty.")

