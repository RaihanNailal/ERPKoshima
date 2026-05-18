# from odoo import http


# class PmScurve(http.Controller):
#     @http.route('/pm_scurve/pm_scurve', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pm_scurve/pm_scurve/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('pm_scurve.listing', {
#             'root': '/pm_scurve/pm_scurve',
#             'objects': http.request.env['pm_scurve.pm_scurve'].search([]),
#         })

#     @http.route('/pm_scurve/pm_scurve/objects/<model("pm_scurve.pm_scurve"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pm_scurve.object', {
#             'object': obj
#         })

