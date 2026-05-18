from odoo import models, fields


class PmGeneralWork(models.Model):
    _name = "pm.general.work"
    _description = "PM General Work"
    _order = "sequence, id"

    sequence = fields.Integer(
        default=10
    )

    project_id = fields.Many2one(
        "pm.project",
        required=True,
        ondelete="cascade",
    )

    name = fields.Char(
        required=True
    )

    line_ids = fields.One2many(
        "pm.general.work.line",
        "work_id",
        string="Bullets",
    )


class PmGeneralWorkLine(models.Model):
    _name = "pm.general.work.line"
    _description = "PM General Work Line"
    _order = "sequence, id"

    sequence = fields.Integer(
        default=10
    )

    work_id = fields.Many2one(
        "pm.general.work",
        required=True,
        ondelete="cascade",
    )

    name = fields.Char(
        required=True
    )