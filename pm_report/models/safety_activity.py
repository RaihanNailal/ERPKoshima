from odoo import models, fields


class PmSafetyActivity(models.Model):
    _name = "pm.safety.activity"
    _description = "PM Safety Activity"
    _order = "sequence, id"

    sequence = fields.Integer(
        default=10
    )

    project_id = fields.Many2one(
        "pm.project",
        required=True,
        ondelete="cascade",
        index=True,
    )

    name = fields.Char(
        required=True
    )

    line_ids = fields.One2many(
        "pm.safety.activity.line",
        "activity_id",
        string="Bullets",
    )

class PmSafetyActivityLine(models.Model):
    _name = "pm.safety.activity.line"
    _description = "PM Safety Activity Line"
    _order = "sequence, id"

    sequence = fields.Integer(
        default=10
    )

    activity_id = fields.Many2one(
        "pm.safety.activity",
        required=True,
        ondelete="cascade",
        index=True,
    )

    name = fields.Char(
        required=True
    )