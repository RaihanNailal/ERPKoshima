{
    'name': 'Project Task',
    'version': '1.0',
    'summary': 'Modul untuk mengelola tugas proyek',
    'category': 'Project Management',
    'depends': ['pm_project'],
    'data': [
        'security/ir.model.access.csv',
        'security/rule_task.xml',
        'views/task_view.xml',
    ],
    'installable': True,
}