# -*- coding: utf-8 -*-
{
    'name': "test_wkf_eg",

    'summary': """
        Show the workflow is working correctly""",

    'description': """
        Show the workflow is working correctly
    """,

    'author': "ZhangJie",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['workflow',],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        # 'views/templates.xml',
        
        'data/data.xml',
    ],
}