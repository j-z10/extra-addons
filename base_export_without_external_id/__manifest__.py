# -*- coding: utf-8 -*-
{
    'name': "base_export_without_external_id",

    'summary': """导出时不导出外部ID""",

    'description': """导出时不导出外部ID, 导出大量数据时可节约大量的时间
    """,

    'author': "ZhangJie",

    'category': 'Tools',
    'version': '0.1',

    'depends': ['base'],

    'data': [
        'templates.xml',
    ],
    'qweb': [
        'static/src/export.xml',
    ]
}