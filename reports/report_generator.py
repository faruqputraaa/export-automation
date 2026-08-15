from datetime import datetime
from pathlib import Path


class ReportGenerator:

    def generate(self, result: dict) -> str:
        total = result["total"]
        sent = result["sent"]
        skipped = result["skipped"]
        failed = result["failed"]

        processed = sent + failed

        if processed > 0:
            success_rate = (
                sent / processed
            ) * 100
        else:
            success_rate = 0

        report = f"""
========================================
       EXPORT AUTOMATION REPORT
========================================

Generated:
{datetime.now().isoformat()}

Total Buyers:
{total}

Emails Sent:
{sent}

Emails Failed:
{failed}

Duplicates Skipped:
{skipped}

Success Rate:
{success_rate:.2f}%

========================================
"""

        return report

    def save(
        self,
        result: dict,
        file_path: str = "reports/latest_report.txt"
    ):
        report = self.generate(result)

        path = Path(file_path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        path.write_text(
            report,
            encoding="utf-8"
        )

        return path