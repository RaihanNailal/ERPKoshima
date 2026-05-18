{
    'name': 'PM S-Curve Analytics',
    'version': '1.0',
    'depends': ['pm_project', 'pm_wbs', 'web'],
    'data': [
        'views/pm_project_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'pm_scurve/static/src/lib/chart.umd.min.js',
            'pm_scurve/static/src/js/scurve_chart.js',
            'pm_scurve/static/src/xml/scurve_chart.xml',
            'pm_scurve/static/src/lib/curve.css',
            #'pm_scurve/static/src/lib/html2canvas.min.js',
            #'pm_scurve/static/src/lib/jspdf.umd.min.js',
        ],
    },
    'installable': True,
}