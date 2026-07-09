# FHIR Stale Message Protection

## Purpose

This document explains the stale-message protection scenario in the SDET Reliability Framework.

The goal is to validate that an older partial healthcare message does not overwrite a newer complete encounter state.

This is a healthcare interoperability reliability scenario using synthetic FHIR-style message events.

---

## Why This Matters

Healthcare systems often receive messages from multiple systems, queues, interfaces, or retry paths.

Messages may arrive:

```text
out of order
late
partially populated
duplicated
retried
after a newer state has already been accepted
```

A common reliability risk is stale overwrite.

Example:

```text
Message 2 arrives first:
  Encounter status = finished
  sequence_number = 2
  completeness = complete

Message 1 arrives second:
  Encounter status = in-progress
  sequence_number = 1
  completeness = partial
```

The system must not allow the older partial message to overwrite the newer complete state.

Expected result:

```text
The current Encounter state remains finished.
The current Encounter state remains complete.
The older partial message is marked stale.
The older partial message is not accepted as current state.
```

---

## Scenario Summary

This project models an out-of-order Encounter update scenario.

The synthetic message events are stored in:

```text
test_data/fhir/message_events/
```

Files:

```text
test_data/fhir/message_events/encounter-message-sequence-002-complete.json
test_data/fhir/message_events/encounter-message-sequence-001-partial.json
```

The first message to arrive is the newer complete state.

The second message to arrive is the older partial state.

This is intentional.

---

## Message 2: Newer Complete Encounter State

Fixture:

```text
test_data/fhir/message_events/encounter-message-sequence-002-complete.json
```

Important fields:

```text
event_id:
  encounter-message-002-complete

resource_reference:
  Encounter/example-encounter-001

sequence_number:
  2

arrival_order:
  1

payload_completeness:
  complete

Encounter.status:
  finished
```

Expected processing result:

```text
accepted_as_current:
  true

stale:
  false

reason:
  newer complete encounter state
```

This message represents the most complete and most current Encounter state.

---

## Message 1: Older Partial Encounter State

Fixture:

```text
test_data/fhir/message_events/encounter-message-sequence-001-partial.json
```

Important fields:

```text
event_id:
  encounter-message-001-partial

resource_reference:
  Encounter/example-encounter-001

sequence_number:
  1

arrival_order:
  2

payload_completeness:
  partial

Encounter.status:
  in-progress
```

Expected processing result:

```text
accepted_as_current:
  false

stale:
  true

reason:
  older partial message arrived after newer complete state
```

This message is older and less complete.

It should be detected as stale.

---

## Processing Rule

The core stale-message rule is:

```text
For the same resource, a message with an older sequence_number must not overwrite a current state that came from a newer sequence_number.
```

In this scenario:

```text
Current state:
  sequence_number = 2
  status = finished
  completeness = complete

Incoming message:
  sequence_number = 1
  status = in-progress
  completeness = partial

Decision:
  reject as stale
```

The current state remains protected.

---

## Automated Test

The stale-message protection test is implemented in:

```text
tests/integration/test_fhir_stale_message_protection.py
```

Run the test with:

```powershell
python -m pytest tests/integration/test_fhir_stale_message_protection.py -v
```

Expected result:

```text
1 passed
```

The test validates:

```text
the newer complete message is accepted as current state
the older partial message is marked stale
the current Encounter state remains sequence 2
the current Encounter status remains finished
the current payload completeness remains complete
the older partial message does not overwrite current state
```

---

## Test Flow

The test loads two synthetic message events:

```text
encounter-message-sequence-002-complete.json
encounter-message-sequence-001-partial.json
```

Then it processes them in arrival order:

```text
Arrival 1:
  sequence 2, complete, finished

Arrival 2:
  sequence 1, partial, in-progress
```

The processing function returns:

```text
current_state
processing_decisions
```

Expected final current state:

```text
resource_reference:
  Encounter/example-encounter-001

sequence_number:
  2

payload_completeness:
  complete

Encounter.status:
  finished

source_event_id:
  encounter-message-002-complete
```

Expected stale decision:

```text
event_id:
  encounter-message-001-partial

resource_reference:
  Encounter/example-encounter-001

sequence_number:
  1

accepted_as_current:
  false

stale:
  true

reason:
  older message rejected to protect current state
```

---

## Why This Is a Reliability Test

This is not just a JSON fixture test.

It validates state protection.

A reliable healthcare integration flow must protect current state from:

```text
late-arriving messages
out-of-order messages
partial updates
older interface events
unsafe overwrites
```

The test proves that the framework can model and validate that behavior.

---

## Relationship to FHIR Validation

The project already includes synthetic FHIR-style resources:

```text
Patient
Encounter
Observation
DiagnosticReport
```

Those resources validate reference integrity.

This stale-message protection scenario adds a different kind of healthcare interoperability validation:

```text
resource relationship validation:
  Do references point to valid resources?

stale-message validation:
  Does the system protect newer complete state from older partial updates?
```

Both are important.

Reference validation protects relationships.

Stale-message validation protects state.

---

## Relationship to Idempotency

This stale-message scenario is related to idempotency and retry safety, but it is not the same thing.

Idempotency answers:

```text
Did the same request get retried?
Should the original response be replayed?
```

Stale-message protection answers:

```text
Is this message older than the current accepted state?
Should this older message be rejected so it does not overwrite newer data?
```

Both patterns protect systems from unreliable real-world behavior.

---

## Healthcare Example

A realistic healthcare integration risk:

```text
An encounter is completed in a source system.

A finished Encounter message is sent and accepted.

Later, an older in-progress message arrives from a delayed queue, retry path, or secondary interface.

If accepted incorrectly, the system may downgrade the encounter from finished to in-progress.
```

That would be unsafe.

Expected behavior:

```text
finished state remains current
older in-progress update is marked stale
audit/evidence records should show why the update was rejected
```

This project models the first part of that behavior in pytest.

A future phase can persist stale-message decisions to PostgreSQL.

---

## Current Implementation

Current implementation is file-based and test-driven.

Current files:

```text
test_data/fhir/message_events/encounter-message-sequence-002-complete.json
test_data/fhir/message_events/encounter-message-sequence-001-partial.json
tests/integration/test_fhir_stale_message_protection.py
```

The current test does not require a live FHIR server.

The current test does not require PostgreSQL.

That is intentional for this phase.

The goal is to first prove the stale-message rule in a small, deterministic test.

---

## Current Limitations

Current limitations:

```text
file-based message event fixtures only
no persistent stale-message evidence table yet
no API endpoint for message processing yet
no local FHIR server yet
no real patient data
no full FHIR conformance validation
no interface engine simulation
```

These are acceptable limitations for the first stale-message milestone.

The current goal is to prove the behavior clearly.

---

## Future Enhancements

Possible next steps:

```text
add PostgreSQL stale-message evidence tables
record accepted and stale message decisions
add SQL validation script for stale-message processing
add pytest test around PostgreSQL stale-message evidence
add OpenTelemetry trace correlation for stale-message processing
add API endpoint for synthetic message ingestion
add multiple Encounter message sequences
add duplicate message handling
add same-sequence conflict handling
add HAPI FHIR server integration later
```

The strongest next enhancement is PostgreSQL evidence for stale-message decisions.

Possible future tables:

```text
fhir_message_events
fhir_current_encounter_state
fhir_stale_message_decisions
```

These would allow the project to prove:

```text
which message arrived
which message was accepted
which message was rejected as stale
what current state remained protected
why the stale decision was made
```

---

## Reliability Value

This scenario demonstrates reliability-focused healthcare testing skills:

```text
out-of-order message handling
state protection
stale update detection
synthetic healthcare event modeling
deterministic pytest validation
negative-path thinking
interoperability risk modeling
```

This is relevant to:

```text
Healthcare QA
FHIR testing
HL7/FHIR integration testing
SDET work
API/database validation
application support engineering
production support
reliability engineering
```

---

## Summary

The stale-message protection scenario proves that the framework can protect a newer complete Encounter state from an older partial update.

Current behavior:

```text
newer complete Encounter message:
  accepted as current

older partial Encounter message:
  marked stale

current state:
  remains sequence 2
  remains complete
  remains finished
```

This adds a realistic healthcare interoperability reliability scenario to the SDET Reliability Framework.
