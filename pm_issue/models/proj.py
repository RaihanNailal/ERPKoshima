from odoo import models

class PmProject(models.Model):
    _inherit = 'pm.project'

    def action_open_issue(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Issue Register - {self.name}',
            'res_model': 'pm.issue',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {
                'default_project_id': self.id
            }
        }