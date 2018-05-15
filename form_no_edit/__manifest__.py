# -*- coding: utf-8 -*-
{
    'name': "form_no_edit",

    'summary': """
        某些情况下，form view不出现编辑按钮""",

    'description': """
        例如：某record的state字段值不为draft的时候，我们希望在这个record的form view中，不显示编辑按钮
        任意model的action window 的context字段设置
        <field name='context'>{'form_no_edit': [('state', '!=', 'draft')]}</field>
    """,

    'author': "ZhangJie",
    'category': 'Tools',
    'version': '0.1',

    'depends': ['web'],
    'data': [
        'templates.xml',
    ],
}
