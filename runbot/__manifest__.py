{
    'name': 'Runbot',
    'category': 'Website',
    'summary': 'Runbot',
    'description': """
This is the module to manage the runbot
=======================================

base from [odoo-extra](https://github.com/odoo/odoo-extra "odoo-extra runbot") runbot.
    """,
    'version': '0.1',
    'author': 'Zhang Jie',
    'depends': ['website'],
    'external_dependencies': {
        'python': ['matplotlib'],
    },
    'data': [
        'data/ir_cron_data.xml',

        'security/data.xml',
        'security/ir.model.access.csv',
        'security/ir.rule.csv',

        'views/runbot_repo_views.xml',
        'views/runbot_branch_views.xml',
        'views/runbot_build_views.xml',
        'views/runbot_event_views.xml',
        'views/templates.xml',

        'views/res_config_settings_views.xml',
    ],
    'installable': True,
}
