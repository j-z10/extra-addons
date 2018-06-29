from odoo import models, api
import time


class Base(models.AbstractModel):
    _inherit = 'base'

    @api.multi
    def export_data(self, fields_to_export, raw_data=False):
        s = time.time()
        if self.env.context.get('no_external_id', False) and ['id'] in fields_to_export:
            fields_to_export.remove(['id'])
        print('fields is', fields_to_export)
        res = super().export_data(fields_to_export, raw_data=raw_data)
        print('using', time.time() - s, 'seconds')
        return res
