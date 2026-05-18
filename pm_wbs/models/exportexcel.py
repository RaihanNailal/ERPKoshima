from odoo import models
import io
import base64
import xlsxwriter

class ProjectExport(models.Model):
    _inherit = 'pm.project'


    def action_export_wbs_excel(self):
        self.ensure_one()
        data = self.get_wbs_data()

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet('WBS')

        # ================= STYLE =================
        header = workbook.add_format({
            'bold': True, 'border': 1,
            'align': 'center', 'valign': 'middle'
        })

        cell = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'middle',
            'text_wrap': True
        })

        percent = workbook.add_format({
            'border': 1,
            'num_format': '0.00%',
            'align': 'center',
            'valign': 'middle',
            'text_wrap': True
        })

        bold = workbook.add_format({
            'bold': True,
            'border': 1,
            'align': 'center',
            'valign': 'middle',
            'text_wrap': True 
        })

        total_fmt = workbook.add_format({
            'bold': True,
            'border': 1,
            'align': 'center',
            'valign': 'middle',
            'bg_color': '#e5e7eb',
            'text_wrap': True
        })

        red_percent = workbook.add_format({
            'border': 1,
            'num_format': '0.00%',
            'align': 'center',
            'valign': 'middle',
            'font_color': 'red',
            'text_wrap': True
        })

        green_text = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'middle',
            'font_color': 'green',
            'bold': True,
            'text_wrap': True
        })

        bold_percent = workbook.add_format({
            'bold': True,
            'border': 1,
            'num_format': '0.00%',
            'align': 'center',
            'valign': 'middle',
            'text_wrap': True
        })

        bold_red = workbook.add_format({
            'bold': True,
            'border': 1,
            'num_format': '0.00%',
            'align': 'center',
            'valign': 'middle',
            'font_color': 'red',
            'text_wrap': True
        })

        total_percent = workbook.add_format({
            'bold': True,
            'border': 1,
            'num_format': '0.00%',
            'align': 'center',
            'valign': 'middle',
            'bg_color': '#e5e7eb',
            'text_wrap': True
        })

        bold_left_gray = workbook.add_format({
            'bold': True,
            'border': 1,
            'align': 'left',
            'valign': 'middle',
            'indent': 1,
            'bg_color': '#e5e7eb'   # 🔥 ini yang bikin abu-abu
        })

        bold_percent_gray = workbook.add_format({
            'bold': True,
            'border': 1,
            'num_format': '0.00%',
            'align': 'center',
            'valign': 'middle',
            'bg_color': '#e5e7eb'
        })

        bold_red_gray = workbook.add_format({
            'bold': True,
            'border': 1,
            'num_format': '0.00%',
            'align': 'center',
            'valign': 'middle',
            'font_color': 'red',
            'bg_color': '#e5e7eb'
        })

        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'center',
            'valign': 'middle'
        })

        level_formats = []
        for i in range(6):
            fmt = workbook.add_format({
                'border': 1,
                'align': 'left',
                'valign': 'middle',
                'indent': i,
                'font_size': 11 if i == 0 else 9,
                'bold': True if i == 0 else False  # 🔥 parent bold
            })
            level_formats.append(fmt)

        # ================= TITLE =================
        total_columns = 4 + len(data['weeks']) + 4

        sheet.merge_range(0, 0, 0, total_columns - 1,
                        f"WBS - {self.name}", title_format)
        
        # ================= HEADER =================
        sheet.merge_range(1, 0, 2, 0, 'WBS', header)
        sheet.merge_range(1, 1, 2, 1, 'Task', header)
        sheet.merge_range(1, 2, 2, 2, 'Weight', header)
        sheet.merge_range(1, 3, 2, 3, 'Prog', header)

        col = 4
        for w in data['weeks']:
            sheet.write(1, col, w['label'], header)
            sheet.write(2, col, w.get('date', ''), header)
            col += 1

        sheet.merge_range(1, col, 2, col, 'Keterangan', header); col += 1
        sheet.merge_range(1, col, 2, col, 'Engineer', header); col += 1
        sheet.merge_range(1, col, 2, col, 'Start', header); col += 1
        sheet.merge_range(1, col, 2, col, 'End', header)

        # ================= DATA =================
        row = 3
        PARENT_HEIGHT = 20
        CHILD_HEIGHT = 16

        for t in data['tasks']:
            level = t.get('level', 0)
            task_fmt = level_formats[min(level, 5)]

            if level == 0:
                sheet.set_row(row, PARENT_HEIGHT)
                sheet.set_row(row+1, PARENT_HEIGHT)
            else:
                sheet.set_row(row, CHILD_HEIGHT)
                sheet.set_row(row+1, CHILD_HEIGHT)

            # merge utama
            sheet.merge_range(row, 0, row+1, 0, t['wbs'], cell)
            sheet.merge_range(row, 1, row+1, 1, t['name'], task_fmt)
            sheet.merge_range(row, 2, row+1, 2, t['weight']/100, percent)

            # ===== SCH =====
            col = 3
            sheet.write(row, col, 'SCH', bold); col += 1

            for w in t['weeks']:
                sheet.write(row, col, w.get('plan', 0)/100, percent)
                col += 1

            # ===== KETERANGAN =====
            ket = t.get('keterangan', '')

            if isinstance(ket, (int, float)):
                ket_fmt = red_percent if ket < 0 else percent
                sheet.merge_range(row, col, row+1, col, ket/100, ket_fmt)
            elif isinstance(ket, str) and ket.lower() == 'done':
                sheet.merge_range(row, col, row+1, col, ket, green_text)
            else:
                sheet.merge_range(row, col, row+1, col, ket, cell)

            col += 1

            sheet.merge_range(row, col, row+1, col, t.get('pic', ''), cell); col += 1
            sheet.merge_range(row, col, row+1, col, str(t.get('start_date', '')), cell); col += 1
            sheet.merge_range(row, col, row+1, col, str(t.get('end_date', '')), cell)

            # ===== ACT =====
            row += 1
            col = 3
            sheet.write(row, col, 'ACT', bold); col += 1

            for w in t['weeks']:
                sheet.write(row, col, w.get('actual', 0)/100, percent)
                col += 1

            row += 1

        # ================= GRAND TOTAL =================
        total_weight = sum([
            t.get('weight', 0)
            for t in data['tasks']
            if t.get('level', 0) == 0
        ])

        # kolom WBS kosong tapi tetap ada garis
        sheet.write(row, 0, '', total_fmt)

        # tulis GRAND TOTAL di kolom Task (rata kiri)
        sheet.write(row, 1, 'GRAND TOTAL', bold_left_gray)

        # kolom weight
        sheet.write(row, 2, total_weight/100, total_percent)

        # kosongkan kolom lainnya biar garis tetap full
        col = 3
        max_col = 4 + len(data['weeks']) + 4

        while col < max_col:
            sheet.write(row, col, '', total_fmt)
            col += 1

        # kosongkan sisanya
        col = 3
        max_col = 4 + len(data['weeks']) + 4
        while col < max_col:
            sheet.write(row, col, '', total_fmt)
            col += 1

        row += 1

        # ================= SUMMARY =================
        summary_titles = [
            ('TARGET PENCAPAIAN', 'plan'),
            ('TARGET KUMULATIF', 'plan_cum'),
            ('REALISASI PENCAPAIAN', 'actual'),
            ('REALISASI KUMULATIF', 'actual_cum'),
            ('SELISIH (+/-)', 'deviation')
        ]

        for title, key in summary_titles:
            sheet.write(row, 0, '', total_fmt)
            sheet.merge_range(row, 1, row, 3, title, bold_left_gray)

            col = 4
            for s in data['summary']:
                val = s.get(key, 0)

                fmt = bold_red_gray if key == 'deviation' else bold_percent_gray

                sheet.write(row, col, val/100, fmt)
                col += 1

            row += 1

        # ================= WIDTH =================
        sheet.set_column(0, 0, 6)
        sheet.set_column(1, 1, 30)
        sheet.set_column(2, 20, 12)

        sheet.freeze_panes(3, 0)

        workbook.close()
        output.seek(0)

        file_data = base64.b64encode(output.read())

        attachment = self.env['ir.attachment'].create({
            'name': f'WBS_{self.name}.xlsx',
            'type': 'binary',
            'datas': file_data,
            'res_model': 'pm.project',
            'res_id': self.id,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
    
    def action_print_wbs(self):
        self.ensure_one()
        return self.env.ref('pm_wbs.action_report_wbs').report_action(self)