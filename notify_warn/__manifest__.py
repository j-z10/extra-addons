# -*- coding: utf-8 -*-
{
    'name': "notify_warn",
    'summary': """支持另一种提示方式""",
    'description': """
py file

```

def foo(self):
    # do sth

    return {
        'type': 'ir.actions.client',

        'tag': 'notify_warn',

        'params': {
            # 2 选 1

            'warn': {'title': 'warn title', 'message': 'warn message', 'sticky': True},
            
            'notify': {'title': 'notify title', 'message': 'notify message', 'sticky': False}
        },
    }
```
xml file

`<button name='foo' type='object'/>`
    """,
    'author': "Zhang Jie",
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': ['web'],
    # always loaded
    'data': [
        'templates.xml',
    ],
}