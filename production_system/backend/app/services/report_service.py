from __future__ import annotations

from pathlib import Path

import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.schemas.reporting import ReportRequest, ReportResponse


class ReportService:
    def generate(self, req: ReportRequest) -> ReportResponse:
        reports_dir = Path("reports")
        reports_dir.mkdir(parents=True, exist_ok=True)

        if req.format.lower() == "xlsx":
            path = reports_dir / "debris_report.xlsx"
            df = pd.DataFrame(
                [
                    {"metric": "detections", "value": 3412},
                    {"metric": "high_risk_events", "value": 42},
                    {"metric": "avg_confidence", "value": 0.82},
                ]
            )
            df.to_excel(path, index=False)
            return ReportResponse(report_path=str(path.resolve()), format="xlsx")

        path = reports_dir / "debris_report.pdf"
        pdf = canvas.Canvas(str(path), pagesize=A4)
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(64, 800, "Space Debris Detection Report")
        pdf.setFont("Helvetica", 11)
        pdf.drawString(64, 776, f"Range: {req.from_date} -> {req.to_date}")
        pdf.drawString(64, 752, "Detections: 3412")
        pdf.drawString(64, 736, "High Risk Alerts: 42")
        pdf.drawString(64, 720, "Estimated catalog match rate: 91.3%")
        pdf.save()
        return ReportResponse(report_path=str(path.resolve()), format="pdf")
