from odoo import http
from odoo.http import request
import json


class PmGantt(http.Controller):

    def _get_actual(self, task):
        # 🔥 recursive ambil leaf
        if task.child_ids:
            return sum(self._get_actual(child) for child in task.child_ids)
        return float(task.progress or 0)

    @http.route('/pm_gantt/get_data/<int:project_id>', type='http', auth="user")
    def get_gantt_json(self, project_id):

        project = request.env['pm.project'].sudo().browse(project_id)

        if not project.exists():
            return request.make_response("[]", headers=[('Content-Type', 'application/json')])

        # 🔥 WBS TREE
        root_tasks = project.task_ids.filtered(lambda t: not t.parent_id).sorted('id')
        ordered = project._generate_wbs(root_tasks)

        gantt_data = []

        for t, number in ordered:

            if not (t.start_date and t.end_date):
                continue

            start = t.start_date
            end = t.end_date
            duration = (end - start).days + 1

            weight = float(t.weight or 0)

            # 🔥 FIX UTAMA (recursive)
            actual_value = self._get_actual(t)

            sisa = max(
                weight - actual_value,
                0
            )
            
            if weight == 0 and sisa == 0:
                progress_percent = 100
            elif weight > 0:
                progress_percent = (
                    actual_value / weight
                ) * 100
            else:
                progress_percent = 0

            gantt_data.append({
                "id": str(t.id),
                "name": t.name,
                "wbs": number,
                "level": number.count('.'),

                "start": start.strftime('%Y-%m-%d'),
                "end": end.strftime('%Y-%m-%d'),
                "duration": duration,

                "progress": progress_percent,
                "weight": weight,
                "actual": actual_value,
                "sisa": sisa,

                "has_child": bool(t.child_ids),
                "pic": t.pic_id.name if t.pic_id else "-",
            })

        return request.make_response(
            json.dumps(gantt_data),
            headers=[('Content-Type', 'application/json')]
        )