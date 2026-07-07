# Dependency Security Quality Gate

## Purpose

This document describes the dependency cleanup and security quality gate work added for the SDET Reliability Framework.

The goal is to make project dependencies intentional, auditable, and easier to maintain.

This milestone focuses on practical release hygiene:

- remove unused dependencies
- remove unused code that requires unnecessary packages
- validate Python dependency health
- audit Python dependencies for known vulnerabilities
- classify Node audit findings
- avoid unsafe automatic dependency changes
- document known risks and release decisions

## Why This Matters

Dependency management is part of release quality.

A project can have passing tests but still carry unnecessary risk if it includes unused packages, stale dependencies, vulnerable transitive packages, or unclear remediation decisions.

This quality gate is intended to make dependency risk visible and manageable.

## Dependency Cleanup

The prior `requirements.txt` appeared to include packages from a broad environment freeze rather than only project-required packages.

Examples of removed packages included unrelated or unused dependencies such as:

- `openai`
- `web3`
- `eth-account`
- `eth-utils`
- `eth-keys`
- `eth-abi`
- `py_clob_client`
- `py_order_utils`
- `aiohttp`
- `numpy`
- `pandas`
- `matplotlib`
- Python `playwright`

The Node Playwright tooling remains in `package.json`, where it belongs.

## Removed Unused Script

The file below was removed:

    scripts/performance_dashboard.py

That script was the only project-level source reference requiring `pandas` and `matplotlib`.

Because it was not referenced by the active project workflow, documentation, or validation stack, removing it allowed the Python dependency list to be simplified.

## Current Python Dependency List

The cleaned Python dependency list is intentionally small:

    fastapi
    uvicorn
    prometheus_client
    pydantic
    pytest
    requests
    PyYAML
    psycopg
    psycopg-binary

These dependencies support the current FastAPI service, PostgreSQL access, Prometheus metrics, Pytest validation, YAML handling, and REST/API test support.

## Python Dependency Validation

The Python dependency validation includes:

    python -m pip check

This verifies that installed Python packages do not have broken dependency relationships.

Current result:

    No broken requirements found.

## Python Vulnerability Audit

The Python dependency vulnerability audit uses:

    python -m pip_audit -r .\requirements.txt

An initial audit found one vulnerability:

| Package | Version | Finding | Fix Version |
|---|---:|---|---:|
| pytest | 9.0.2 | CVE-2025-71176 | 9.0.3 |

The project updated `pytest` to `9.0.3`.

Current Python audit result:

    No known vulnerabilities found.

## Python Regression Validation

After the dependency cleanup and `pytest` update, the full Python regression suite was run:

    python -m pytest

Current result:

    206 passed, 1 warning

The warning is a Starlette/FastAPI test client deprecation warning. It does not fail the current validation run.

A Windows temp-directory cleanup message also appeared after the run. The test session itself completed successfully.

## Node Dependency Audit Classification

The project also uses Node-based development and test tooling:

- Newman
- Playwright
- axe-core for Playwright

The full Node audit command is:

    npm audit --audit-level=high

The current full Node audit reports vulnerabilities through the Newman/Postman dependency chain.

The affected chain includes packages such as:

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

The audit output indicates that `npm audit fix --force` would install `newman@2.1.2`, which is a breaking change.

That forced fix is not applied.

## Release Decision

The Node audit findings are classified as known transitive development/test-tooling findings.

They are documented and monitored, but not automatically force-fixed because the proposed remediation would downgrade Newman in a breaking way.

This is a deliberate release-quality decision.

The project does not ignore the findings. It classifies them as:

    known transitive dev-tooling risk with no safe automatic fix currently applied

## Blocking vs Advisory Checks

The dependency quality gate separates blocking checks from advisory checks.

### Blocking Checks

These should pass for the release:

    python -m pip check
    python -m pip_audit -r .\requirements.txt
    python -m pytest

### Advisory Checks

These are reviewed and documented:

    npm audit --audit-level=high

The full Node audit currently reports Newman/Postman transitive dependency findings. These findings require monitoring and future remediation when a safe dependency path is available.

## Operational Lesson

A real release process should not blindly apply automated dependency fixes.

The correct process is:

1. Run dependency health checks.
2. Run vulnerability audits.
3. Fix safe direct dependency findings.
4. Identify whether findings are direct or transitive.
5. Identify whether affected packages are runtime dependencies or development/test tooling.
6. Avoid breaking forced fixes without impact analysis.
7. Document known risks.
8. Make a release decision based on severity, exposure, usage, and remediation safety.

## Current Scope

This project is a local and Continuous Integration validation framework using synthetic data.

The dependency security quality gate demonstrates practical release hygiene. It is not a full enterprise software supply-chain security program.

## Future Improvements

Possible future improvements include:

- add a dedicated dependency security validation script
- add `pip-audit` to GitHub Actions
- add Node production/runtime audit checks
- evaluate alternatives to Newman if transitive audit findings remain unresolved
- add Software Bill of Materials generation
- add Dependabot configuration
- document accepted-risk review dates
