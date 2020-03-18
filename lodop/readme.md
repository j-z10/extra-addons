主要是用来直接调用打印机打印, 普通打印需要下载PDF, 然后再本地调用打印机. 这样可以直接调用打印机

1. 有坑, 如果odoo跑了多个db, 那么在lodop打印html的时候是获取不到html中样式文件. 因为lodop是单独请求的静态文件, 在它请求的session中没有指定db
2. 如果是最普通的连打快递面单则简单的多, 需要用js画lodop的模板, 返回的rend_data给需要打印的关键数据, 然后options.type
```python

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def lodop_print_quotation(self):
        self.filtered(lambda s: s.state == 'draft').write({'state': 'sent'})
        base_url = self.env['ir.config_parameter'].get_param('web.base.url').encode('utf-8')
        iu = self.env.ref('sale.report_saleorder')
        rend_data_list = []
        for so in self:
            html = iu.render({'editable': False, 'docs': so})
            # 由于拿到html之后,是lodop调用打印,所以如果html中的静态文件需要指定base_url,lodop才能准确的拿到静态文件等
            print_html = re.sub(r'<head>', '<head><base href="%s"/>' % base_url, html)
            rend_data_list.append({
                'rend_data': print_html,
                'options': {
                    'pagesize': {'width': 2100, 'height': 2970},    # A4纸张, 以mm为单位
                    'printer': False,    # 打印机的名称, 不设置就会被lodop调用默认打印机
                    'print_init_name': '报价单(%s)' % so.name,
                    'type': False,      # 不设置就是默认html打印, 否则就是自己在js那边画lodop模板
                }
            })
        return {
            'type': 'ir.actions.client',
            'tag': 'lodop_print_main_menu',
            'target': 'new',
            'context': {
                'rend_data_list': rend_data_list,
            },
        }

```