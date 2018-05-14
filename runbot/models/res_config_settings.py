from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    # _name = 'runbot.config.settings'
    _inherit = 'res.config.settings'

    default_workers = fields.Integer(string='Total Number of Workers')
    default_running_max = fields.Integer(string='Maximum Number of Running Builds')
    default_timeout = fields.Integer(string='Default Timeout (in seconds)')
    default_starting_port = fields.Integer('Starting Port for Running Builds')
    default_domain = fields.Char('Runbot Domain')

    def get_values(self):
        vals = super().get_values()
        icp = self.env['ir.config_parameter'].sudo()
        workers = icp.get_param('runbot.workers', default=6)
        running_max = icp.get_param('runbot.running_max', default=75)
        timeout = icp.get_param('runbot.timeout', default=1800)
        starting_port = icp.get_param('runbot.starting_port', default=2000)
        runbot_domain = icp.get_param('runbot.domain', default='runbot.odoo.com')
        vals.update({
            'default_workers': int(workers),
            'default_running_max': int(running_max),
            'default_timeout': int(timeout),
            'default_starting_port': int(starting_port),
            'default_domain': runbot_domain,
        })
        return vals
    
    def set_values(self):
        icp = self.env['ir.config_parameter'].sudo()
        icp.set_param('runbot.workers', self.default_workers)
        icp.set_param('runbot.running_max', self.default_running_max)
        icp.set_param('runbot.timeout', self.default_timeout)
        icp.set_param('runbot.starting_port', self.default_starting_port)
        icp.set_param('runbot.domain', self.default_domain)
        return super().set_values()
