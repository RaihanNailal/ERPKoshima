from odoo import models, fields


class Task(models.Model):
    _name = 'pm.task'
    _description = 'Project Task'

    name = fields.Char(required=True)

    project_id = fields.Many2one(
        'pm.project',
        required=True,
        ondelete='cascade'
    )

    parent_id = fields.Many2one('pm.task')
    child_ids = fields.One2many('pm.task', 'parent_id')

    start_date = fields.Date()
    end_date = fields.Date()

    progress = fields.Float()
    weight = fields.Float()