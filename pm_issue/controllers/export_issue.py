from odoo import http
from odoo.http import request
from .issue_reportlab import build_issue_report_pdf


class IssueExport(http.Controller):

    @http.route(
        "/pm_issue/export_selected",
        auth="user",
    )
    def export_selected_issue(self, ids=None, **kw):

        if not ids:
            return request.not_found()

        issue_ids = [
            int(x)
            for x in ids.split(",")
            if x
        ]

        issues = request.env["pm.issue"].browse(issue_ids)

        pdf = build_issue_report_pdf(issues)

        return request.make_response(
            pdf,
            headers=[
                ("Content-Type", "application/pdf"),
                (
                    "Content-Disposition",
                    "inline; filename=issue_report.pdf",
                ),
            ],
        )