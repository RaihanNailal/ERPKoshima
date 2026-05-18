from odoo import models, fields, api


class IssueAssignWizard(models.TransientModel):
    _name = 'pm.issue.assign.wizard'
    _description = 'Assign Issue Task'


    issue_id = fields.Many2one(
        'pm.issue',
        required=True
    )

    engineer_id = fields.Many2one(
        'res.users',
        string='Engineer',
        required=True
    )

    task_name = fields.Char(
        string='Task Name',
        required=True
    )


    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        if res.get('issue_id'):
            issue = self.env['pm.issue'].browse(
                res['issue_id']
            )
            res['task_name'] = issue.name

        return res


    def action_confirm(self):

        issue = self.issue_id

        if not issue.project_id.active:
            raise ValidationError("Project sudah di-archive, tidak bisa assign task")

        task = self.env['pm.task'].create({
            'name': f'[ISSUE] {self.task_name}',
            'project_id': issue.project_id.id,
            'pic_id': self.engineer_id.id,
            'issue_source_task_id': issue.task_id.id,
            'is_issue_task': True,
            'status': 'progress',
        })

        issue.write({
            'converted_task_id': task.id,
            'is_converted': True,
            'reviewed_by': self.env.user.id,
            'reviewed_date': fields.Date.today(),
            'status': 'progress',
        })

        return {
            'type':'ir.actions.client',
            'tag':'reload'
        }