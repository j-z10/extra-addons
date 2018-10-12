from odoo.http import request, route, Controller


class DemoCtrl(Controller):
    @route('/hello', type='http', auth="none", website=True)
    def hello(self, *args, **kwargs):
        response = request.render('ajax_demo.layout', {})
        response.headers['X-Frame-Options'] = 'DENY'
        return response
