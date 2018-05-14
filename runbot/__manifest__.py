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
        'views/runbot_repo_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
}
