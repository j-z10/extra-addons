from odoo import models, fields


class RunbotEvent(models.Model):
    _inherit = 'ir.logging'
    _order = 'id'

    TYPES = [(t, t.capitalize()) for t in 'client server runbot'.split()]
    build_id = fields.Many2one('runbot.build', 'Build')
    type = fields.Selection(TYPES, string='Type', required=True)
