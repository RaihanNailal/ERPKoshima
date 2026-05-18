# from odoo import http


# class PmProject(http.Controller):
#     @http.route('/pm_project/pm_project', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pm_project/pm_project/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('pm_project.listing', {
#             'root': '/pm_project/pm_project',
#             'objects': http.request.env['pm_project.pm_project'].search([]),
#         })

#     @http.route('/pm_project/pm_project/objects/<model("pm_project.pm_project"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pm_project.object', {
#             'object': obj
#         })

