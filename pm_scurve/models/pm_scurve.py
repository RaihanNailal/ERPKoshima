from odoo import models, fields, api
from datetime import date


class PmProject(models.Model):
    _inherit = 'pm.project'

    # =========================
    # SIGNATURE
    # =========================

    sign_left_date = fields.Char(string="Tempat, Tanggal")
    sign_left_name = fields.Char(string="Nama (Kiri)")
    sign_left_position = fields.Char(string="Jabatan (Kiri)")
    sign_left_company = fields.Char(string="Perusahaan (Kiri)")
    sign_left_image = fields.Binary(string="Tanda Tangan (Kiri)")

    sign_right_name = fields.Char(string="Nama (Kanan)")
    sign_right_position = fields.Char(string="Jabatan (Kanan)")
    sign_right_company = fields.Char(string="Perusahaan (Kanan)")
    sign_right_image = fields.Binary(string="Tanda Tangan (Kanan)")

    # =========================
    # OPEN SCURVE
    # =========================

    def action_view_scurve(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.client',
            'tag': 'pm_scurve.scurve_js_action',
            'params': {
                'project_id': self.id,
                'project_name': self.name,
                'vendor': self.vendor,
                'po_number': self.po_number,
            }
        }

    # =========================
    # MAIN SCURVE DATA
    # =========================

    @api.model
    def get_scurve_data(self, project_id):

        project = self.env['pm.project'].sudo().browse(project_id)

        if not project.exists():
            return self._empty_result()

        # =========================
        # 🔥 SINGLE SOURCE OF TRUTH
        # =========================

        wbs_data = project.get_wbs_data() or {}

        weeks = wbs_data.get('weeks') or []

        wbs_tasks = (
            wbs_data.get('tasks') or []
        )

        main_tasks = [
            t for t in wbs_tasks
            if not t.get('parent_id')
        ]

        tasks_data = []

        summary = wbs_data.get('summary') or []

        total_weight = wbs_data.get('total_weight') or 0

        total_progress = wbs_data.get('total_progress') or 0

        for idx, task in enumerate(main_tasks, start=1):

            weekly = []

            for w in task.get('weeks', []):

                weekly.append({
                    'date': w.get('date'),
                    'plan': w.get('plan', 0),
                    'actual': w.get('actual', 0),
                })

            tasks_data.append({
                'id': task.get('id'),
                'no': idx,
                'name': task.get('name'),
                'weight': task.get('weight', 0),
                'progress': task.get('progress', 0),
                'weekly': weekly,
                'keterangan': task.get('keterangan', ''),
            })

        # =========================
        # WEEK HEADER
        # =========================

        weeks_header = [
            {
                'num': i,
                'date': w.get('date'),
                'label': w.get('label'),
            }
            for i, w in enumerate(weeks, start=1)
        ]

        # =========================
        # CURRENT WEEK
        # =========================

        today = fields.Date.today()

        current_week = 0

        if project.start_date:

            delta_days = (
                today - project.start_date
            ).days

            if delta_days >= 0:
                current_week = (
                    delta_days // 7
                ) + 1

        current_week = min(
            current_week,
            len(weeks)
        )

        # =========================
        # CHART DATA
        # =========================

        labels = []
        planned_data = []
        actual_data = []
        filtered_summary = []

        for i, s in enumerate(summary, start=1):

            labels.append(f"W{i}")

            plan = float(
                s.get('plan_cum', 0)
            )

            actual = float(
                s.get('actual_cum', 0)
            )

            deviation = float(
                s.get('deviation', 0)
            )

            planned_data.append(plan)
            actual_data.append(actual)

            row = dict(s)

            row['plan_cum'] = round(plan, 2)
            row['actual_cum'] = round(actual, 2)
            row['deviation'] = round(deviation, 2)

            filtered_summary.append(row)

        # =========================
        # PROJECT INFO
        # =========================

        start = project.start_date
        end = project.end_date

        remaining_days = 0

        if start and end:
            remaining_days = max(
                (end - today).days,
                0
            )

        # =========================
        # RETURN
        # =========================

        return {

            # =========================
            # CHART
            # =========================

            'labels': labels,

            'datasets': [
                {
                    'label': 'Schedule',
                    'data': planned_data
                },
                {
                    'label': 'Actual',
                    'data': actual_data
                }
            ],

            # =========================
            # TABLE
            # =========================

            'weeks_header': weeks_header,

            'tasks': tasks_data,

            'summary': filtered_summary,

            # =========================
            # TOTAL
            # =========================

            'total_weight': round(
                total_weight,
                2
            ),

            'total_progress': round(
                total_progress,
                2
            ),

            # =========================
            # PROJECT
            # =========================

            'project_name': project.name or "",

            'vendor': project.vendor or "",

            'po_number': project.po_number or "",

            'project_start': (
                start.strftime('%Y-%m-%d')
                if start else ""
            ),

            'project_end': (
                end.strftime('%Y-%m-%d')
                if end else ""
            ),

            'remaining_days': remaining_days,

            'current_week': current_week,

            # =========================
            # LOGO
            # =========================

            'logo_left': project.logo_left,

            'logo_right': project.logo_right,

            # =========================
            # SIGN LEFT
            # =========================

            'sign_left_date': (
                project.sign_left_date or ""
            ),

            'sign_left_name': (
                project.sign_left_name or ""
            ),

            'sign_left_position': (
                project.sign_left_position or ""
            ),

            'sign_left_company': (
                project.sign_left_company or ""
            ),

            'sign_left_image': (
                project.sign_left_image
            ),

            # =========================
            # SIGN RIGHT
            # =========================

            'sign_right_name': (
                project.sign_right_name or ""
            ),

            'sign_right_position': (
                project.sign_right_position or ""
            ),

            'sign_right_company': (
                project.sign_right_company or ""
            ),

            'sign_right_image': (
                project.sign_right_image
            ),
        }

    # =========================
    # EMPTY RESULT
    # =========================

    def _empty_result(self):

        return {
            'labels': [],
            'datasets': [],
            'weeks_header': [],
            'tasks': [],
            'summary': [],
            'logo_left': False,
            'logo_right': False,
        }

    # =========================
    # WRITE SIGNATURE
    # =========================

    @api.model
    def write_signature(
        self,
        project_id,
        field,
        value
    ):

        project = self.browse(project_id)

        if not project.exists():
            return False

        project.write({
            field: value
        })

        return True

    # =========================
    # EXPORT PDF
    # =========================

    def action_export_scurve_pdf(self):

        return self.env.ref(
            "pm_scurve.action_report_scurve"
        ).report_action(self)