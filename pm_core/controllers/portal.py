from odoo import http
from odoo.http import request


class PMPortal(http.Controller):

    @http.route(['/my/projects'], type='http', auth='user', website=True)
    def my_projects(self):

        user = request.env.user

        projects = request.env['pm.project'].search([
                ('client_id','=',user.id)
            ])

        return request.render('pm_project.portal_my_projects', {
            'projects': projects
        })