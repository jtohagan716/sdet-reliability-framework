# Patient Data Quality Review Queue

## Purpose

The Patient Data Quality Review Queue demonstrates how a technical data quality decision can be surfaced as a reviewable item.

This feature extends the FHIR stale-message protection work by showing that a stale-message decision does not have to remain hidden in logs or database tables.

Instead, the system can create a patient-centered review item that can be reviewed by a Data Quality Expert.

The goal is not to build an Electronic Health Record (EHR) or provider-facing clinical workflow.

The goal is to demonstrate healthcare-aware reliability validation, data-layer evidence, and reviewable operational decision support.

## Problem Modeled

Healthcare integration workflows can receive messages out of order.

A newer complete message may arrive first, and an older partial message may arrive later.

If handled incorrectly, the older message could silently overwrite the newer state.

Example risk:

```text
A complete Encounter is already recorded as finished.

An older partial Encounter message arrives later.

If the system accepts the stale message, the Encounter could be downgraded from finished to in-progress.