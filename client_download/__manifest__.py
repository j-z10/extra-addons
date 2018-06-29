{
    'name': 'client_download',
    'version': '1.0',
    'category': 'Extra Tools',
    'description': """
download current page of list view data to csv file
""",
    'depends': ['web'],
    'data': [
        'views/templates.xml',
    ],
    'qweb': [
        'static/src/*.xml',
    ],
    'installable': True,
}
