from odoo import models, fields, api
from datetime import date


class PmProject(models.Model):
    _inherit = 'pm.project'


    weekly_actual = fields.Float(
        string="Actual Progress",
        compute="_compute_resume",
        store=True
    )

    weekly_plan = fields.Float(
        string="Planned Progress",
        compute="_compute_resume",
        store=True
    )

    deviation = fields.Float(
        string="Deviation",
        compute="_compute_resume",
        store=True
    )

    remaining_days = fields.Integer(
        string="Remaining Days",
        compute="_compute_resume",
        store=True
    )

    status_color = fields.Selection(
        [
            ('success', 'Success'),
            ('danger', 'Danger'),
        ],
        compute="_compute_resume",
        store=True
    )

    @api.depends(
        'start_date',
        'end_date'
    )
    def _compute_resume(self):

        today = date.today()

        for rec in self:

            rec.weekly_actual = 0
            rec.weekly_plan = 0
            rec.deviation = 0
            rec.remaining_days = 0
            rec.status_color = 'success'

            # =====================================
            # REMAINING DAYS
            # =====================================

            if rec.end_date:

                rec.remaining_days = (
                    rec.end_date - today
                ).days

            # =====================================
            # GET SUMMARY FROM WBS ENGINE
            # =====================================

            data = rec.get_wbs_data() or {}

            summary = data.get(
                'summary',
                []
            )

            if not summary:
                continue

            # =====================================
            # CURRENT WEEK
            # =====================================

            week = 1

            if rec.start_date:

                delta = (
                    today - rec.start_date
                ).days

                if delta >= 0:
                    week = (delta // 7) + 1

            week = min(
                week,
                len(summary)
            )

            row = summary[week - 1]

            # =====================================
            # VALUES
            # =====================================

            rec.weekly_actual = round(
                row.get('actual_cum', 0),
                2
            )

            rec.weekly_plan = round(
                row.get('plan_cum', 0),
                2
            )

            rec.deviation = round(
                row.get('deviation', 0),
                2
            )

            # =====================================
            # STATUS COLOR
            # =====================================

            if rec.deviation < 0:
                rec.status_color = 'danger'
            else:
                rec.status_color = 'success'


    def action_open_project_issues(self):

        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Issue Register',

            'res_model': 'pm.issue',

            'view_mode': 'list',

            'domain': [
                ('project_id', '=', self.id)
            ],

            'context': {
                'create': False,
                'edit': False,
                'delete': False,
            }
        }