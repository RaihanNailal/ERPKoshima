from odoo import models


class PMProject(models.Model):
    _inherit = "pm.project"


    def action_export_scurve_reportlab(self):

        self.ensure_one()

        return {
            "type":"ir.actions.act_url",
            "url":f"/pm_scurve/export_reportlab/{self.id}",
            "target":"self",
        }