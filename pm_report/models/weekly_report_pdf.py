from odoo import models


class WeeklyReportPDF(models.AbstractModel):
    _name = "report.pm_report.weekly_report_pdf_template"

    def _get_report_values(self, docids, data=None):
        docs = self.env["pm.project"].browse(docids)

        return {
            "docs": docs,
            "report_data": docs[0].get_weekly_report_pdf_data() if docs else {},
        }