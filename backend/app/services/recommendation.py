"""
BhoomiGuard AI — Rule-Based Recommendation Engine
Generates actionable recommendations based on SHAP risk factors + input features.
"""
from typing import Any


THRESHOLD_HIGH_LEGAL = 10
THRESHOLD_HIGH_APPROVAL = 60
THRESHOLD_HIGH_COMPENSATION = 0.5   # fraction of total_landowners
THRESHOLD_HIGH_DOCUMENTS = 20
THRESHOLD_HIGH_OBJECTIONS = 15
THRESHOLD_HIGH_LAND_PENDING = 50.0  # percent
THRESHOLD_HIGH_PREVIOUS_DELAY = 30  # days
THRESHOLD_LOW_SURVEY = 60.0         # percent


def generate_recommendations(
    input_features: dict[str, Any],
    top_risk_factors: list[dict],
    risk_level: str,
    district_delay_rate: float = None,
) -> list[dict]:
    """
    Generate actionable recommendations based on:
    1. Input feature values (primary — project-level)
    2. Top SHAP risk factors (direction of impact)
    3. Risk level
    4. Optional district historical context
    """
    recommendations = []
    risk_feature_names = {r["feature"].lower() for r in top_risk_factors}

    total_owners = input_features.get("total_landowners", 1) or 1

    # ── Legal cases ──────────────────────────────────────────────────
    if input_features.get("legal_cases", 0) >= THRESHOLD_HIGH_LEGAL:
        recommendations.append({
            "priority": "High",
            "action": "Prioritize Legal Case Resolution",
            "reason": (
                f"{input_features['legal_cases']} active legal cases detected. "
                "Engage legal counsel immediately to expedite case reviews and settlements."
            ),
        })

    # ── Approval pending days ──────────────────────────────────────────
    if input_features.get("approval_pending_days", 0) >= THRESHOLD_HIGH_APPROVAL:
        recommendations.append({
            "priority": "High",
            "action": "Escalate Pending Approvals",
            "reason": (
                f"Approval has been pending for {input_features['approval_pending_days']} days. "
                "Review the approval chain, identify bottlenecks, and escalate to senior officials."
            ),
        })

    # ── Compensation pending ──────────────────────────────────────────
    comp_ratio = input_features.get("compensation_pending", 0) / total_owners
    if comp_ratio >= THRESHOLD_HIGH_COMPENSATION:
        pct = round(comp_ratio * 100, 1)
        recommendations.append({
            "priority": "High",
            "action": "Accelerate Compensation Processing",
            "reason": (
                f"{pct}% of landowners ({input_features['compensation_pending']}/{total_owners}) "
                "have pending compensation. Prioritize verification, valuation, and disbursement."
            ),
        })

    # ── Documents pending ──────────────────────────────────────────────
    if input_features.get("documents_pending", 0) >= THRESHOLD_HIGH_DOCUMENTS:
        recommendations.append({
            "priority": "Medium",
            "action": "Complete Missing Documentation",
            "reason": (
                f"{input_features['documents_pending']} documents are pending. "
                "Assign dedicated officers to complete verification and digitization."
            ),
        })

    # ── Objections ──────────────────────────────────────────────────────
    if input_features.get("objections_count", 0) >= THRESHOLD_HIGH_OBJECTIONS:
        recommendations.append({
            "priority": "High",
            "action": "Conduct Stakeholder Grievance Sessions",
            "reason": (
                f"{input_features['objections_count']} objections filed by landowners. "
                "Schedule grievance redressal meetings to address concerns and reduce legal risk."
            ),
        })

    # ── Survey completion ──────────────────────────────────────────────
    if input_features.get("survey_completed_percent", 100) < THRESHOLD_LOW_SURVEY:
        recommendations.append({
            "priority": "Medium",
            "action": "Expedite Land Survey",
            "reason": (
                f"Survey is only {input_features['survey_completed_percent']:.1f}% complete. "
                "Deploy additional survey teams to accelerate completion."
            ),
        })

    # ── High pending land ──────────────────────────────────────────────
    if input_features.get("land_pending_percent", 0) >= THRESHOLD_HIGH_LAND_PENDING:
        recommendations.append({
            "priority": "Medium",
            "action": "Intensive Land Acquisition Drive",
            "reason": (
                f"{input_features['land_pending_percent']:.1f}% of land is still pending acquisition. "
                "Focus resources on unresolved parcels and establish dedicated acquisition teams."
            ),
        })

    # ── Previous delay history ──────────────────────────────────────────
    if input_features.get("previous_delay_days", 0) >= THRESHOLD_HIGH_PREVIOUS_DELAY:
        recommendations.append({
            "priority": "Medium",
            "action": "Implement Proactive Monitoring",
            "reason": (
                f"This project has a history of {input_features['previous_delay_days']} delay days. "
                "Establish weekly progress reviews and milestone-based escalation protocols."
            ),
        })

    # ── District-level context ──────────────────────────────────────────
    if district_delay_rate is not None and district_delay_rate > 0.6:
        pct = round(district_delay_rate * 100, 1)
        recommendations.append({
            "priority": "Low",
            "action": "District-Level Coordination",
            "reason": (
                f"This district has a historical delay rate of {pct}%. "
                "Coordinate with district administration for streamlined approval processes."
            ),
        })

    # ── Critical risk catch-all ──────────────────────────────────────
    if risk_level == "Critical" and len(recommendations) == 0:
        recommendations.append({
            "priority": "High",
            "action": "Immediate Management Review Required",
            "reason": (
                "This project has been identified as Critical risk. "
                "Escalate immediately to senior management for emergency intervention."
            ),
        })

    # ── AI/SHAP Driven Dynamic Rules ──────────────────────────────────────
    # If the model explicitly identified a feature as a major risk driver, but it didn't hit 
    # our static rules, add an AI-driven recommendation for it.
    for factor in top_risk_factors:
        feature_label = factor["feature"]
        importance = factor["importance"]
        if factor["direction"] == "increases_risk" and importance > 0.05:
            # Map feature back to actionable item
            action = f"Mitigate risk driven by {feature_label}"
            reason = f"The AI model identified {feature_label} as a significant driver of delay risk (Impact: {importance:.2f}). Please review this area closely."
            
            # Ensure we don't duplicate existing static recommendations
            if "Legal" in feature_label and any("Legal" in r["action"] for r in recommendations): continue
            if "Approval" in feature_label and any("Approval" in r["action"] for r in recommendations): continue
            if "Compensation" in feature_label and any("Compensation" in r["action"] for r in recommendations): continue
            if "Objection" in feature_label and any("Grievance" in r["action"] for r in recommendations): continue
            
            recommendations.append({
                "priority": "Medium",
                "action": f"[AI Insight] {action}",
                "reason": reason,
            })

    # Sort: High → Medium → Low
    priority_order = {"High": 0, "Medium": 1, "Low": 2}
    recommendations.sort(key=lambda r: priority_order.get(r["priority"], 3))

    # Limit to top 6 most important
    return recommendations[:6]
