{
    'name': 'My Project',
    'version': '1.1',
    'category': 'Project Management',
    'summary': 'Aplikasi Utama untuk Manajemen Proyek',
    'depends': ['base', 'pm_core', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'security/rules_project.xml',
        'views/project_menus.xml',
    ],
    'application': True,
    'installable': True,
}