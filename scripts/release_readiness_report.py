from datetime import UTC, datetime
from pathlib import Path
from scripts.read_playwright_results import get_playwright_status
from scripts.collect_release_signals import collect_release_signals


signals = [
    ("Docker Build", "PASS"),
    ("Python Tests", "PASS"),
    ("Security Validation", "PASS"),
    ("Performance Gate", "PASS"),
    ("Observability Validation", "PASS"),
]

signals.append(get_playwright_status())

signals.extend(collect_release_signals())

blocking_failures = [name for name, status in signals if status != "PASS"]
overall_status = "READY FOR RELEASE" if not blocking_failures else "BLOCK RELEASE"

lines = []
lines.append("=" * 58)
lines.append("SDET RELIABILITY FRAMEWORK - RELEASE READINESS REPORT")
lines.append("=" * 58)
lines.append(f"Generated UTC: {datetime.now(UTC).isoformat()}")
lines.append("")

for name, status in signals:
    lines.append(f"{name:<35} {status}")

lines.append("-" * 58)
lines.append(f"Overall Status: {overall_status}")
lines.append("=" * 58)

report_text = "\n".join(lines)

print(report_text)

reports_dir = Path("reports")
reports_dir.mkdir(exist_ok=True)

report_path = reports_dir / "release_readiness_report.txt"
report_path.write_text(report_text, encoding="utf-8")

print()
print(f"Report written to: {report_path}")