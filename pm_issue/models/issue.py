from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PmIssue(models.Model):
    _name = 'pm.issue'
    _description = 'Issue Register'
    _order = 'status, submitted_date desc'

    name = fields.Char(string="Description", required=True)

    register_number = fields.Char(
        string="Register Number",
        readonly=True,
        copy=False,
    )

    project_id = fields.Many2one(
        'pm.project',
        required=True,
        ondelete='cascade'
    )

    task_id = fields.Many2one(
        'pm.task',
        string="Related Task",
         required=False
    )

    submitted_by = fields.Many2one(
        'res.users',
        default=lambda self: self.env.user,
        readonly=True
    )

    submitted_date = fields.Date(
        default=fields.Date.today
    )

    reviewed_by = fields.Many2one(
        'res.users',
        string='Reviewed By',
    )

    reviewed_date = fields.Date(
        string='Reviewed Date',
    )

    status = fields.Selection(
        [
            ('open', 'Submitted'),
            ('progress', 'Under Review'),
            ('closed', 'Solved'),
        ],
        default='open',
        group_expand='_expand_status'
    )

    converted_task_id = fields.Many2one(
        'pm.task',
        string="Task",
        readonly=True
    )

    is_converted = fields.Boolean(default=False)

    photo_ids = fields.One2many(
        'pm.issue.photo',
        'issue_id',
        domain=[('type','=','before')],
        string='Issue Documentation'
    )

    task_photo_ids = fields.One2many(
        'pm.task.photo',
        compute='_compute_task_photos',
        string='Task Documentation'
    )

    after_photo_ids = fields.One2many(
        'pm.issue.photo',
        'issue_id',
         domain=[('type','=','after')], 
        string='After Documentation'
    )

    is_client_visible = fields.Boolean(
        string="Visible to Client",
        default=False
    )

    active = fields.Boolean(
        related='project_id.active',
        store=True
    )

    corrective_action = fields.Text(
        string='Corrective Action'
    )

    # AUTO NUMBER
    @api.model
    def create(self, vals_list):

        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        for vals in vals_list:

            # 🔥 FIX 1: isi project dari task kalau belum ada
            if vals.get('task_id') and not vals.get('project_id'):
                task = self.env['pm.task'].browse(vals['task_id'])
                vals['project_id'] = task.project_id.id

            # 🔥 FIX 2: safety kalau masih kosong
            if not vals.get('project_id'):
                raise ValueError("Project wajib diisi")

            project = self.env['pm.project'].browse(vals['project_id'])

            if not project.active:
                raise ValueError("Project sudah di-archive")

            if not vals.get('register_number') or vals.get('register_number') in ('NEW','/'):
                vals['register_number'] = self._generate_issue_number(project)

        return super().create(vals_list)

    def action_review(self):
        for rec in self:
            rec.write({
                'reviewed_by': self.env.user.id,
                'reviewed_date': fields.Date.today(),
                'status': 'progress',
            })

    # ACTION CLOSE
    def action_resolve(self):
        for rec in self:
            if not rec.corrective_action:
                raise ValidationError(
                    "Corrective Action wajib diisi sebelum Solve."
                )

            rec.write({
                'status': 'closed',
            })

    def _expand_status(self, *args):
        return [
            'open',
            'progress',
            'closed',
        ]

    def action_assign_task(self):
        self.ensure_one()

        if not self.project_id.active:
            raise ValidationError("Project sudah di-archive")

        return {
            'type': 'ir.actions.act_window',
            'name': 'Assign Engineer',
            'res_model': 'pm.issue.assign.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_issue_id': self.id,
            }
        }

    def _generate_issue_number(self, project):

        prefix = project.project_code or 'PRJ'

        last_issue = self.search(
            [
                ('project_id','=',project.id),
                ('register_number','!=','/')
            ],
            order='id desc',
            limit=1
        )

        next_num = 1

        if last_issue:
            try:
                next_num = int(
                    last_issue.register_number.split('-')[-1]
                ) + 1
            except:
                next_num = 1

        return f"{prefix}-ISS-{str(next_num).zfill(3)}"
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        project_id = self.env.context.get(
            'default_project_id'
        )

        if project_id:
            project = self.env['pm.project'].browse(
                project_id
            )

            res['register_number'] = self._generate_issue_number(
                project
            )

        return res
    
    @api.onchange('task_id')
    def _onchange_task(self):
        if self.task_id:
            self.project_id = self.task_id.project_id
        else:
            self.project_id = False

    @api.depends('converted_task_id', 'converted_task_id.photo_ids')
    def _compute_task_photos(self):
        for rec in self:
            if rec.converted_task_id:
                rec.task_photo_ids = rec.converted_task_id.photo_ids
            else:
                rec.task_photo_ids = False

    def action_print_issue_report(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/pm_issue/export_selected?ids=%s' % ','.join(
                map(str, self.ids)
            ),
            'target': 'new',
        }

class PmIssuePhoto(models.Model):
    _name = 'pm.issue.photo'
    _description = 'Issue Documentation'

    issue_id = fields.Many2one(
        'pm.issue',
        required=True,
        ondelete='cascade'
    )

    image = fields.Image(string="Foto", required=True, attachment=True,)
    image_name = fields.Char(string="Nama File")

    note = fields.Char(
        string="Keterangan",
        required=True
    )

    user_id = fields.Many2one(
        'res.users',
        default=lambda self: self.env.user,
        readonly=True,
        string="Uploaded By"
    )

    create_date = fields.Datetime(
        string="Uploaded At",
        readonly=True
    )

    type = fields.Selection([
        ('before', 'Before'),
        ('after', 'After')
    ], default='before')

    @api.model
    def create(self, vals_list):

        # 🔥 HANDLE kalau single dict
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        for vals in vals_list:
            vals.setdefault(
                'type',
                self.env.context.get('default_type', 'before')
            )

        return super().create(vals_list)
    
class IssueReport(models.AbstractModel):
    _name = 'report.pm_issue.report_issue_multi'

    def _get_report_values(self, docids, data=None):

        domain = self.env.context.get('active_domain')

        if domain:
            docs = self.env['pm.issue'].search(domain)
        else:
            docs = self.env['pm.issue'].browse(docids)

        return {
            'docs': docs
        }