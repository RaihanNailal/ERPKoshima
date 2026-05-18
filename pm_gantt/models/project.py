from odoo import models

class PmProject(models.Model):
    _inherit = 'pm.project'

    def action_view_gantt_from_list(self):
        self.ensure_one()  # 🔥 penting

        return {
            'type': 'ir.actions.client',
            'tag': 'pm_gantt.gantt_js_action',
            'context': {
                'project_id': self.id,
                'project_name': self.name,
            }
        }