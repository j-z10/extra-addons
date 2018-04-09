# coding: utf-8

from odoo import models, exceptions, api


class Cron(models.Model):
    _inherit = 'ir.cron'

    @api.multi
    def method_direct_trigger(self):
        for cron in self:
            try:
                # 在执行一条任务之前, 尝试获取行锁
                cron._try_lock()
            except exceptions.UserError:
                # 如果不成功, 代表此行任务正在被定时任务或者另一个用户执行
                raise exceptions.UserError('This cron task is currently being executed by another cron worker or user.')
            else:
                cron._callback(cron.model, cron.function, cron.args, cron.id)
        return True
