# Pull Request Validation Checklist

## Summary

Describe the purpose of this change.

## Type of Change

- [ ] Test automation update
- [ ] API validation update
- [ ] Reliability or observability update
- [ ] Documentation update
- [ ] CI/CD pipeline update
- [ ] Security-aware validation update
- [ ] Bug fix
- [ ] Other

## Validation Performed

- [ ] Python/Pytest test suite passed
- [ ] Playwright automation suite passed, if applicable
- [ ] Postman/Newman REST API validation passed, if applicable
- [ ] Docker Compose stack started successfully, if applicable
- [ ] FastAPI `/health` endpoint validated, if applicable
- [ ] Prometheus `/metrics` endpoint validated, if applicable
- [ ] Newman XML report generated, if applicable
- [ ] GitHub Actions CI passed

## Release Readiness Considerations

- [ ] Change is covered by automated or documented validation
- [ ] Expected behavior is documented
- [ ] Failure behavior was considered
- [ ] No credentials, secrets, PHI, PII, or production data were added
- [ ] Documentation was updated, if needed

## Evidence

Add links, screenshots, command output, test reports, or notes that support the validation performed.

Examples:

- GitHub Actions run:
- Newman report artifact:
- Local test command:
- Screenshot:
- Relevant log output:

## Notes for Reviewers

Add anything a reviewer should pay special attention to.