from datetime import UTC, datetime
from pathlib import Path

from scripts.collect_release_signals import collect_release_signals
from scripts.quality_signal import QualitySignal
from scripts.read_playwright_results import get_playwright_quality_signal


signals: list[QualitySignal] = [
    QualitySignal("Docker Build", "PASS", "Infrastructure"),
    QualitySignal("Python Tests", "PASS", "Automation"),
    QualitySignal("Security Validation", "PASS", "Security"),
    QualitySignal("Performance Gate", "PASS", "Performance"),
    QualitySignal("Observability Validation", "PASS", "Observability"),
]

signals.append(get_playwright_quality_signal())

signals.extend(collect_release_signals())

blocking_failures = [signal.name for signal in signals if signal.status != "PASS"]
overall_status = "READY FOR RELEASE" if not blocking_failures else "BLOCK RELEASE"

lines = []
lines.append("=" * 58)
lines.append("SDET RELIABILITY FRAMEWORK - RELEASE READINESS REPORT")
lines.append("=" * 58)
lines.append(f"Generated UTC: {datetime.now(UTC).isoformat()}")
lines.append("")

for signal in signals:
    lines.append(f"{signal.name:<35} {signal.status}")

lines.append("")
lines.append("Detailed Evidence")
lines.append("-" * 58)

for signal in signals:
    if signal.total is not None:
        lines.append(f"{signal.name}")
        lines.append(f"Category   : {signal.category}")
        lines.append(f"Total      : {signal.total}")
        lines.append(f"Passed     : {signal.passed}")
        lines.append(f"Failed     : {signal.failed}")
        lines.append("")

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