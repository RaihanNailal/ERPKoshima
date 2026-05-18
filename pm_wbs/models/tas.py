from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Task(models.Model):
    _inherit = 'pm.task'

    # =========================
    # BASIC FIELD
    # =========================
    wbs_number = fields.Char(string="WBS Number")

    manual_start_date = fields.Date(string="Start Date")
    manual_end_date = fields.Date(string="End Date")

    # computed (display)
    start_date = fields.Date(
        string="Start Date",
        compute="_compute_dates",
        store=True
    )

    end_date = fields.Date(
        string="End Date",
        compute="_compute_dates",
        store=True
    )

    pic_id = fields.Many2one(
        'res.users',
        string="Engineer",
        tracking=True
    )

    parent_id = fields.Many2one('pm.task', string="Parent Task")
    child_ids = fields.One2many('pm.task', 'parent_id', string="Sub Tasks")

    has_child = fields.Boolean(
        compute="_compute_has_child",
        store=True
    )

    # =========================
    # 🔥 STORAGE FIELD (REAL VALUE)
    # =========================
    manual_weight = fields.Float(string="Manual Weight (%)")

    # =========================
    # COMPUTED FIELD (DISPLAY)
    # =========================
    progress = fields.Float(
        string="Progress (%)",
        compute="_compute_progress",
        store=True,
        recursive=True
    )

    weight = fields.Float(
        string="Weight (%)",
        compute="_compute_weight",
        inverse="_inverse_weight",
        store=True,
        recursive=True
    )

    # =========================
    # COMPUTE
    # =========================

    @api.depends('child_ids')
    def _compute_has_child(self):
        for rec in self:
            rec.has_child = bool(rec.child_ids)

    @api.depends('child_ids.progress', 'child_ids.weight')
    def _compute_progress(self):
        Weekly = self.env['pm.wbs.task.week']

        # 🔥 ambil semua data sekaligus
        data = Weekly.read_group(
            [
                ('task_id', 'in', self.ids),
                ('active', '=', True)
            ],
            ['actual'],
            ['task_id']
        )

        mapped = {d['task_id'][0]: d['actual'] for d in data}

        for rec in self:
            if rec.child_ids:
                total_weight = sum(c.weight or 0 for c in rec.child_ids)

                if total_weight > 0:
                    if rec.child_ids:
                        rec.progress = sum(c.progress or 0 for c in rec.child_ids)
                    else:
                        rec.progress = mapped.get(rec.id, 0)
                else:
                    rec.progress = 0
            else:
                # 🔥 pakai mapping (NO SEARCH)
                rec.progress = mapped.get(rec.id, 0)

    @api.depends('child_ids.weight', 'manual_weight')
    def _compute_weight(self):
        for rec in self:
            if rec.child_ids:
                rec.weight = sum(c.weight or 0 for c in rec.child_ids)
            else:
                rec.weight = rec.manual_weight or 0

    # =========================
    # INVERSE
    # =========================

    def _inverse_weight(self):
        for rec in self:
            if not rec.child_ids:
                rec.manual_weight = rec.weight

    # =========================
    # DELETE CASCADE
    # =========================

    def unlink(self):
        for rec in self:
            if rec.child_ids:
                rec.child_ids.unlink()
        return super().unlink()

    # =========================
    # 🔥 VALIDATION PROJECT (LEAF ONLY)
    # =========================

    @api.constrains('manual_weight', 'project_id')
    def _check_total_weight_project(self):
        for rec in self:
            if not rec.project_id:
                continue

            project = rec.project_id

            leaf_tasks = project.task_ids.filtered(lambda t: not t.child_ids)

            total_weight = sum(t.manual_weight or 0 for t in leaf_tasks)

            if total_weight > 100:
                raise ValidationError(
                    f"Total weight project '{project.name}' melebihi 100% ({total_weight}%)"
                )

    # =========================
    # 🔥 VALIDATION SUBTASK
    # =========================

    @api.constrains('manual_weight', 'parent_id')
    def _check_subtask_weight(self):
        for rec in self:
            if rec.parent_id:
                siblings = rec.parent_id.child_ids
                total = sum(t.manual_weight or 0 for t in siblings)

                if total > 100:
                    raise ValidationError(
                        f"Total weight subtask dari '{rec.parent_id.name}' melebihi 100% ({total}%)"
                    )

    # =========================
    # 🔥 LIMIT INDIVIDUAL
    # =========================

    @api.constrains('manual_weight')
    def _check_weight_limit(self):
        for rec in self:
            if rec.manual_weight > 100:
                raise ValidationError("Weight tidak boleh lebih dari 100%")

    # =========================
    # 🔥 ENGINEER RULE
    # =========================

    @api.constrains('pic_id', 'child_ids')
    def _check_pic_only_leaf(self):
        for rec in self:
            if rec.child_ids and rec.pic_id:
                raise ValidationError(
                    "Engineer hanya boleh diisi pada subtask (leaf task)."
                )

    @api.onchange('child_ids')
    def _onchange_child_clear_pic(self):
        for rec in self:
            if rec.child_ids:
                rec.pic_id = False

    @api.depends(
        'child_ids.manual_start_date',
        'child_ids.manual_end_date',
        'manual_start_date',
        'manual_end_date'
    )
    def _compute_dates(self):
        for rec in self:

            if rec.child_ids:
                starts = [d for d in rec.child_ids.mapped('manual_start_date') if d]
                ends = [d for d in rec.child_ids.mapped('manual_end_date') if d]

                rec.start_date = min(starts) if starts else False
                rec.end_date = max(ends) if ends else False

            else:
                rec.start_date = rec.manual_start_date
                rec.end_date = rec.manual_end_date

    def write(self, vals):
        res = super().write(vals)

        if any(k in vals for k in ['manual_start_date', 'manual_end_date']):

            # 🔥 recompute dirinya sendiri
            self._compute_dates()

            # 🔥 recompute parent
            parents = self.mapped('parent_id')
            if parents:
                parents._compute_dates()

        return res