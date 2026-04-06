from pydantic import BaseModel


class ReportRequest(BaseModel):
    from_date: str
    to_date: str
    format: str = "pdf"


class ReportResponse(BaseModel):
    report_path: str
    format: str
