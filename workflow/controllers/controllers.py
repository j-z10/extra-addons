from odoo import http


class WkfController(http.Controller):
    @http.route('/workflow/exec_workflow', type='json', auth="user")
    def exec_workflow(self, model, id, signal):
        http.request.session.check_security()
        return http.request.env[model].browse(id).signal_workflow(signal)[id]
