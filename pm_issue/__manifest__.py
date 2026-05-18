{
    'name': 'PM Issue Register',
    'version': '1.0',
    'depends': ['pm_project', 'pm_task', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'security/rule_issue.xml',
        'data/sequence.xml',
        'views/report_issue.xml',
        'views/issue.xml',
        'views/asignwizard.xml',
    ],
    'installable': True,
}