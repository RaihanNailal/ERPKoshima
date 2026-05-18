from odoo import models, fields


class WeeklyReportPhoto(models.Model):
    _name = "pm.weekly.report.photo"
    _description = "Weekly Report Photo"

    project_id = fields.Many2one(
        "pm.project",
        required=True,
        ondelete="cascade",
    )

    name = fields.Char("Caption")
    image = fields.Image(
        "Photo",
        required=True,
        attachment=True,
    )