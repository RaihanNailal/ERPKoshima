{
    'name': 'PM Weekly Report',
    'version': '1.0',

    'depends': [
        'pm_core',
        'pm_project',
        'pm_wbs',
        'pm_issue',
        'pm_scurve',
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/report_menu.xml',
        'views/weekly_report_pdf.xml',
        'views/weekly_report_template.xml',
         'views/dokumentasi_template.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'pm_report/static/src/js/weekly_report.js',
            'pm_report/static/src/xml/weekly_report.xml',
            'pm_report/static/src/scss/weekly_report.scss',
        ],
    },

    'installable': True,
}