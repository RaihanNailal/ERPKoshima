from odoo import models, fields
from datetime import timedelta, date

class PmProject(models.Model):
    _inherit = "pm.project"

    prepared_by = fields.Char(
        string="Prepared By"
    )

    acknowledged_by = fields.Char(
        string="Acknowledged By"
    )

    checked_by = fields.Char(
        string="Checked By"
    )

    approved_by = fields.Char(
        string="Approved By"
    )

    prepared_company = fields.Char(
        string="Prepared Company"
    )

    acknowledged_company = fields.Char(
        string="Acknowledged Company"
    )

    checked_company = fields.Char(
        string="Checked Company"
    )

    approved_company = fields.Char(
        string="Approved Company"
    )

    weekly_table_ids = fields.One2many(
        "pm.weekly.table",
        "project_id",
        string="Weekly Tables",
    )

    mcu_process = fields.Integer(default=0)
    
    input_berkas = fields.Integer(default=0)
    
    induction_process = fields.Integer(default=0)
    
    id_card_process = fields.Integer(default=0)
    
    id_card = fields.Integer(default=0)
    
    waskat = fields.Integer(default=0)

    manpower_note = fields.Text(
        string="Manpower Note"
    )

    last_week = fields.Float(
        string="Last Week",
        digits=(16, 2),
        default=0.0,
    )

    this_week = fields.Float(
        string="This Week",
        digits=(16, 2),
        default=0.0,
    )

    accumulative = fields.Float(
        string="Accumulative",
        digits=(16, 2),
        default=0.0,
    )

    safety_activity_ids = fields.One2many(
        "pm.safety.activity",
        "project_id",
        string="Safety Activities",
    )

    general_work_ids = fields.One2many(
        "pm.general.work",
        "project_id",
        string="General Works",
    )

    activity_schedule_ids = fields.One2many(
        "pm.activity.schedule",
        "project_id",
        string="Activity Schedules",
    )

    photo_ids = fields.One2many(
        "pm.weekly.report.photo",
        "project_id",
        string="Documentation Photos",
    )

    def get_weekly_overview(self):

        self.ensure_one()

        scurve = self.get_scurve_data(self.id)

        current_week = (
            scurve.get("current_week") or 1
        )

        tasks = (
            scurve.get("tasks") or []
        )

        result = []

        grand_weight = 0
        grand_plan = 0
        grand_actual = 0

        for task in tasks:

            weekly = (
                task.get("weekly") or []
            )[:current_week]

            total_plan = sum(
                w.get("plan", 0)
                for w in weekly
            )

            total_actual = sum(
                w.get("actual", 0)
                for w in weekly
            )

            deviation = (
                total_actual - total_plan
            )

            # =========================
            # STATUS
            # =========================

            if total_actual < total_plan:
                note = "On Progress"

            else:
                note = "Done"

            weight = round(
                task.get("weight", 0),
                2
            )

            plan = round(total_plan, 2)

            actual = round(total_actual, 2)

            grand_weight += weight
            grand_plan += plan
            grand_actual += actual

            result.append({

                "no":
                    task.get("no"),

                "description":
                    task.get("name"),

                "weight":
                    weight,

                "plan":
                    plan,

                "actual":
                    actual,

                "deviation":
                    round(deviation, 2),

                "note":
                    note,
            })

        # =========================
        # GRAND TOTAL
        # =========================

        result.append({

            "no": "",

            "description":
                "Grand Total",

            "weight":
                round(grand_weight, 2),

            "plan":
                round(grand_plan, 2),

            "actual":
                round(grand_actual, 2),

            "deviation":
                round(
                    grand_actual - grand_plan,
                    2
                ),

            "note":
                "",

            "is_total":
                True,
        })

        return result
    
    # =========================
    # TIMELINE DATA
    # =========================

    def get_timeline_data(self):

        self.ensure_one()

        root_tasks = self.task_ids.filtered(
            lambda t: not t.parent_id
        ).sorted("id")

        ordered = self._generate_wbs(root_tasks)

        if not ordered:
            return {
                "months": [],
                "dates": [],
                "tasks": [],
            }

        all_dates = []

        for task, number in ordered:

            if task.start_date and task.end_date:

                current = task.start_date

                while current <= task.end_date:
                    all_dates.append(current)
                    current += timedelta(days=1)

        if not all_dates:
            return {
                "months": [],
                "dates": [],
                "tasks": [],
            }

        start_date = min(all_dates)
        end_date = max(all_dates)

        dates = []
        current = start_date

        while current <= end_date:
            dates.append(current)
            current += timedelta(days=1)

        # =========================
        # MONTH HEADER
        # =========================

        months = []
        current_month = None
        span = 0

        for d in dates:

            month_name = d.strftime("%B")

            if current_month == month_name:
                span += 1
            else:

                if current_month:
                    months.append({
                        "name": current_month,
                        "span": span,
                    })

                current_month = month_name
                span = 1

        if current_month:
            months.append({
                "name": current_month,
                "span": span,
            })

        # =========================
        # TASK ROWS
        # =========================

        rows = []

        for task, number in ordered:

            if not task.start_date or not task.end_date:
                continue

            row_dates = []

            for d in dates:

                active = (
                    task.start_date <= d <= task.end_date
                )

                row_dates.append(active)

            rows.append({
                "wbs": number,
                "name": task.name,
                "start": task.start_date,
                "end": task.end_date,
                "duration": (
                    task.end_date - task.start_date
                ).days + 1,
                "dates": row_dates,
                "is_parent": bool(task.child_ids),
                "level": number.count("."),
            })

        return {
            "months": months,
            "dates": dates,
            "tasks": rows,
        }
    
    def _chunk_dates_by_3_months(self, dates):
        chunks = []
        chunk = []
        month_keys = []

        for d in dates:
            month_key = (d.year, d.month)

            if month_key not in month_keys:
                if len(month_keys) >= 3:
                    chunks.append(chunk)
                    chunk = []
                    month_keys = []

                month_keys.append(month_key)

            chunk.append(d)

        if chunk:
            chunks.append(chunk)

        return chunks


    def get_weekly_timeline_chunks(self):
        self.ensure_one()

        root_tasks = self.task_ids.filtered(
            lambda t: not t.parent_id
        ).sorted("id")

        ordered = self._generate_wbs(root_tasks)

        tasks = [
            (task, number)
            for task, number in ordered
            if task.start_date and task.end_date
        ]

        if not tasks:
            return []

        min_date = min(task.start_date for task, number in tasks)
        max_date = max(task.end_date for task, number in tasks)

        dates = []
        current = min_date

        while current <= max_date:
            dates.append(current)
            current += timedelta(days=1)

        date_chunks = self._chunk_dates_by_3_months(dates)

        result = []

        for chunk in date_chunks:
            months = []
            current_month = None
            span = 0

            for d in chunk:
                month_name = d.strftime("%B")

                if current_month == month_name:
                    span += 1
                else:
                    if current_month:
                        months.append({
                            "name": current_month,
                            "span": span,
                        })

                    current_month = month_name
                    span = 1

            if current_month:
                months.append({
                    "name": current_month,
                    "span": span,
                })

            rows = []

            for task, number in tasks:
                rows.append({
                    "wbs": number,
                    "name": task.name,
                    "start": task.start_date,
                    "end": task.end_date,
                    "duration": (task.end_date - task.start_date).days + 1,
                    "dates": [
                        task.start_date <= d <= task.end_date
                        for d in chunk
                    ],
                    "is_parent": bool(task.child_ids),
                    "level": number.count("."),
                })

            result.append({
                "months": months,
                "dates": chunk,
                "tasks": rows,
            })

        return result
    
    # =========================
    # OPEN REPORT
    # =========================

    def action_open_weekly_report(self):

        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "pm_weekly_report.weekly_report_action",
            "target": "current",
            "params": {
                "project_id": self.id,
            },
        }
    
    def action_export_pdf(self):
        self.ensure_one()

        return {
            "type": "ir.actions.act_url",
            "url": "/pm_report/weekly_export_pdf/%s" % self.id,
            "target": "self",
        }
    
    def get_weekly_report_pdf_data(self):
        self.ensure_one()

        schedules = {
            "last_week": [],
            "this_week": [],
            "next_week": [],
        }

        for schedule in self.activity_schedule_ids:
            schedules[schedule.category] = schedule.line_ids

        period = self.get_weekly_period_data()

        return {
            "project": self,
            "tables": self.weekly_table_ids,
            "safety": self.safety_activity_ids,
            "issues": self.env["pm.issue"].search([
                ("project_id", "=", self.id),
                ("is_client_visible", "=", True),
            ]),
            "general": self.general_work_ids,
            "overview": self.get_weekly_overview(),
            "timeline": self.get_timeline_data(),
            "timeline_chunks": self.get_weekly_timeline_chunks(),
            "photos": self.photo_ids,
            "schedules": schedules,

            "current_week": period["current_week"],
            "period_start": period["period_start"],
            "period_end": period["period_end"],
            "today": period["today"],
        }
    
    def get_weekly_period_data(self):
        self.ensure_one()

        if not self.start_date:
            return {
                "current_week": 1,
                "period_start": None,
                "period_end": None,
                "today": date.today(),
            }

        start_date = self.start_date
        today = date.today()

        diff_days = (today - start_date).days

        current_week = (diff_days // 7) + 1

        if current_week < 1:
            current_week = 1

        period_start = start_date + timedelta(
            days=(current_week - 1) * 7
        )

        period_end = period_start + timedelta(days=6)

        return {
            "current_week": current_week,
            "period_start": period_start,
            "period_end": period_end,
            "today": today,
        }