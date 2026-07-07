# v1.9.0 - Dependency Cleanup and Security Quality Gate

## Summary

This milestone adds dependency cleanup and dependency security quality gate work to the SDET Reliability Framework.

The purpose is to make the project dependency set cleaner, reduce unnecessary package exposure, validate Python dependency health, remediate a Python audit finding, and classify known Node development/test-tooling audit findings.

## Work Completed

### 1. Reviewed Existing Python Dependencies

The existing `requirements.txt` contained many packages that did not appear to be required by the active project.

Examples included:

- `openai`
- `web3`
- Ethereum-related packages
- `aiohttp`
- `numpy`
- `pandas`
- `matplotlib`
- Python `playwright`

This indicated that the file had likely been generated from a broad environment freeze rather than an intentional project dependency list.

### 2. Scanned Project Imports

Project source files were scanned to identify actual top-level Python imports.

The scan excluded:

- `.venv`
- `venv`
- `node_modules`
- `.git`
- `__pycache__`

This avoided treating installed third-party package code as project source code.

### 3. Removed Unused Dashboard Script

The following file was removed:

    scripts/performance_dashboard.py

That script referenced `pandas` and `matplotlib`, but it was not part of the active validation workflow.

Removing the unused script allowed the Python dependency list to be simplified.

### 4. Cleaned Python Requirements

The Python dependency list was reduced to intentional project dependencies.

The cleaned dependency set supports:

- FastAPI runtime
- Uvicorn server execution
- Prometheus metrics
- Pydantic models
- Pytest validation
- Requests-based API validation
- PostgreSQL access through Psycopg
- YAML handling

### 5. Fixed Python Audit Finding

The Python audit initially found one vulnerability:

| Package | Version | Finding | Fix Version |
|---|---:|---|---:|
| pytest | 9.0.2 | CVE-2025-71176 | 9.0.3 |

Action taken:

    pytest was updated from 9.0.2 to 9.0.3.

Current Python audit result:

    No known vulnerabilities found.

### 6. Validated Python Dependency Health

Command run:

    python -m pip check

Result:

    No broken requirements found.

### 7. Ran Python Regression Suite

Command run:

    python -m pytest

Result:

    206 passed, 1 warning

The warning was a Starlette/FastAPI test client deprecation warning.

A Windows temp-directory cleanup message appeared after the test run, but the test session itself completed successfully.

### 8. Reviewed Node Audit Findings

Command reviewed:

    npm audit --audit-level=high

The full Node audit reported vulnerabilities through the Newman/Postman dependency chain.

The affected packages are transitive development/test-tooling dependencies used through Newman and related Postman packages.

The audit output indicated that the available forced fix would install:

    newman@2.1.2

That would be a breaking downgrade, so the forced fix was not applied.

### 9. Added Repeatable Dependency Security Script

The following script was added:

    scripts/validate_dependency_security.ps1

The script separates blocking checks from advisory checks.

Blocking checks:

    python -m pip check
    python -m pip_audit -r .\requirements.txt
    npm audit --omit=dev --audit-level=high

Advisory check:

    npm audit --audit-level=high

The full Node audit remains advisory because the current findings are known transitive development/test-tooling findings and the proposed forced remediation is a breaking Newman downgrade.

## Script Validation Result

The dependency security script completed successfully.

The script reported:

    Blocking dependency security checks completed successfully.

The script also reported advisory findings for the full Node development/test-tooling audit.

This is expected under the current classification.

## Release Decision

The release decision for this milestone is:

- Python dependency health passed.
- Python vulnerability audit passed after updating `pytest`.
- Python regression suite passed.
- Production/runtime Node dependency audit is treated as blocking.
- Full Node development/test-tooling audit is reviewed as advisory.
- Newman/Postman transitive findings are documented.
- `npm audit fix --force` is not applied because it would downgrade Newman in a breaking way.

## Validation Evidence

| Validation Area | Result |
|---|---|
| Python dependency health | Passed |
| Python vulnerability audit | Passed after pytest update |
| Python regression suite | 206 passed, 1 warning |
| Node production/runtime audit | Blocking check in dependency security script |
| Full Node dev-tooling audit | Advisory findings present |
| Forced Node audit fix | Not applied because it would introduce a breaking Newman downgrade |
| Dependency security script | Completed successfully |

## Operational Interpretation

This milestone demonstrates practical dependency security review.

The work did not treat audit output as a simple checkbox.

Instead, the process classified findings based on:

- direct vs transitive dependency
- runtime vs development/test tooling
- safe fix vs breaking forced fix
- current project exposure
- validation impact
- documentation requirements

## Professional Release Practice Demonstrated

A real operation would expect this kind of reasoning:

1. Identify the finding.
2. Determine whether it affects runtime or tooling.
3. Determine whether the dependency is direct or transitive.
4. Determine whether a safe fix exists.
5. Apply safe direct fixes.
6. Avoid breaking forced fixes without impact analysis.
7. Document known risk.
8. Re-run validation after dependency changes.
9. Preserve a clear audit trail.

## Data Safety

All project data remains synthetic.

No real patient data, protected health information, personally identifiable information, credentials, secrets, or production data are used.

## Current Scope

This milestone improves dependency hygiene and dependency-audit awareness for a practice-scale reliability validation framework.

It is not a full enterprise security program.

## Future Improvements

Potential next steps include:

- add the dependency security validation script to GitHub Actions
- evaluate alternatives to Newman/Postman if safe remediation remains unavailable
- add Dependabot configuration
- generate a Software Bill of Materials
- add accepted-risk review dates
- separate runtime, CI, and local-development dependency policies
