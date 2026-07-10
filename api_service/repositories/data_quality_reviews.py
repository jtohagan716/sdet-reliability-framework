from typing import Any

from api_service.database import get_connection


VALID_REVIEW_STATUSES = {
    "pending_review",
    "confirmed_correct",
    "flagged_incorrect",
    "needs_reconciliation",
    "closed",
}


def list_review_items(
    review_status: str | None = None,
    limit: int = 25,
) -> list[dict[str, Any]]:
    safe_limit = max(1, min(limit, 100))

    with get_connection() as conn:
        with conn.cursor() as cursor:
            if review_status:
                cursor.execute(
                    """
                    SELECT
                        review_item_key,
                        review_source,
                        patient_reference,
                        encounter_reference,
                        related_event_id,
                        related_decision_id,
                        review_reason,
                        risk_summary,
                        review_priority,
                        review_status,
                        assigned_role,
                        assigned_to,
                        created_at,
                        reviewed_at,
                        reviewed_by,
                        review_outcome,
                        review_notes,
                        details
                    FROM patient_data_quality_review_items
                    WHERE review_status = %s
                    ORDER BY created_at DESC, review_item_id DESC
                    LIMIT %s;
                    """,
                    (review_status, safe_limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT
                        review_item_key,
                        review_source,
                        patient_reference,
                        encounter_reference,
                        related_event_id,
                        related_decision_id,
                        review_reason,
                        risk_summary,
                        review_priority,
                        review_status,
                        assigned_role,
                        assigned_to,
                        created_at,
                        reviewed_at,
                        reviewed_by,
                        review_outcome,
                        review_notes,
                        details
                    FROM patient_data_quality_review_items
                    ORDER BY created_at DESC, review_item_id DESC
                    LIMIT %s;
                    """,
                    (safe_limit,),
                )

            return list(cursor.fetchall())


def get_review_item_detail(review_item_key: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    review_item_id,
                    review_item_key,
                    review_source,
                    patient_reference,
                    encounter_reference,
                    related_event_id,
                    related_decision_id,
                    review_reason,
                    risk_summary,
                    review_priority,
                    review_status,
                    assigned_role,
                    assigned_to,
                    created_at,
                    reviewed_at,
                    reviewed_by,
                    review_outcome,
                    review_notes,
                    details
                FROM patient_data_quality_review_items
                WHERE review_item_key = %s;
                """,
                (review_item_key,),
            )

            review_item = cursor.fetchone()

            if review_item is None:
                return None

            cursor.execute(
                """
                SELECT
                    action_type,
                    action_by,
                    action_role,
                    action_note,
                    action_at,
                    details
                FROM patient_data_quality_review_actions
                WHERE review_item_id = %s
                ORDER BY review_action_id;
                """,
                (review_item["review_item_id"],),
            )

            actions = list(cursor.fetchall())

            review_item_without_internal_id = dict(review_item)
            review_item_without_internal_id.pop("review_item_id", None)
            review_item_without_internal_id["actions"] = actions

            return review_item_without_internal_id