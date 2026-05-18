from odoo import models, fields, api


class PmProject(models.Model):
    _name = 'pm.project'
    _description = 'Project'
    _order = "status"

    name = fields.Char(string='Project Name', required=True)

    project_code = fields.Char(
        string='Project Code',
        copy=False,
    )

    logo_left = fields.Image(
        "Logo Client",
        attachment=True,
    )

    logo_right = fields.Image(
        "Logo Vendor",
        attachment=True,
    )

    client_id = fields.Many2one('res.users', string='Client')
    leader_id = fields.Many2one(
        'res.users',
        string='Project Leader'
    )

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')

    status = fields.Selection([
        ('draft', 'Draft'),
        ('progres', 'In Progress'),
        ('done', 'Done'),
    ], default='draft', group_expand='_expand_status')


    progress = fields.Float(
        string='Progress (%)',
        compute='_compute_progress',
        store=True,
    )

    vendor = fields.Char(string="Vendor")
    po_number = fields.Char(string="Nomor PO")
    description = fields.Text(string="Deskripsi Project")
    project_location = fields.Text(string="Project Location")

    active = fields.Boolean(default=True)
    
        
    def action_button_start(self):
        for rec in self:
            rec.status = 'progres'

    def action_button_done(self):
        for rec in self:
            rec.status = 'done'

    # =========================
    # DELETE
    # =========================
    def action_delete_project(self):
        self.unlink()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Projects',
            'res_model': 'pm.project',
            'view_mode': 'kanban,list,form',
            'target': 'current',
        }

    # =========================
    # CLEAN EXPAND
    # =========================
    def _expand_status(self, *args):
        return [key for key, _ in self._fields['status'].selection]
    
    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:

            if not vals.get('project_code') and vals.get('name'):

                words = vals['name'].split()

                code=''.join(
                    w[0]
                    for w in words
                    if any(c.isalpha() for c in w)
                ).upper()

                vals['project_code']=(
                    code[:8] or 'PRJ'
                )

        return super().create(vals_list)

    def action_archive_project(self):
        for rec in self:
            rec.active = False

            self.env['pm.task'].with_context(active_test=False).search([
                ('project_id','=',rec.id)
            ]).write({'active': False})

            self.env['pm.wbs.task.week'].with_context(active_test=False).search([
                ('project_id','=',rec.id)
            ]).write({'active': False})

            # 🔥 TAMBAH INI (ISSUE)
            self.env['pm.issue'].with_context(active_test=False).search([
                ('project_id','=',rec.id)
            ]).write({'active': False})

    def action_restore_project(self):
        for rec in self:
            rec.active = True

            self.env['pm.task'].with_context(active_test=False).search([
                ('project_id','=',rec.id)
            ]).write({'active': True})

            self.env['pm.wbs.task.week'].with_context(active_test=False).search([
                ('project_id','=',rec.id)
            ]).write({'active': True})

            self.env['pm.issue'].with_context(active_test=False).search([
                ('project_id','=',rec.id)
            ]).write({'active': True})
