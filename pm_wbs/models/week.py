from odoo import models, fields, api
from odoo.exceptions import ValidationError


class WbsTaskWeek(models.Model):
    _name = 'pm.wbs.task.week'
    _description = 'WBS Weekly Data'

    task_id = fields.Many2one(
        'pm.task',
        required=True,
        ondelete='cascade'
    )
    project_id = fields.Many2one(
        'pm.project',
        required=True,
        ondelete='cascade'
    )
    date = fields.Date(required=True)

    plan = fields.Float()
    actual = fields.Float()

    # =========================
    # 🔥 ANTI DUPLIKAT (WAJIB)
    # =========================
    _sql_constraints = [
        (
            'unique_task_date',
            'unique(task_id, date)',
            'Data weekly untuk task dan tanggal ini sudah ada!'
        )
    ]

    active = fields.Boolean(default=True)

    # =========================
    # 🔥 HELPER (CORE CLEAN)
    # =========================
    def _upsert_week(self, task, date, field_name, value):
        """
        Helper untuk create/update weekly
        TANPA mengubah behavior sistem
        """

        # 🔒 validasi dasar
        if value < 0:
            raise ValidationError("Nilai tidak boleh negatif")

        rec = self.search([
            ('task_id', '=', task.id),
            ('date', '=', date),
            ('active', '=', True)
        ], limit=1)

        if rec:
            rec[field_name] = float(value)
        else:
            self.create({
                'task_id': task.id,
                'project_id': task.project_id.id,
                'date': date,
                field_name: float(value),
                'active': True 
            })

    # =========================
    # WRITE PLAN
    # =========================
    @api.model
    def write_plan(self, task_id, date, value):

        task = self.env['pm.task'].browse(task_id)

        if not task.exists():
            raise ValidationError("Task tidak ditemukan!")

        if not task.project_id:
            raise ValidationError("Task tidak punya project!")
        
        if not task.project_id.active:
            raise ValidationError("Project sudah di-archive, tidak bisa input progress")

        self._upsert_week(task, date, 'plan', value)

        return True

    # =========================
    # WRITE ACTUAL
    # =========================
    @api.model
    def write_actual(self, task_id, date, value):

        task = self.env['pm.task'].browse(task_id)

        if not task.exists():
            raise ValidationError("Task tidak ditemukan!")

        if not task.project_id:
            raise ValidationError("Task tidak punya project!")
        
        if not task.project_id.active:
            raise ValidationError("Project sudah di-archive, tidak bisa input progress")

        self._upsert_week(task, date, 'actual', value)

        return True