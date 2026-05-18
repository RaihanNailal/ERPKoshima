# from odoo import http


# class PmResume(http.Controller):
#     @http.route('/pm_resume/pm_resume', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pm_resume/pm_resume/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('pm_resume.listing', {
#             'root': '/pm_resume/pm_resume',
#             'objects': http.request.env['pm_resume.pm_resume'].search([]),
#         })

#     @http.route('/pm_resume/pm_resume/objects/<model("pm_resume.pm_resume"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pm_resume.object', {
#             'object': obj
#         })

