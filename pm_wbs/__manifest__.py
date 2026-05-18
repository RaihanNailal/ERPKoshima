{
    'name': 'PM WBS',
    'version': '1.0',
    'depends': ['pm_project', 'pm_task', 'web'],
    'data': [
        'views/wbs_menu.xml',
        'views/reportwbs.xml',
        'security/ir.model.access.csv',
        'security/rule_wbs.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'pm_wbs/static/src/js/wbs_main.js',
            'pm_wbs/static/src/js/init.js',
            'pm_wbs/static/src/xml/wbs_main.xml',
            'pm_wbs/static/src/lib/wbs.css',
        ],
    },
    'installable': True,
}