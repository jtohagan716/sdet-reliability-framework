# FHIR Stale Message PostgreSQL Evidence

## Purpose

This document explains the PostgreSQL-backed evidence layer for the FHIR stale-message protection scenario in the SDET Reliability Framework.

The goal is to prove that the framework can preserve message history, protect current Encounter state, and archive stale-message decisions in a repeatable database-backed validation flow.

This is a synthetic FHIR-style healthcare interoperability reliability scenario.

It is not a full FHIR server implementation.

It is not a FHIR conformance test suite.

It does not use real patient data.

---

## Reliability Problem

Healthcare integration systems may receive messages out of order.

A newer complete message may arrive before an older partial message.

Example:

```text
Message 2 arrives first:
  resource: Encounter/example-encounter-001
  sequence_number: 2
  status: finished
  completeness: complete

Message 1 arrives second:
  resource: Encounter/example-encounter-001
  sequence_number: 1
  status: in-progress
  completeness: partial
```

The older partial message must not overwrite the newer complete state.

Expected behavior:

```text
The newer complete message is accepted as current state.
The older partial message is preserved as message history.
The older partial message is archived as stale.
The current Encounter state remains finished and complete.
```

---

## Design Pattern

This validation uses three PostgreSQL tables:

```text
fhir_message_events
fhir_current_encounter_state
fhir_stale_message_decisions
```

The design separates message history, current state, and stale-message decisions.

```text
append-only message history
+ current-state projection
+ stale-message decision archive
```

This is intentional.

A reliable healthcare integration flow should not silently overwrite current state with an older message.

It should preserve what arrived, record what was accepted, and explain what was rejected.

---

## Table 1: fhir_message_events

The `fhir_message_events` table stores every synthetic healthcare message event that arrives.

This table acts as append-only message history.

It records both accepted and stale messages.

Important fields include:

```text
event_id
source_system
interface_name
message_type
resource_reference
sequence_number
arrival_order
payload_completeness
resource_status
processing_status
received_at
payload_hash
raw_payload
details
```

In this scenario, the table records:

```text
encounter-message-002-complete
  accepted
  sequence_number = 2
  status = finished
  completeness = complete

encounter-message-001-partial
  stale
  sequence_number = 1
  status = in-progress
  completeness = partial
```

The stale message is not deleted.

It remains available for review, reconciliation, troubleshooting, and possible replay analysis.

---

## Table 2: fhir_current_encounter_state

The `fhir_current_encounter_state` table stores the current accepted state for the Encounter.

This is the operational current-state projection.

Important fields include:

```text
resource_reference
current_sequence_number
current_resource_status
current_payload_completeness
source_event_id
source_message_event_id
current_payload_hash
current_payload
details
```

In this scenario, the protected current state is:

```text
resource_reference:
  Encounter/example-encounter-001

current_sequence_number:
  2

current_resource_status:
  finished

current_payload_completeness:
  complete

source_event_id:
  encounter-message-002-complete
```

The older partial message does not update this table.

---

## Table 3: fhir_stale_message_decisions

The `fhir_stale_message_decisions` table stores the reason a stale message was archived and rejected.

This table acts as an auditable decision record.

Important fields include:

```text
stale_event_id
stale_message_event_id
protected_resource_reference
stale_sequence_number
current_sequence_number
stale_resource_status
current_resource_status
stale_payload_completeness
current_payload_completeness
decision_status
decision_reason
risk_prevented
details
```

In this scenario, the stale decision records:

```text
stale_event_id:
  encounter-message-001-partial

decision_status:
  stale_archived

decision_reason:
  Older partial Encounter message archived and rejected to protect newer complete Encounter state

risk_prevented:
  Prevented downgrade from finished complete state to in-progress partial state
```

---

## Why This Design Is Safer

This design is safer than a single mutable table because it protects against silent data corruption.

A weaker design might allow this:

```text
late older message arrives
current state is overwritten
finished becomes in-progress
no clear evidence explains why
```

This framework validates a safer pattern:

```text
late older message arrives
message is preserved
current state is protected
stale decision is archived
reason is queryable
validation remains repeatable
```

The result is better evidence for:

```text
out-of-order message review
interface troubleshooting
database validation
audit review
production support analysis
defect reproduction
manual reconciliation
safe replay planning
```

---

## Files Added

Schema:

```text
db/sql/010_fhir_stale_message_evidence.sql
```

Validation script:

```text
scripts/validate_fhir_stale_message_evidence.sql
```

Automated pytest integration test:

```text
tests/integration/test_fhir_stale_message_postgres_evidence.py
```

---

## Running the SQL Validation Script

Run:

```powershell
Get-Content scripts\validate_fhir_stale_message_evidence.sql | docker compose exec -T postgres psql -x -U sdet_user -d sdet_reliability
```

Expected evidence includes:

```text
FHIR stale-message event history:
Protected current Encounter state:
Archived stale-message decision:
Expected protected state assertion:
Expected stale archive assertion:
Expected append-only history assertion:
```

Expected assertions:

```text
protected_state_assertion     | passed
stale_archive_assertion       | passed
append_only_history_assertion | passed
ROLLBACK
```

The `ROLLBACK` is intentional.

It keeps the validation repeatable and deterministic.

---

## Running the Automated Test

Run:

```powershell
python -m pytest tests/integration/test_fhir_stale_message_postgres_evidence.py -v
```

Expected result:

```text
1 passed
```

Run the broader FHIR validation group:

```powershell
python -m pytest tests/integration/test_fhir_resource_validation.py tests/integration/test_fhir_postgres_validation_evidence.py tests/integration/test_fhir_stale_message_protection.py tests/integration/test_fhir_stale_message_postgres_evidence.py -v
```

---

## Validation Evidence

The SQL validation proves three things.

### 1. Append-only message history exists

Both messages are preserved:

```text
encounter-message-002-complete
encounter-message-001-partial
```

The stale message is not deleted.

It remains available for review.

### 2. Current Encounter state is protected

The current state remains:

```text
sequence_number:
  2

status:
  finished

completeness:
  complete

source_event_id:
  encounter-message-002-complete
```

The older partial message does not overwrite the current state.

### 3. Stale message decision is archived

The older message is recorded as:

```text
decision_status:
  stale_archived

risk_prevented:
  Prevented downgrade from finished complete state to in-progress partial state
```

This provides evidence explaining why the message was not accepted as current state.

---

## Relationship to the File-Based Stale Message Test

The file-based stale-message test proves the decision logic in Python.

File:

```text
tests/integration/test_fhir_stale_message_protection.py
```

The PostgreSQL evidence test proves that the decision can also be represented as database evidence.

File:

```text
tests/integration/test_fhir_stale_message_postgres_evidence.py
```

Together, they show:

```text
behavioral validation
+ database evidence validation
```

---

## Relationship to FHIR

This module uses synthetic FHIR-style resources and message events.

It is intended to model healthcare interoperability reliability risks.

It does not claim to implement full FHIR server behavior.

It does not claim FHIR conformance.

The FHIR-style concepts used here include:

```text
Patient
Encounter
resource reference
message/event history
current resource state
stale update protection
audit-style decision evidence
```

The goal is reliability validation, not production FHIR architecture.

---

## Relationship to Production Support

This scenario models a practical production support problem.

A support engineer, tester, or integration analyst may need to answer:

```text
What messages arrived?
In what order did they arrive?
Which message was accepted?
Which message was rejected?
Why was it rejected?
What current state was protected?
Can we review the stale message later?
Could this be replayed after a correction?
```

This design makes those questions answerable through database evidence.

---

## Current Limitations

Current limitations:

```text
synthetic FHIR-style data only
no real patient data
no production FHIR server
no live interface engine
no message broker
no external source system
no automated replay processor
no same-sequence conflict scenario yet
no duplicate-message scenario yet
no sequence-gap scenario yet
```

These are acceptable limitations for this milestone.

The purpose of this phase is to prove the database evidence pattern clearly and repeatably.

---

## Future Enhancements

Possible future enhancements include:

```text
duplicate message detection
same-sequence conflict detection
sequence-gap detection
newer-but-incomplete message rejection
source-system authority rules
manual reconciliation workflow evidence
message replay after mapping correction
OpenTelemetry trace correlation for stale-message processing
API endpoint for synthetic message ingestion
local HAPI FHIR server integration
```

The next strongest enhancement is duplicate-message detection because it connects directly to the existing idempotency and retry-safety work.

---

## Summary

The PostgreSQL stale-message evidence layer proves that the framework can preserve healthcare message history, protect current Encounter state, and archive stale-message decisions.

Current behavior:

```text
newer complete Encounter message:
  accepted as current

older partial Encounter message:
  preserved in message history
  archived as stale
  rejected from current-state update

current Encounter state:
  remains sequence 2
  remains finished
  remains complete
```

This adds database-backed reliability evidence to the synthetic FHIR-style healthcare interoperability module.
