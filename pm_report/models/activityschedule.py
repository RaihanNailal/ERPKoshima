from odoo import models, fields


class PmActivitySchedule(models.Model):
    _name = "pm.activity.schedule"
    _description = "PM Activity Schedule"

    project_id = fields.Many2one(
        "pm.project",
        required=True,
        ondelete="cascade",
    )

    category = fields.Selection(
        [
            ("last_week", "Last Week"),
            ("this_week", "This Week"),
            ("next_week", "Next Week"),
        ],
        required=True,
    )

    line_ids = fields.One2many(
        "pm.activity.schedule.line",
        "schedule_id",
        string="Tasks",
    )


class PmActivityScheduleLine(models.Model):
    _name = "pm.activity.schedule.line"
    _description = "PM Activity Schedule Line"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)

    schedule_id = fields.Many2one(
        "pm.activity.schedule",
        required=True,
        ondelete="cascade",
    )

    name = fields.Char(required=True)