from odoo import http
from odoo.http import request
import io
import xlsxwriter
from datetime import timedelta, date

def chunk_dates_by_3_months(dates):
    chunks = []
    current_chunk = []
    current_month = None
    month_count = 0

    for d in dates:
        if current_month is None:
            current_month = d.month

        if d.month != current_month:
            month_count += 1
            current_month = d.month

        if month_count == 3:
            chunks.append(current_chunk)
            current_chunk = []
            month_count = 0

        current_chunk.append(d)

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

class PmGanttExcel(http.Controller):

    @http.route('/pm_gantt/export_excel/<int:project_id>', type='http', auth="user")
    def export_excel(self, project_id):

        project = request.env['pm.project'].sudo().browse(project_id)

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet("Gantt")

        # ================= FORMAT =================
        header = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'middle',
            'border': 1
        })

        center = workbook.add_format({
            'align': 'center',
            'valign': 'middle',
            'border': 1
        })

        bold_center = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'middle',
            'border': 1
        })

        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'center',
            'valign': 'middle'
        })

        bar_green_parent = workbook.add_format({
            'bg_color': '#15803d',
            'border': 1
        })

        bar_green_child = workbook.add_format({
            'bg_color': '#22c55e',
            'border': 1
        })

        empty_cell = workbook.add_format({'border': 1})

        # ================= AMBIL DATA =================
        root_tasks = project.task_ids.filtered(lambda t: not t.parent_id).sorted('id')
        ordered = project._generate_wbs(root_tasks)

        tasks = [(t, num) for t, num in ordered if t.start_date and t.end_date]

        if not tasks:
            return

        # ================= RANGE TANGGAL =================
        min_date = min(t.start_date for t, _ in tasks)
        max_date = max(t.end_date for t, _ in tasks)

        dates = []
        d = min_date
        while d <= max_date:
            dates.append(d)
            d += timedelta(days=1)

        headers = ["WBS", "Task", "Start", "End", "Dur"]

        total_cols = len(headers) + len(dates)

        # ================= TITLE =================
        sheet.merge_range(0, 0, 0, total_cols - 1, project.name or "Project Timeline", title_format)

        # ================= HEADER ROW =================
        sheet.set_row(0, 30)
        sheet.set_row(1, 25)
        sheet.set_row(2, 25)

        # HEADER KIRI (MERGE 2 BARIS)
        for col, h in enumerate(headers):
            sheet.merge_range(1, col, 2, col, h, header)

        # LEBAR KOLOM
        sheet.set_column(0, 0, 10)
        sheet.set_column(1, 1, 22)
        sheet.set_column(2, 3, 18)
        sheet.set_column(4, 4, 8)

        # ================= HEADER BULAN + TANGGAL =================
        col_offset = len(headers)
        current_month = None
        month_start_col = col_offset

        for i, d in enumerate(dates):
            col = col_offset + i
            month_name = d.strftime("%B")

            # tanggal
            sheet.write(2, col, d.strftime("%d"), header)
            sheet.set_column(col, col, 4)

            # handle merge bulan
            if current_month is None:
                current_month = month_name
                month_start_col = col
            elif month_name != current_month:
                sheet.merge_range(1, month_start_col, 1, col - 1, current_month, header)
                current_month = month_name
                month_start_col = col

        # merge bulan terakhir
        sheet.merge_range(1, month_start_col, 1, col_offset + len(dates) - 1, current_month, header)

        # ================= DATA =================
        row = 3

        for t, number in tasks:

            start = t.start_date
            end = t.end_date
            duration = (end - start).days + 1

            level = number.count('.')

            if level == 0:
                sheet.set_row(row, 28)

                # 🔥 SEMUA KOLOM BOLD
                sheet.write(row, 0, number, bold_center)
                sheet.write(row, 1, t.name, bold_center)
                sheet.write(row, 2, start.strftime('%Y-%m-%d'), bold_center)
                sheet.write(row, 3, end.strftime('%Y-%m-%d'), bold_center)
                sheet.write(row, 4, duration, bold_center)

                bar_format = bar_green_parent

            else:
                sheet.set_row(row, 20)

                sheet.write(row, 0, number, center)
                sheet.write(row, 1, t.name, center)
                sheet.write(row, 2, start.strftime('%Y-%m-%d'), center)
                sheet.write(row, 3, end.strftime('%Y-%m-%d'), center)
                sheet.write(row, 4, duration, center)

                bar_format = bar_green_child

            # BAR
            for col, d in enumerate(dates):
                if start <= d <= end:
                    sheet.write(row, col + len(headers), "", bar_format)
                else:
                    sheet.write(row, col + len(headers), "", empty_cell)

            row += 1

        # ================= FREEZE =================
        sheet.freeze_panes(3, len(headers))

        workbook.close()
        output.seek(0)

        return request.make_response(
            output.read(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', 'attachment; filename=gantt.xlsx')
            ]
        )
    
def build_timeline_pdf(project):

    root_tasks = project.task_ids.filtered(
        lambda t: not t.parent_id
    ).sorted("id")

    ordered = project._generate_wbs(root_tasks)

    tasks = [
        (t, num)
        for t, num in ordered
        if t.start_date and t.end_date
    ]

    if not tasks:
        return None

    today = date.today()

    current_week = 1
    week_range = "-"
    remaining_days = 0

    if project.start_date and project.end_date:

        if today >= project.start_date:
            diff = (today - project.start_date).days
            current_week = (diff // 7) + 1

        week_start_date = project.start_date + timedelta(
            days=(current_week - 1) * 7
        )

        week_end_date = week_start_date + timedelta(days=6)

        if week_end_date > project.end_date:
            week_end_date = project.end_date

        week_range = (
            f"{week_start_date.strftime('%d/%m/%Y')} - "
            f"{week_end_date.strftime('%d/%m/%Y')}"
        )

        remaining_days = max(
            (project.end_date - today).days,
            0
        )

    min_date = min(t.start_date for t, _ in tasks)
    max_date = max(t.end_date for t, _ in tasks)

    dates = []
    d = min_date

    while d <= max_date:
        dates.append(d)
        d += timedelta(days=1)

    task_map = []

    for t, num in tasks:
        level = num.count(".")

        task_map.append({
            "task": t,
            "wbs": num,
            "level": level,
            "is_parent": level == 0,
            "dates": [
                t.start_date <= d <= t.end_date
                for d in dates
            ],
        })

    date_chunks = chunk_dates_by_3_months(dates)

    html_list = []

    for chunk in date_chunks:

        chunk_task_map = []

        for row in task_map:
            new_row = row.copy()

            new_row["dates"] = [
                row["task"].start_date <= d <= row["task"].end_date
                for d in chunk
            ]

            chunk_task_map.append(new_row)

        months_chunk = []
        current_month = None
        count = 0

        for d in chunk:
            month_name = d.strftime("%B")

            if current_month is None:
                current_month = month_name
                count = 1

            elif month_name == current_month:
                count += 1

            else:
                months_chunk.append({
                    "name": current_month,
                    "span": count,
                })

                current_month = month_name
                count = 1

        months_chunk.append({
            "name": current_month,
            "span": count,
        })

        html_list.append(
            request.env["ir.ui.view"]._render_template(
                "pm_gantt.gantt_pdf_template",
                {
                    "project": project,
                    "dates": chunk,
                    "task_map": chunk_task_map,
                    "months": months_chunk,
                    "current_week": current_week,
                    "week_range": week_range,
                    "remaining_days": remaining_days,
                }
            )
        )

    report_action = request.env.ref(
        "pm_gantt.action_gantt_pdf_a3_internal"
    ).sudo()

    return report_action._run_wkhtmltopdf(
        html_list,
        landscape=True,
        specific_paperformat_args={
            "data-report-margin-top": 5,
            "data-report-margin-bottom": 5,
            "data-report-header-spacing": 0,
        }
    )

class PmGanttPDF(http.Controller):

    @http.route(
        "/pm_gantt/export_pdf/<int:project_id>",
        type="http",
        auth="user"
    )
    def export_pdf(self, project_id):

        project = request.env["pm.project"].sudo().browse(project_id)

        if not project.exists():
            return request.not_found()

        pdf = build_timeline_pdf(project)

        if not pdf:
            return request.not_found()

        return request.make_response(
            pdf,
            headers=[
                ("Content-Type", "application/pdf"),
                (
                    "Content-Disposition",
                    f"attachment; filename={project.name}.pdf"
                ),
            ]
        )
