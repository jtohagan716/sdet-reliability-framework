# PostgreSQL Audit Validation

## Purpose

This document explains how the SDET Reliability Framework validates PostgreSQL stored audit logic.

The goal is to prove that database-side changes to synthetic encounter records are captured in a repeatable, testable, and traceable way.

This supports reliability validation by showing that the system does not only return successful API responses, but also records database audit evidence.

---

## What This Validates

The audit validation flow proves that:

* An encounter insert creates an audit row.
* An encounter update creates an audit row.
* Old and new values are captured.
* Audit metadata such as `changed_by` and `change_source` is populated.
* The validation can run inside a transaction and roll back test data.
* The audit flow can be tested manually and through automated pytest integration testing.
* OpenTelemetry trace identifiers can be stored in audit rows for runtime correlation.

---

## Components Involved

| Component                                              | Purpose                                                                     |
| ------------------------------------------------------ | --------------------------------------------------------------------------- |
| `encounters`                                           | Source table where synthetic encounter records are inserted and updated     |
| `encounter_audit`                                      | Audit table where change history is recorded                                |
| `audit_encounter_changes()`                            | PostgreSQL trigger function that detects insert, update, and delete changes |
| `write_encounter_audit()`                              | PostgreSQL helper function that writes audit rows                           |
| `trg_audit_encounter_changes`                          | Trigger attached to the `encounters` table                                  |
| `scripts/validate_encounter_audit.sql`                 | Manual SQL validation script                                                |
| `tests/integration/test_encounter_audit_validation.py` | Automated pytest validation of the audit script                             |
| `/qa/audit-otel-validation`                            | Local QA endpoint that validates audit and OpenTelemetry trace correlation  |

---

## Audit Table Behavior

The `encounter_audit` table records old and new values for encounter changes.

Tracked fields include:

* `encounter_id`
* `patient_id`
* `provider_id`
* `facility_id`
* `operation_type`
* `old_encounter_date`
* `new_encounter_date`
* `old_encounter_type`
* `new_encounter_type`
* `old_status`
* `new_status`
* `changed_at`
* `changed_by`
* `change_source`
* `trace_id`
* `span_id`
* `request_id`
* `request_method`
* `request_path`
* `service_name`

The `trace_id` and `span_id` fields allow audit rows to be correlated with OpenTelemetry traces.

---

## Manual SQL Validation

The manual validation script is located at:

```text
scripts/validate_encounter_audit.sql
```

Run it with:

```powershell
Get-Content scripts\validate_encounter_audit.sql | docker compose exec -T postgres psql -U sdet_user -d sdet_reliability -v ON_ERROR_STOP=1
```

Expected result:

```text
operation_type | old_status | new_status
---------------+------------+------------
INSERT         |            | scheduled
UPDATE         | scheduled  | completed
```

The script uses a transaction and ends with:

```sql
ROLLBACK;
```

This allows the validation to prove audit behavior without permanently inserting synthetic validation records.

---

## Screenshot: Manual Audit Validation Result

Insert screenshot here after capturing the PostgreSQL audit query result:

```markdown
![Manual audit validation result](images/postgres-audit-query-by-trace-id.png)
```

Screenshot file to capture:

```text
docs/images/postgres-audit-query-by-trace-id.png
```

The screenshot should show:

* Two audit rows.
* One `INSERT` row.
* One `UPDATE` row.
* `old_status` and `new_status`.
* Matching `trace_id` values if using the OpenTelemetry validation endpoint.
* `request_path` showing `/qa/audit-otel-validation`.

---

## Automated Audit Integration Test

The automated audit integration test is located at:

```text
tests/integration/test_encounter_audit_validation.py
```

Run it with:

```powershell
python -m pytest tests/integration/test_encounter_audit_validation.py -v
```

This test runs the SQL validation script against the Docker Compose PostgreSQL service.

The test verifies:

* The SQL script completes successfully.
* The output contains an `INSERT` audit row.
* The output contains an `UPDATE` audit row.
* The expected old and new status values are present.
* Audit metadata values are present.
* The validation script rolls back after execution.

Because this is a Docker-backed integration test, it skips cleanly if the PostgreSQL Docker Compose service is not available.

---

## Screenshot: Automated Audit Test Pass

Insert screenshot here after capturing the pytest result:

```markdown
![Pytest audit integration pass](images/pytest-audit-integration-pass.png)
```

Screenshot file to capture:

```text
docs/images/pytest-audit-integration-pass.png
```

The screenshot should show:

```text
tests/integration/test_encounter_audit_validation.py
1 passed
```

---

## API-Based Audit and Trace Validation

The project also includes a local QA endpoint:

```text
POST /qa/audit-otel-validation
```

Run it with:

```powershell
$response = Invoke-RestMethod -Method Post http://localhost:8000/qa/audit-otel-validation
$response | ConvertTo-Json -Depth 6
```

Expected result:

```text
validation: passed
audit_row_count: 2
trace_id: populated
span_id: populated
audit_rows: INSERT and UPDATE
```

This endpoint performs the following actions:

1. Captures the active OpenTelemetry trace context.
2. Stores trace and request metadata into PostgreSQL transaction-local settings.
3. Inserts a synthetic encounter.
4. Updates the encounter status from `scheduled` to `completed`.
5. Allows the PostgreSQL trigger to write audit rows.
6. Queries the audit rows and returns them in the API response.

---

## Screenshot: API Audit/OpenTelemetry Validation Response

Insert screenshot here after capturing the endpoint response:

```markdown
![Audit OpenTelemetry endpoint response](images/audit-otel-endpoint-response.png)
```

Screenshot file to capture:

```text
docs/images/audit-otel-endpoint-response.png
```

The screenshot should show:

* `validation: passed`
* `trace_id`
* `span_id`
* `audit_row_count: 2`
* One `INSERT` audit row
* One `UPDATE` audit row

---

## Query Audit Rows by Trace ID

After running the API validation endpoint, store the returned trace ID:

```powershell
$traceId = $response.trace_id
```

Then query PostgreSQL:

```powershell
docker compose exec postgres psql -U sdet_user -d sdet_reliability -c "SELECT audit_id, encounter_id, operation_type, old_status, new_status, trace_id, span_id, request_method, request_path, service_name FROM encounter_audit WHERE trace_id = '$traceId' ORDER BY audit_id;"
```

Expected result:

```text
INSERT |           | scheduled  | same trace_id
UPDATE | scheduled | completed  | same trace_id
```

This proves that the runtime request trace and the database audit trail are correlated.

---

## Screenshot: PostgreSQL Audit Rows by Trace ID

Insert screenshot here after querying audit rows by trace ID:

```markdown
![PostgreSQL audit query by trace ID](images/postgres-audit-query-by-trace-id.png)
```

Screenshot file to capture:

```text
docs/images/postgres-audit-query-by-trace-id.png
```

The screenshot should show:

* Two audit rows.
* The same `trace_id` on both rows.
* `INSERT` and `UPDATE` operations.
* `request_method` showing `POST`.
* `request_path` showing `/qa/audit-otel-validation`.
* `service_name` showing `sdet-reliability-api`.

---

## Reliability Value

This audit validation adds value because it verifies behavior below the API response layer.

A simple API test can prove that an endpoint returned `200 OK`.

This audit validation proves more:

```text
API request succeeded
  -> database insert occurred
  -> database update occurred
  -> trigger executed
  -> audit rows were written
  -> old and new values were captured
  -> trace_id was stored for correlation
```

That is stronger evidence of system reliability.

---

## Safety and Data Notes

This project uses synthetic data only.

Do not include real patient data, production credentials, protected health information, or sensitive identifiers in screenshots, traces, logs, or audit examples.

The local PostgreSQL credentials are for development only.
