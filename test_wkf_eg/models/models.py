# -*- coding: utf-8 -*-

from odoo import models, fields, api


class TestWkfEg(models.Model):
    _name = 'test_wkf_eg.test_wkf_eg'
    _inherit = ['workflow.mixin']

    name = fields.Char()
    value = fields.Integer()
    value2 = fields.Float(compute="_value_pc", store=True)
    description = fields.Text()
    state = fields.Selection([
        ('draft', 'Draft'),
        ('to_approve', 'To Approve'),
        ('approved', 'Approved'),
        ('denied', 'Denied'),
    ], default='draft')

    @api.depends('value')
    def _value_pc(self):
        self.value2 = float(self.value) / 100
