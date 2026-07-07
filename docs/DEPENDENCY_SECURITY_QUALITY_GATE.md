# Dependency Security Quality Gate

## Purpose

This document describes the dependency cleanup and dependency security quality gate for the SDET Reliability Framework.

The goal is to make dependency risk visible, repeatable, and reviewable as part of release validation.

This quality gate focuses on practical release hygiene:

- maintain an intentional dependency list
- remove unused packages and unused code
- validate Python package dependency health
- audit Python dependencies for known vulnerabilities
- separate runtime dependency checks from development/test-tooling checks
- avoid unsafe forced dependency changes
- document known transitive dependency findings
- preserve a repeatable operational validation path

## Operational Context

Dependency validation is part of release quality.

A project can have passing functional tests while still carrying unnecessary risk through unused dependencies, stale packages, vulnerable transitive packages, or unclear remediation decisions.

This quality gate is designed to show how a release process can classify and manage dependency findings instead of treating every audit result as either ignored or automatically force-fixed.

## Dependency Cleanup Completed

The prior Python dependency file contained packages that were not required by the active project.

Examples of removed packages included:

- `openai`
- `web3`
- Ethereum-related packages
- `aiohttp`
- `numpy`
- `pandas`
- `matplotlib`
- Python `playwright`

The Node Playwright tooling remains in `package.json`, where it belongs.

## Removed Unused Script

The following file was removed:

    scripts/performance_dashboard.py

That script was the only project-level source reference requiring `pandas` and `matplotlib`.

Because the script was not part of the active validation workflow, removing it allowed the Python dependency list to be simplified.

## Current Python Dependency Scope

The cleaned Python dependency list supports:

- FastAPI application runtime
- Uvicorn server execution
- Prometheus metrics
- Pydantic models
- Pytest validation
- Requests-based API validation
- PostgreSQL access through Psycopg
- YAML handling

## Dependency Security Validation Script

The dependency security quality gate is implemented in:

    scripts/validate_dependency_security.ps1

Run it with:

    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate_dependency_security.ps1

The script performs blocking checks and an advisory check.

## Blocking Checks

Blocking checks fail the script if they do not pass.

### Python Package Dependency Health

Command:

    python -m pip check

Purpose:

    Verifies that installed Python packages do not have broken dependency relationships.

Expected result:

    No broken requirements found.

### Python Vulnerability Audit

Command:

    python -m pip_audit -r .\requirements.txt

Purpose:

    Audits Python dependencies listed in requirements.txt for known vulnerabilities.

Expected result:

    No known vulnerabilities found.

### Node Production/Runtime Dependency Audit

Command:

    npm audit --omit=dev --audit-level=high

Purpose:

    Checks production/runtime Node dependencies while excluding development dependencies.

Expected result:

    No blocking production/runtime high-severity audit findings.

## Advisory Check

The full Node audit is intentionally advisory.

Command:

    npm audit --audit-level=high

Purpose:

    Reviews development and test tooling dependency findings.

Current classification:

    Known transitive development/test-tooling findings through the Newman/Postman dependency chain.

The script does not fail on this advisory check. Instead, it reports that advisory findings are present and instructs the user to review whether a safe remediation path exists.

## Current Newman/Postman Audit Finding

The current full Node audit reports vulnerabilities through the Newman/Postman dependency chain.

The affected dependency chain includes packages such as:

- `newman`
- `postman-runtime`
- `postman-sandbox`
- `postman-collection`
- `handlebars`
- `lodash`
- `node-forge`
- `flatted`
- `uuid`
- `qs`
- `underscore`

The audit output indicates that `npm audit fix --force` would install:

    newman@2.1.2

That is a breaking downgrade.

The forced fix is not applied.

## Release Decision

The current release decision is:

- Python dependency health passes.
- Python vulnerability audit passes after updating `pytest`.
- Production/runtime Node audit is treated as blocking.
- Full Node development/test-tooling audit is treated as advisory.
- Newman/Postman transitive findings are documented.
- `npm audit fix --force` is not used because it would apply a breaking Newman downgrade.

This is an intentional release-quality decision.

The project does not ignore the Node findings. It classifies them as:

    known transitive development/test-tooling risk with no safe automatic remediation currently applied

## Operational Lesson

A real dependency security review should not blindly apply automated fixes.

A responsible process should:

1. Identify the finding.
2. Determine whether it is direct or transitive.
3. Determine whether it affects runtime code or development/test tooling.
4. Determine whether a safe fix exists.
5. Apply safe direct fixes.
6. Avoid breaking forced fixes without impact analysis.
7. Document known findings.
8. Re-run validation after dependency changes.
9. Preserve a clear release decision trail.

## Current Scope

This project is a practice-scale reliability validation framework using synthetic data.

This quality gate demonstrates dependency hygiene, audit classification, and release decision discipline.

It is not a full enterprise software supply-chain security program.

## Future Improvements

Possible future improvements include:

- add the dependency security validation script to GitHub Actions
- evaluate alternatives to Newman if transitive findings remain unresolved
- add Dependabot configuration
- generate a Software Bill of Materials
- add documented review dates for accepted advisory findings
- separate runtime, CI, and local-development dependency policies
