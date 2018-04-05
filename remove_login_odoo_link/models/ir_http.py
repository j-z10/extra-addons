from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        value = super().session_info()
        value['main_company_name'] = self.env['main.company'].get_main_company_name()
        return value
