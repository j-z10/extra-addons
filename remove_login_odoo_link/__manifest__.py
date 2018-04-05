# -*- coding: utf-8 -*-
{
    'name': "remove_login_odoo_link",

    'summary': """移除登陆界面的Powered by Odoo的链接, 以及页面Odoo title""",

    'description': """
    
- 移除登陆界面的Powered by Odoo的链接；
    
- 如果只有一个公司，使用公司名字作为页面的title；

- 如果有多个公司，可以添加ir.config_parameter参数, key 为 main.company_name, value 为 具体的名字；
    """,

    'author': "ZhangJie",
    'website': "https://github.com/JZ10UJS",

    'category': 'Tools',
    'version': '0.1',

    'depends': ['web'],

    'data': [
        'templates.xml',
    ],
}