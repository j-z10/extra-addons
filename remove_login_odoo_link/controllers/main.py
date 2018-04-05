from odoo.http import request, route

from odoo.addons.web.controllers.main import Home


class LoginCtrl(Home):
    @route()
    def web_login(self, *args, **kwargs):
        response = super().web_login(*args, **kwargs)
        if response.is_qweb:
            response.qcontext['title'] = request.env['main.company'].get_main_company_name()
        return response
