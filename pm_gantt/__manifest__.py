{
    'name': "PM Gantt Chart",
    'category': 'Project',
    'version': '1.0',
    'depends': ['pm_project', 'pm_task', 'web'],
    'data': [
        'views/gantt_views.xml',
        'views/pdf.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'pm_gantt/static/src/lib/frappe-gantt.css',
            'pm_gantt/static/src/lib/frappe-gantt.min.js',
            'pm_gantt/static/src/js/gantt_renderer.js',
            'pm_gantt/static/src/xml/gantt_template.xml',
        ],
    },
    'installable': True,
}