from odoo import models, fields
from datetime import timedelta

class Project(models.Model):
    _inherit = 'pm.project'

    def _generate_wbs(self, tasks, prefix=''):
        result = []
        index = 1

        for t in tasks:
            number = f"{prefix}{index}" if prefix else str(index)

            t.wbs_number = number
            result.append((t, number))

            if t.child_ids:
                result += self._generate_wbs(t.child_ids, prefix=number + '.')

            index += 1

        return result

    def _get_leaf_tasks(self):
        return self.task_ids.filtered(
        lambda t:
            not t.child_ids
            and not t.is_issue_task
            and t.active
        )

    def get_wbs_data(self):
        self.ensure_one()

        if not self.start_date or not self.end_date:
            return {
                'weeks': weeks or [],
                'tasks': tasks or [],
                'summary': summary or [],
                'total_weight': total_weight or 0,
            }

        # =========================
        # GENERATE WEEKS (FIX PARTIAL LAST WEEK)
        # =========================
        weeks = []
        current = self.start_date
        week_number = 1

        while current <= self.end_date:

            week_start = current
            week_end = current + timedelta(days=6)

            # 🔥 POTONG DI AKHIR PROJECT
            if week_end > self.end_date:
                week_end = self.end_date

            weeks.append({
                'label': f'W{week_number}',
                'date': week_start.strftime('%Y-%m-%d'),
                'end_date': week_end.strftime('%Y-%m-%d'),
            })

            current += timedelta(days=7)
            week_number += 1

        # =========================
        # PRELOAD WEEKLY (🔥 CORE FIX)
        # =========================
        Weekly = self.env['pm.wbs.task.week']

        all_weekly = Weekly.search([
            ('project_id', '=', self.id),
            ('active', '=', True)
        ])

        weekly_map = {}
        for w in all_weekly:
            weekly_map[(w.task_id.id, w.date)] = w

        # =========================
        # TOTAL PROJECT
        # =========================
        leaf_tasks = self._get_leaf_tasks()
        total_weight = sum(t.manual_weight or 0 for t in leaf_tasks)

        total_progress = 0
        if total_weight > 0:
            total_progress = sum(
                (t.progress or 0) * (t.weight or 0)
                for t in leaf_tasks
            ) / total_weight

        # =========================
        # WBS ORDER
        # =========================
        filtered_tasks = self.task_ids.filtered(
            lambda t: not t.is_issue_task and t.active
        )
        
        root_tasks = filtered_tasks.filtered(lambda t: not t.parent_id)
        ordered_tasks = self._generate_wbs(root_tasks)

        tasks = []

        # =========================
        # BUILD TASKS
        # =========================
        for t, number in ordered_tasks:

            # 🔥 weight
            weight = sum(c.weight or 0 for c in t.child_ids) if t.child_ids else (t.manual_weight or 0)

            # 🔥 progress
            if t.child_ids:
                progress = sum(c.progress or 0 for c in t.child_ids)
            else:
                progress = t.progress or 0

            row = {
                'id': t.id,
                'wbs': number,
                'name': t.name or '',
                'parent_id': t.parent_id.id if t.parent_id else False,
                'has_child': bool(t.child_ids),
                'pic_id': t.pic_id.id if t.pic_id else False,
                'pic': t.pic_id.name if t.pic_id else '',
                'progress': round(progress, 2),
                'weight': round(weight, 2),
                'start_date': t.start_date.strftime('%Y-%m-%d') if t.start_date else '',
                'end_date': t.end_date.strftime('%Y-%m-%d') if t.end_date else '',
                'level': number.count('.'),
                'weeks': []
            }

            # =========================
            # WEEK DATA (🔥 NO MORE SEARCH)
            # =========================
            for w in weeks:
                week_date = fields.Date.from_string(w['date'])

                if t.child_ids:
                    # parent → sum child
                    plan = sum(
                        (weekly_map.get((cid, week_date)).plan or 0)
                        for cid in t.child_ids.ids
                        if (cid, week_date) in weekly_map
                    )
                    actual = sum(
                        (weekly_map.get((cid, week_date)).actual or 0)
                        for cid in t.child_ids.ids
                        if (cid, week_date) in weekly_map
                    )
                else:
                    rec = weekly_map.get((t.id, week_date))
                    plan = rec.plan if rec else 0
                    actual = rec.actual if rec else 0

                row['weeks'].append({
                    'active': True,
                    'plan': round(plan, 4),
                    'actual': round(actual, 4),
                    'date': w['date'],
                })

            # =========================
            # KETERANGAN
            # =========================
            total_plan = sum(w['plan'] for w in row['weeks'])
            total_actual = sum(w['actual'] for w in row['weeks'])

            row['keterangan'] = (
                "Done" if abs(total_actual - total_plan) < 0.0001
                else round(total_actual - total_plan, 2)
            )

            tasks.append(row)

        # =========================
        # SUMMARY (PERBAIKAN TOTAL)
        # =========================
        summary = []
        cumulative_plan = 0
        cumulative_actual = 0

        # 1. Ambil ID dari leaf tasks saja (untuk menghindari double counting)
        leaf_task_ids = self._get_leaf_tasks().ids
        divisor = total_weight if total_weight > 0 else 100

        for w in weeks:
            week_date = fields.Date.from_string(w['date'])

            # 2. Filter: Hanya ambil record mingguan milik LEAF TASKS pada tanggal tersebut
            week_recs = all_weekly.filtered(
                lambda r: r.date == week_date and r.task_id.id in leaf_task_ids
            )

            plan_total = sum(r.plan or 0 for r in week_recs)
            actual_total = sum(r.actual or 0 for r in week_recs)

            cumulative_plan += plan_total
            cumulative_actual += actual_total

            # 3. Hitung Deviasi (Selisih)
            # Pastikan ini menghasilkan angka, bukan None
            current_dev = ((cumulative_actual - cumulative_plan) / divisor * 100)

            summary.append({
                'date': w['date'],
                'plan': (plan_total / divisor * 100),
                'actual': (actual_total / divisor * 100),
                'plan_cum': (cumulative_plan / divisor * 100),
                'actual_cum': (cumulative_actual / divisor * 100),
                'deviation': round(current_dev, 2),
            })

        return {
            'weeks': weeks,
            'tasks': tasks,
            'summary': summary,
            'total_weight': round(total_weight, 2),
            'total_progress': round(total_progress, 2)
        }
    
    