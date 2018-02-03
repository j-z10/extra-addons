# -*- coding: utf-8 -*-
{
    'name': "field_widget",

    'summary': """一些特殊需求的widget，
    list view的限制长度显示字段， 
    form view将小数转换成百分比显示""",

    'description': """
    支持在list view 中使用：
        <field name='name' widget='limited_char' options='{"limit": 12}'/>  
        最长显示12个字符，鼠标移动上去时，显示原始数据的tooltip，作用于char, text字段;
        
    list, form view都可使用：    
        <field name='float_value' widget='percent'/> 
        将小数用百分比的形式显示出来，编辑时回到小数显示, 作用于float字段;
        可配合digits同时使用<field name='float_value' widget='percent' digits='[5,4]'/>
        此时编辑状态可以输入'0.1234', 保存后显示为 '12.34%';
    """,

    'author': "ZhangJie",

    'category': 'Tools',
    'version': '0.1',

    'depends': ['web'],

    'data': [
        'templates.xml',
    ],
}