{
    'name': 'workflow',
    'version': '1.0',
    'category': 'Extra Tools',
    'description': """
Trans workflow on odoo-10 to odoo-11.0
""",
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',

        'views/workflow_view.xml',
        'views/templates.xml',
    ],
    'installable': True,
}
