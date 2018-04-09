{
    'name': 'base_ir_cron_concurrent',
    'version': '0.1',
    "category": "Tools",
    'description': """某条定时任务正在执行期间(cron worker或其他用户通过UI手动触发), 无法被另一用户通过UI手动触发执行该任务.""",
    'author': 'Todd',
    'depends': ['base'],
    'data': [
    ],
}
