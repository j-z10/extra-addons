# coding: utf-8
{
    'name': 'Lodop Tools',
    'category': 'Tools',
    'author': 'Zhang Jie',
    'website': 'https://github.com/JZ10UJS/extra-addons',
    'version': '0.1',
    'description':
        """
Lodop 定制
===========================
1. 支持使用Lodop打印
        """,
    'depends': ['web'],
    'installable': True,
    'application': True,
    'data': [
        'templates.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
}
