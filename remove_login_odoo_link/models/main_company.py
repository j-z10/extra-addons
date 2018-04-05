from odoo import models, api


class MainCompany(models.AbstractModel):
    _name = 'main.company'

    @api.model
    def get_main_company_name(self):
        c_name = self.env.user.company_id.name
        if self.env['res.company'].search_count([]) == 1:
            return c_name
        else:
            return self.env['ir.config_parameter'].sudo().get_param('main.company_name', default=c_name)
