import json
from pathlib import Path


MESSAGE_EVENT_DIR = Path("test_data/fhir/message_events")


def load_message_event(filename: str) -> dict:
    """
    Load a synthetic healthcare message event fixture.

    These files are project-specific wrappers used to model FHIR-style
    interoperability reliability scenarios.
    """
    event_path = MESSAGE_EVENT_DIR / filename

    with event_path.open("r", encoding="utf-8") as event_file:
        return json.load(event_file)


def process_encounter_message_events(events: list[dict]) -> tuple[dict, list[dict]]:
    """
    Process synthetic Encounter message events in arrival order.

    Rule:
        A message with an older sequence_number must not overwrite the current
        Encounter state when a newer sequence_number has already been accepted.
    """
    current_state = None
    processing_decisions = []

    for event in sorted(events, key=lambda item: item["arrival_order"]):
        resource_reference = event["resource_reference"]
        sequence_number = event["sequence_number"]

        if current_state is None:
            current_state = {
                "resource_reference": resource_reference,
                "sequence_number": sequence_number,
                "payload_completeness": event["payload_completeness"],
                "resource": event["resource"],
                "source_event_id": event["event_id"],
            }

            processing_decisions.append(
                {
                    "event_id": event["event_id"],
                    "resource_reference": resource_reference,
                    "sequence_number": sequence_number,
                    "accepted_as_current": True,
                    "stale": False,
                    "reason": "first message accepted as current state",
                }
            )
            continue

        if sequence_number > current_state["sequence_number"]:
            current_state = {
                "resource_reference": resource_reference,
                "sequence_number": sequence_number,
                "payload_completeness": event["payload_completeness"],
                "resource": event["resource"],
                "source_event_id": event["event_id"],
            }

            processing_decisions.append(
                {
                    "event_id": event["event_id"],
                    "resource_reference": resource_reference,
                    "sequence_number": sequence_number,
                    "accepted_as_current": True,
                    "stale": False,
                    "reason": "newer message accepted as current state",
                }
            )
            continue

        processing_decisions.append(
            {
                "event_id": event["event_id"],
                "resource_reference": resource_reference,
                "sequence_number": sequence_number,
                "accepted_as_current": False,
                "stale": True,
                "reason": "older message rejected to protect current state",
            }
        )

    return current_state, processing_decisions


def test_older_partial_encounter_message_does_not_overwrite_newer_complete_state():
    """
    Validate stale-message protection for synthetic FHIR-style Encounter updates.

    Arrival order:
        1. sequence 2, finished, complete
        2. sequence 1, in-progress, partial

    Expected result:
        The final current state remains sequence 2, finished, complete.
        The older partial message is marked stale.
    """
    newer_complete_message = load_message_event(
        "encounter-message-sequence-002-complete.json"
    )
    older_partial_message = load_message_event(
        "encounter-message-sequence-001-partial.json"
    )

    events = [
        newer_complete_message,
        older_partial_message,
    ]

    current_state, processing_decisions = process_encounter_message_events(events)

    assert current_state["resource_reference"] == "Encounter/example-encounter-001"
    assert current_state["sequence_number"] == 2
    assert current_state["payload_completeness"] == "complete"
    assert current_state["resource"]["status"] == "finished"
    assert current_state["source_event_id"] == "encounter-message-002-complete"

    stale_decisions = [
        decision
        for decision in processing_decisions
        if decision["stale"] is True
    ]

    assert stale_decisions == [
        {
            "event_id": "encounter-message-001-partial",
            "resource_reference": "Encounter/example-encounter-001",
            "sequence_number": 1,
            "accepted_as_current": False,
            "stale": True,
            "reason": "older message rejected to protect current state",
        }
    ]

    older_partial_decision = stale_decisions[0]

    assert older_partial_decision["accepted_as_current"] is False
    assert older_partial_decision["stale"] is True