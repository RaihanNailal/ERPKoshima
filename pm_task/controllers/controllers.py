# from odoo import http


# class PmTask(http.Controller):
#     @http.route('/pm_task/pm_task', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pm_task/pm_task/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('pm_task.listing', {
#             'root': '/pm_task/pm_task',
#             'objects': http.request.env['pm_task.pm_task'].search([]),
#         })

#     @http.route('/pm_task/pm_task/objects/<model("pm_task.pm_task"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pm_task.object', {
#             'object': obj
#         })

