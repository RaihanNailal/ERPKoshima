from odoo import models, fields


class PmWeeklyTable(models.Model):
    _name = "pm.weekly.table"
    _description = "PM Weekly Table"
    _order = "sequence, id"

    sequence = fields.Integer(
        default=10
    )

    name = fields.Char(
        required=True
    )

    project_id = fields.Many2one(
        "pm.project",
        required=True,
        ondelete="cascade",
        index=True,
    )

    column_ids = fields.One2many(
        "pm.weekly.table.column",
        "table_id",
        string="Columns",
    )

    line_ids = fields.One2many(
        "pm.weekly.table.line",
        "table_id",
        string="Lines",
    )

    type = fields.Selection(
        [
            ("supervisor", "Supervisor"),
            ("technical", "Technical"),
            ("awareness", "Awareness"),
        ],
        string="Type",
    )

class PmWeeklyTableColumn(models.Model):
    _name = "pm.weekly.table.column"
    _description = "PM Weekly Table Column"
    _order = "sequence, id"

    sequence = fields.Integer(
        default=10
    )

    name = fields.Char(
        required=True
    )

    table_id = fields.Many2one(
        "pm.weekly.table",
        required=True,
        ondelete="cascade",
        index=True,
    )

class PmWeeklyTableLine(models.Model):
    _name = "pm.weekly.table.line"
    _description = "PM Weekly Table Line"
    _order = "sequence, id"

    sequence = fields.Integer(
        default=10
    )

    table_id = fields.Many2one(
        "pm.weekly.table",
        required=True,
        ondelete="cascade",
        index=True,
    )

    name = fields.Char(
        required=True
    )

    position = fields.Char()

    note = fields.Text()

    value_ids = fields.One2many(
        "pm.weekly.table.value",
        "line_id",
        string="Values",
    )

class PmWeeklyTableValue(models.Model):
    _name = "pm.weekly.table.value"
    _description = "PM Weekly Table Value"
    _rec_name = "line_id"

    line_id = fields.Many2one(
        "pm.weekly.table.line",
        required=True,
        ondelete="cascade",
        index=True,
    )

    column_id = fields.Many2one(
        "pm.weekly.table.column",
        required=True,
        ondelete="cascade",
        index=True,
    )

    value = fields.Boolean(
        default=False
    )

    _sql_constraints = [
        (
            "unique_line_column",
            "unique(line_id, column_id)",
            "Column already exists in this line."
        )
    ]