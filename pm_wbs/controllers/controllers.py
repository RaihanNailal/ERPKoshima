# from odoo import http


# class PmWbs(http.Controller):
#     @http.route('/pm_wbs/pm_wbs', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pm_wbs/pm_wbs/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('pm_wbs.listing', {
#             'root': '/pm_wbs/pm_wbs',
#             'objects': http.request.env['pm_wbs.pm_wbs'].search([]),
#         })

#     @http.route('/pm_wbs/pm_wbs/objects/<model("pm_wbs.pm_wbs"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pm_wbs.object', {
#             'object': obj
#         })

