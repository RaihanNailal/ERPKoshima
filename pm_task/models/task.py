from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta


class Task(models.Model):
    _inherit = 'pm.task'

    project_id = fields.Many2one(
        'pm.project',
        ondelete='cascade'
    )

    actual_input = fields.Float(string="Progress Minggu Ini (%)")

    photo_ids = fields.One2many(
        'pm.task.photo',
        'task_id',
        string="Dokumentasi"
    )

    pic_id = fields.Many2one(
        'res.users',
        string='PIC'
    )

    # 🔥 TOTAL ACTUAL (UNTUK REPORT)
    total_actual = fields.Float(
        string="Total Actual (%)",
        compute="_compute_total_actual",
        store=False
    )

    # 🔥 PROGRESS (STATE UTAMA - MANUAL)
    progress = fields.Float(
        string="Progress (%)",
        group_operator=False
    )

    # 🔥 SISA
    remaining_progress = fields.Float(
        string="Sisa (%)",
        compute="_compute_remaining_progress",
        store=True,
        group_operator=False
    )

    weight = fields.Float(
        related=False,
        group_operator=False
    )

    # 🔥 CURRENT WEEK
    current_week_label = fields.Char(
        string="Current Week",
        compute="_compute_current_week"
    )

    note_ids = fields.One2many(
        'pm.task.note',
        'task_id',
        string='Daily Notes'
    )

    is_issue_task = fields.Boolean(default=False)

    issue_source_task_id = fields.Many2one(
        'pm.task',
        string='Related Task',
        readonly=True
    )

    corrective_action = fields.Text(
        string='Corrective Action',
        compute='_compute_corrective_action',
        inverse='_inverse_corrective_action',
    )

    status = fields.Selection([
        ('open', 'Open'),
        ('progress', 'In Progress'),
        ('done', 'Done'),
    ], default='open', string="Status")

    task_group = fields.Selection(
        [
            ('planned','Planned Tasks'),
            ('issue','Issue Tasks'),
        ],
        compute='_compute_task_group',
        store=True,
        group_expand='_group_expand_task_group',
        string='Task Type'
    )

    issue_photo_html = fields.Html(
        compute="_compute_issue_photo_html"
    )

    active = fields.Boolean(default=True)
    # =========================
    # TOTAL ACTUAL
    # =========================
    @api.depends()
    def _compute_total_actual(self):
        Weekly = self.env['pm.wbs.task.week']
        for rec in self:
            rec.total_actual = sum(
                Weekly.search([
                    ('task_id', '=', rec.id),
                    ('active', '=', True)
                ]).mapped('actual')
            )

    # =========================
    # REMAINING
    # =========================
    @api.depends('weight', 'progress')
    def _compute_remaining_progress(self):
        for rec in self:
            rec.remaining_progress = max(
                (rec.weight or 0) - (rec.progress or 0),
                0
            )

    # =========================
    # CURRENT WEEK
    # =========================
    @api.depends('project_id')
    def _compute_current_week(self):
        today = fields.Date.today()

        for rec in self:
            if not rec.project_id.start_date:
                rec.current_week_label = "-"
                continue

            delta_days = (today - rec.project_id.start_date).days

            if delta_days < 0:
                rec.current_week_label = "W0"
            else:
                week = (delta_days // 7) + 1
                rec.current_week_label = f"W{week}"

    # =========================
    # VALIDASI INPUT
    # =========================
    @api.constrains('actual_input')
    def _check_actual_input(self):
        for rec in self:
            if rec.actual_input < 0:
                raise ValidationError("Progress tidak boleh negatif")
            if rec.actual_input > 100:
                raise ValidationError("Progress tidak boleh lebih dari 100%")

    # =========================
    # WRITE
    # =========================
    def write(self, vals):
        res = super().write(vals)

        if 'actual_input' in vals:
            for rec in self:
                if rec.actual_input and rec.actual_input > 0:
                    rec._write_actual_to_week()

        return res

    # =========================
    # CORE LOGIC
    # =========================
    def _write_actual_to_week(self):
        Weekly = self.env['pm.wbs.task.week']
        today = fields.Date.today()

        for rec in self:

            # ❗ VALIDASI
            if rec.child_ids:
                raise ValidationError(
                    "Progress hanya boleh diinput pada subtask (leaf task)."
                )

            if not rec.actual_input:
                continue

            # 🔥 HITUNG PROGRESS BARU
            current = rec.progress or 0
            new_total = current + rec.actual_input

            if new_total > rec.weight:
                raise ValidationError(
                    f"Melebihi bobot! Sisa hanya {rec.remaining_progress:.2f}%"
                )

            # 🔥 CARI WEEK
            weeks = Weekly.search([
                ('project_id', '=', rec.project_id.id),
                ('active', '=', True)
            ], order='date ASC')

            target_week = False
            for w in weeks:
                if w.date <= today <= (w.date + timedelta(days=6)):
                    target_week = w
                    break

            if not target_week:
                continue

            # 🔥 UPDATE WEEKLY
            rec_week = Weekly.search([
                ('task_id', '=', rec.id),
                ('date', '=', target_week.date),
                ('active', '=', True)
            ], limit=1)

            if rec_week:
                rec_week.actual += rec.actual_input
            else:
                Weekly.create({
                    'task_id': rec.id,
                    'project_id': rec.project_id.id,
                    'date': target_week.date,
                    'actual': rec.actual_input
                })

            # 🔥 UPDATE PROGRESS (INI KUNCI)
            rec.progress = new_total

            # 🔥 RESET INPUT
            rec.with_context(skip_write=True).update({
                'actual_input': 0
            })

    def action_create_issue(self):
        self.ensure_one()

        return {
            'type':'ir.actions.act_window',
            'name':'Create Issue',
            'res_model':'pm.issue',
            'view_mode':'form',
            'target':'new',
            'context':{
                'default_project_id': self.project_id.id,
                'default_task_id': self.id,
            }
        }
    
    def action_mark_done(self):
        for rec in self:
            rec.status = 'done'

            if rec.is_issue_task:
                issue = self.env['pm.issue'].search([
                    ('converted_task_id', '=', rec.id)
                ], limit=1)

                # auto Resolve issue
                if issue and issue.status != 'closed':
                    issue.action_resolve()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Issue resolved successfully',
                'type': 'success',
                'sticky': False,
                'next': {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                }
            }
        }
    
    @api.depends('is_issue_task')
    def _compute_task_group(self):
        for rec in self:
            rec.task_group = (
                'issue' if rec.is_issue_task else 'planned'
            )

    def _group_expand_task_group(self, values, domain):
        return ['planned', 'issue']
    
    @api.depends('is_issue_task')
    def _compute_issue_photo_html(self):
        Issue = self.env['pm.issue']

        issues = Issue.search([
            ('converted_task_id', 'in', self.ids)
        ])

        issue_map = {i.converted_task_id.id: i for i in issues}

        for rec in self:

            html = '<div style="display:flex; flex-wrap:wrap; gap:10px;">'

            issue = issue_map.get(rec.id)

            if issue:
                for photo in issue.photo_ids:
                    html += f"""
                        <div style="
                            width:150px;
                            border:1px solid #ddd;
                            border-radius:8px;
                            overflow:hidden;
                        ">
                            <img src="/web/image/pm.issue.photo/{photo.id}/image"
                                style="width:100%; height:120px; object-fit:cover;"
                                alt="Issue Image"/>
                            <div style="text-align:center;">
                                {photo.note or ''}
                            </div>
                        </div>
                    """
            else:
                html += '<i>Tidak ada dokumentasi issue</i>'

            html += '</div>'

            rec.issue_photo_html = html

    @api.depends('is_issue_task')
    def _compute_corrective_action(self):
        Issue = self.env['pm.issue']

        issues = Issue.search([
            ('converted_task_id', 'in', self.ids)
        ])

        issue_map = {
            i.converted_task_id.id: i
            for i in issues
        }

        for rec in self:
            issue = issue_map.get(rec.id)
            rec.corrective_action = issue.corrective_action if issue else False


    def _inverse_corrective_action(self):
        Issue = self.env['pm.issue']

        for rec in self:
            if not rec.is_issue_task:
                continue

            issue = Issue.search([
                ('converted_task_id', '=', rec.id)
            ], limit=1)

            if issue:
                issue.corrective_action = rec.corrective_action

class TaskPhoto(models.Model):
    _name = 'pm.task.photo'
    _description = 'Task Photo'

    task_id = fields.Many2one('pm.task', ondelete='cascade')

    image = fields.Image(string="Foto", required=True, attachment=True,)
    image_name = fields.Char(string="Nama File")

    note = fields.Char(string="Keterangan")

    # 🔥 USER
    user_id = fields.Many2one(
        'res.users',
        default=lambda self: self.env.user,
        readonly=True,
        string="Uploaded By"
    )

    # 🔥 TIME
    create_date = fields.Datetime(
        string="Uploaded At",
        readonly=True
    )

class PmTaskNote(models.Model):
    _name = 'pm.task.note'
    _description = 'Task Daily Notes'
    _order = 'create_date desc'

    task_id = fields.Many2one(
        'pm.task',
        required=True,
        ondelete='cascade'
    )

    note = fields.Text(
        string="Catatan",
        required=True
    )

    user_id = fields.Many2one(
        'res.users',
        default=lambda self: self.env.user,
        readonly=True
    )

    create_date = fields.Datetime(
        readonly=True
    )


class PmProject(models.Model):
    _inherit = 'pm.project'

    task_ids = fields.One2many(
        'pm.task',
        'project_id',
        string='Tasks'
    )