\# FHIR Reference Validation



\## Purpose



This document explains how the SDET Reliability Framework validates synthetic FHIR-style resource references.



The goal is to prove that healthcare resources are not only valid JSON files, but also form a consistent local interoperability chain.



This is an early healthcare interoperability testing scenario inside the larger reliability framework.



\---



\## Validation Scope



The current validation focuses on four synthetic FHIR-style resources:



```text

Patient

Encounter

Observation

DiagnosticReport

```



These resources form this expected relationship chain:



```text

Patient/example-patient-001

&#x20; -> Encounter/example-encounter-001

&#x20;   -> Observation/example-observation-001

&#x20;     -> DiagnosticReport/example-diagnosticreport-001

```



The validation is intentionally file-based at this stage.



The project is not yet using a local FHIR server.



\---



\## Synthetic Test Fixtures



Valid fixtures:



```text

test\_data/fhir/patient-example.json

test\_data/fhir/encounter-example.json

test\_data/fhir/observation-example.json

test\_data/fhir/diagnosticreport-example.json

```



Negative fixture:



```text

test\_data/fhir/invalid/diagnosticreport-broken-observation-reference.json

```



The negative fixture intentionally references an Observation that does not exist:



```text

Observation/example-observation-missing-001

```



This allows the test framework to prove that broken healthcare references are detected.



\---



\## Positive Validation



The positive validation proves that each resource declares the expected `resourceType`.



Expected values:



```text

Patient.resourceType = Patient

Encounter.resourceType = Encounter

Observation.resourceType = Observation

DiagnosticReport.resourceType = DiagnosticReport

```



The test also proves that the resources form the expected reference chain.



Expected references:



```text

Encounter.subject.reference

&#x20; -> Patient/example-patient-001



Observation.subject.reference

&#x20; -> Patient/example-patient-001



Observation.encounter.reference

&#x20; -> Encounter/example-encounter-001



DiagnosticReport.subject.reference

&#x20; -> Patient/example-patient-001



DiagnosticReport.encounter.reference

&#x20; -> Encounter/example-encounter-001



DiagnosticReport.result.reference

&#x20; -> Observation/example-observation-001

```



\---



\## Negative Validation



The negative validation proves that an unresolved reference is detected.



The intentionally broken DiagnosticReport points to:



```text

Observation/example-observation-missing-001

```



That Observation is not included in the supplied synthetic resource set.



Expected validation finding:



```text

source:

&#x20; DiagnosticReport/example-diagnosticreport-broken-001



missing\_reference:

&#x20; Observation/example-observation-missing-001

```



This proves the test framework can identify an invalid healthcare resource relationship.



\---



\## Automated Test



The validation is implemented in:



```text

tests/integration/test\_fhir\_resource\_validation.py

```



The test currently validates:



```text

resource type correctness

expected happy-path reference chain

absence of unresolved references in the valid resource set

detection of a broken DiagnosticReport.result reference

```



Expected local result:



```text

4 passed

```



\---



\## Why This Matters



FHIR-style resources often reference other resources.



A healthcare system may receive or process resources that point to:



```text

missing patients

missing encounters

missing observations

missing diagnostic results

incorrect resource IDs

out-of-order messages

stale or partial updates

```



A broken reference can create bad downstream behavior.



Examples:



```text

A DiagnosticReport points to an Observation that was never loaded.



An Observation points to an Encounter that does not exist.



An Encounter points to a Patient that cannot be resolved.

```



This project starts by validating those relationships in synthetic test data before adding a local FHIR server or database projection layer.



\---



\## Reliability Value



This is not just a JSON syntax check.



The test validates relationship integrity across multiple healthcare resources.



That demonstrates transferable testing skills:



```text

healthcare data validation

API fixture design

reference integrity testing

negative test design

synthetic data strategy

repeatable pytest automation

interoperability-focused quality checks

```



This fits the broader reliability theme of the project:



```text

A system should not only accept good data.

It should also detect and reject unsafe or inconsistent data.

```



\---



\## Current Limitations



This validation is intentionally narrow.



Current limitations:



```text

not full FHIR conformance validation

not terminology validation

not profile validation

not server-side FHIR API validation

not SMART-on-FHIR authentication

not real patient data

```



Those are future possibilities.



The current goal is to establish a clean, understandable healthcare interoperability validation foundation.



\---



\## Future Enhancements



Possible next steps:



```text

add a broken Encounter -> Patient reference fixture

add a broken Observation -> Encounter reference fixture

add validation result reporting

persist validation findings to PostgreSQL

add SQL evidence for reference checks

add stale-message protection scenario

add local HAPI FHIR server

add Synthea-generated synthetic FHIR data

```



The next strongest technical enhancement is to persist validation results into PostgreSQL so reference validation has database-backed evidence.



\---



\## Summary



This module proves that the framework can validate healthcare resource relationships using synthetic FHIR-style data.



Current behavior:



```text

valid resource chain:

&#x20; passes



broken DiagnosticReport -> Observation reference:

&#x20; detected



real patient data:

&#x20; not used

```



This is a clean first step toward healthcare interoperability testing inside the SDET Reliability Framework.



