from odoo import http
from odoo.http import request
from odoo import fields
import io
import base64
import tempfile

from reportlab.platypus import *
from reportlab.lib import colors
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import utils
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Table

def build_scurve_reportlab_pdf(project, selected_week=None, page_size="A3"):

    data = project.get_scurve_data(project.id)

    if selected_week is None:
        selected_week = int(
            data.get("current_week", 1) or 1
        )

    tasks = data["tasks"]
    summary = data["summary"]
    weeks = data["weeks_header"]

    if page_size == "A4":
        report_page_size = landscape(A4)
        weeks_per_page = 12
        usable_width = 277 * mm
        left_margin = 10 * mm
        right_margin = 10 * mm
        top_margin = 10 * mm
        bottom_margin = 10 * mm

        no_w = 10 * mm
        task_w = 62 * mm
        bobot_w = 14 * mm
        prog_w = 11 * mm
        ket_w = 22 * mm
        min_week_w = 8 * mm

        sign_col_widths = [138 * mm, 138 * mm]

    else:
        report_page_size = landscape(A3)
        weeks_per_page = 20
        usable_width = 395 * mm
        left_margin = 5
        right_margin = 5
        top_margin = 15
        bottom_margin = 15

        no_w = 10 * mm
        task_w = 70 * mm
        bobot_w = 15 * mm
        prog_w = 12 * mm
        ket_w = 24 * mm
        min_week_w = 12 * mm

        sign_col_widths = [145 * mm, 145 * mm]

    week_chunks = [
        (
            start,
            weeks[start:start + weeks_per_page],
            summary[start:start + weeks_per_page],
        )
        for start in range(
            0,
            len(weeks),
            weeks_per_page,
        )
    ]

    def save_binary(binary_data):
        if not binary_data:
            return None

        path = tempfile.NamedTemporaryFile(
            suffix=".png",
            delete=False,
        ).name

        with open(path, "wb") as f:
            f.write(base64.b64decode(binary_data))

        return path

    logo_left = save_binary(data.get("logo_left"))
    logo_right = save_binary(data.get("logo_right"))

    week_plan = []
    week_actual = []

    for wi in range(len(weeks)):
        p = 0
        a = 0

        for t in tasks:
            p += float(t["weekly"][wi]["plan"])
            a += float(t["weekly"][wi]["actual"])

        week_plan.append(p)
        week_actual.append(a)

    buf = io.BytesIO()

    pdf = SimpleDocTemplate(
        buf,
        pagesize=report_page_size,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=top_margin,
        bottomMargin=bottom_margin,
    )

    styles = getSampleStyleSheet()
    story = []

    def fit_logo(path, max_w, max_h):
        if not path:
            return ""

        img = utils.ImageReader(path)
        iw, ih = img.getSize()

        ratio = min(
            max_w / iw,
            max_h / ih,
        )

        return Image(
            path,
            width=iw * ratio,
            height=ih * ratio,
        )

    left_logo = fit_logo(
        logo_left,
        75 * mm,
        25 * mm,
    )

    right_logo = fit_logo(
        logo_right,
        45 * mm,
        25 * mm,
    )

    header = Table(
        [[
            left_logo,
            Paragraph(
                "<para align='center'><font size=20><b>S-Curve</b></font></para>",
                styles["Normal"],
            ),
            right_logo,
        ]],
        colWidths=[
            130 * mm,
            135 * mm,
            130 * mm,
        ],
    )

    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("ALIGN", (2, 0), (2, 0), "RIGHT"),

        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    task_style = ParagraphStyle(
        "task_style",
        fontName="Helvetica",
        fontSize=8 if page_size == "A4" else 10,
        leading=8 if page_size == "A4" else 10,
        alignment=TA_LEFT,
        wordWrap="CJK",
    )

    summary_style = ParagraphStyle(
        "summary_style",
        fontName="Helvetica-Bold",
        fontSize=8 if page_size == "A4" else 10,
        leading=8 if page_size == "A4" else 10,
        alignment=1,
    )

    for page_no, (offset, weeks_chunk, summary_chunk) in enumerate(week_chunks):

        from datetime import timedelta

        current_week = selected_week
        week_label = f"W{current_week}"
        week_range = "-"

        if weeks and current_week and current_week <= len(weeks):

            wk = weeks[current_week - 1]
            dt = wk.get("date")

            if dt:
                if isinstance(dt, str):
                    dt = fields.Date.from_string(dt)

                week_start = dt.strftime("%d/%m/%Y")
                week_end_date = dt + timedelta(days=6)

                if project.end_date and week_end_date > project.end_date:
                    week_end_date = project.end_date

                week_end = week_end_date.strftime("%d/%m/%Y")
                week_range = f"{week_start} - {week_end}"

            # ================= HEADER =================

            header = Table(
                [[
                    left_logo,
                    Paragraph(
                        "<para align='center'><font size=20><b>S-Curve</b></font></para>",
                        styles["Normal"],
                    ),
                    right_logo,
                ]],
                colWidths=[
                    135 * mm,
                    125 * mm,
                    135 * mm,
                ],
            )

            header.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

                ("ALIGN", (0, 0), (0, 0), "LEFT"),
                ("ALIGN", (1, 0), (1, 0), "CENTER"),
                ("ALIGN", (2, 0), (2, 0), "RIGHT"),

                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))

            # ================= LEFT BLOCK =================

            left_block = Table([
                ["PEKERJAAN", ":", data.get("project_name", "")],
                ["PENYEDIA", ":", data.get("vendor", "")],
                ["NOMOR PO", ":", data.get("po_number", "")],
            ], colWidths=[30 * mm, 5 * mm, 95 * mm])

            # ================= CENTER BLOCK =================
            center_block = Table([
                ["", "MINGGU KE", ":", week_label],
                ["", "TANGGAL", ":", week_range],
            ], colWidths=[
                22 * mm,   # spacer kiri
                34 * mm,
                5 * mm,
                62 * mm,
            ])

            # ================= RIGHT BLOCK =================
            right_block = Table([
                ["START", ":", data.get("project_start", "")],
                ["END", ":", data.get("project_end", "")],
                ["REMAINING", ":", f'{data.get("remaining_days", 0)} HARI'],
            ], colWidths=[30 * mm, 5 * mm, 42 * mm])

            left_block.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 11),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ]))

            center_block.setStyle(TableStyle([
                ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 11),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ]))

            right_block.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 11),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),

                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),

                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]))

            # ================= FULL WIDTH INFO =================
            header_info = Table(
                [[left_block, center_block, right_block]],
                colWidths=[
                    150 * mm,
                    100 * mm,
                    145 * mm,
                ],
            )

            header_info.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),

                ("ALIGN", (0, 0), (0, 0), "LEFT"),
                ("ALIGN", (1, 0), (1, 0), "CENTER"),
                ("ALIGN", (2, 0), (2, 0), "RIGHT"),

                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),

                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))

            story.append(header)
            story.append(Spacer(1, 8))
            story.append(header_info)
            story.append(Spacer(1, 8))

            story.append(
                Table(
                    [[""]],
                    colWidths=[395 * mm],
                    style=[
                        ("LINEBELOW", (0, 0), (-1, -1), 0.6, colors.grey),
                    ],
                )
            )

            story.append(Spacer(1, 18))

        rows = []

        headers = ["NO", "TASK", "BOBOT", "PROG"]

        for w in weeks_chunk:
            headers.append(
                Paragraph(
                    f"""
                    <para align='center'>
                    <font color='white'><b>W{w['num']}</b></font><br/>
                    <font size=6 color='#cbd5f5'>({w['date']})</font>
                    </para>
                    """,
                    styles["Normal"],
                )
            )

        headers.append("KETERANGAN")
        rows.append(headers)

        for t in tasks:
            ket_raw = t.get("keterangan")

            if isinstance(ket_raw, str) and ket_raw.lower() == "done":
                ket = Paragraph(
                    """
                    <para align="center">
                    <font color="green">Done</font>
                    </para>
                    """,
                    summary_style,
                )
            else:
                ket = ""

            task_name = Paragraph(
                str(t["name"]),
                task_style,
            )

            sch = [
                t["no"],
                task_name,
                f'{t["weight"]}%',
                "SCH",
            ]

            act = ["", "", "", "ACT"]

            for wk in t["weekly"][offset:offset + weeks_per_page]:
                sch.append(f'{wk["plan"]:.2f}%')
                act.append(f'{wk["actual"]:.2f}%')

            sch.append(ket)
            act.append("")

            rows.append(sch)
            rows.append(act)

        rows.append(
            [
                "GRAND TOTAL",
                "",
                f"{data.get('total_weight', 100):.0f}%",
                "",
            ]
            + [""] * len(weeks_chunk)
            + [""]
        )

        rows.append(
            ["TARGET PENCAPAIAN", "", "", ""]
            + [
                f"{x:.2f}%"
                for x in week_plan[offset:offset + weeks_per_page]
            ]
            + [""]
        )

        rows.append(
            ["TARGET KUMULATIF", "", "", ""]
            + [
                f"{s['plan_cum']:.2f}%"
                for s in summary_chunk
            ]
            + [""]
        )

        rows.append(
            ["REALISASI PENCAPAIAN", "", "", ""]
            + [
                f"{x:.2f}%"
                for x in week_actual[offset:offset + weeks_per_page]
            ]
            + [""]
        )

        rows.append(
            ["REALISASI KUMULATIF", "", "", ""]
            + [
                f"{s['actual_cum']:.2f}%"
                for s in summary_chunk
            ]
            + [""]
        )

        dev_cells = []

        for i, s in enumerate(summary_chunk):
            global_index = offset + i

            if global_index < current_week:
                dev = float(s["deviation"])
                clr = "green" if dev >= 0 else "red"

                dev_cells.append(
                    Paragraph(
                        f'<para align="center"><font color="{clr}">{dev:.2f}%</font></para>',
                        summary_style,
                    )
                )
            else:
                dev_cells.append("")

        rows.append(
            ["SELISIH (+/-)", "", "", ""]
            + dev_cells
            + [""]
        )

        fixed = (
            no_w
            + task_w
            + bobot_w
            + prog_w
            + ket_w
        )

        week_w = max(
            min_week_w,
            (usable_width - fixed) / len(weeks_chunk),
        )

        col_widths = [
            no_w,
            task_w,
            bobot_w,
            prog_w,
        ]

        col_widths += [week_w] * len(weeks_chunk)
        col_widths.append(ket_w)

        spans = []

        for i in range(len(tasks)):
            r = 1 + i * 2

            spans += [
                ("SPAN", (0, r), (0, r + 1)),
                ("SPAN", (1, r), (1, r + 1)),
                ("SPAN", (2, r), (2, r + 1)),
                ("SPAN", (-1, r), (-1, r + 1)),
            ]

        page_current_week = max(
            0,
            min(
                selected_week - offset,
                len(summary_chunk),
            ),
        )

        tbl = OverlayTable(
            rows,
            colWidths=col_widths,
            repeatRows=1,
            summary=summary_chunk,
            current_week=page_current_week,
        )

        tbl.splitByRow = 1

        tbl.setStyle(TableStyle(spans + [
            ("GRID", (0, 0), (-1, -1), 0.35, colors.lightgrey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("SPAN", (0, -6), (1, -6)),
            ("SPAN", (0, -5), (3, -5)),
            ("SPAN", (0, -4), (3, -4)),
            ("SPAN", (0, -3), (3, -3)),
            ("SPAN", (0, -2), (3, -2)),
            ("SPAN", (0, -1), (3, -1)),
        ]))

        story.append(tbl)

        if page_no < len(week_chunks) - 1:
            story.append(PageBreak())

    story.append(Spacer(1, 25))

    left_date = data.get("sign_left_date", "")
    left_company = data.get("sign_left_company", "")
    left_name = data.get("sign_left_name", "")
    left_pos = data.get("sign_left_position", "")

    right_company = data.get("sign_right_company", "")
    right_name = data.get("sign_right_name", "")
    right_pos = data.get("sign_right_position", "")

    story.append(Spacer(1, 28))

    sign = Table(
        [[
            Paragraph(f"""
            <para align=center>
            {left_date}<br/><br/>
            Diajukan oleh,<br/><br/>
            {left_company}<br/><br/><br/><br/><br/>
            (_____________________)<br/>
            {left_name}<br/>
            {left_pos}
            </para>
            """, styles["Normal"]),

            Paragraph(f"""
            <para align=center>
            <br/><br/>
            Disetujui oleh,<br/><br/>
            {right_company}<br/><br/><br/><br/><br/>
            (_____________________)<br/>
            {right_name}<br/>
            {right_pos}
            </para>
            """, styles["Normal"]),
        ]],
        colWidths=sign_col_widths,
    )

    sign.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    story.append(sign)

    pdf.build(story)

    out = buf.getvalue()
    buf.close()

    return out

class OverlayTable(Table):

    SUMMARY_ROWS = 6

    def __init__(
        self,
        *args,
        summary=None,
        current_week=None,
        **kwargs
    ):

        super().__init__(*args, **kwargs)

        self.summary = summary or []

        if current_week is None:
            self.current_week = len(self.summary)
        else:
            self.current_week = current_week


    # =====================================
    # DRAW CURVE
    # =====================================

    def _draw_curve(
        self,
        pts,
        color,
        draw_labels=False,
        plot_top=0,
        plot_bottom=0
    ):

        c = self.canv

        if len(pts) < 1:
            return

        # =====================================
        # CURVE LINE
        # =====================================

        if not draw_labels:

            c.setStrokeColor(color)
            c.setLineWidth(2)

            for i in range(len(pts)-1):

                c.line(
                    pts[i][0],
                    pts[i][1],
                    pts[i+1][0],
                    pts[i+1][1]
                )

        # =====================================
        # POINTS / LABELS
        # =====================================

        for x, y, val in pts:

            # ---------------------------------
            # POINT MARKER
            # ---------------------------------

            if not draw_labels:

                c.setFillColor(color)

                c.circle(
                    x,
                    y,
                    3,
                    fill=1
                )

                continue

            # ---------------------------------
            # LABEL
            # ---------------------------------

            label = f"{val:.1f}%"

            box_w = 18
            box_h = 7

            # =====================================
            # LABEL POSITION
            # hijau bawah
            # orange atas
            # =====================================

            if color == colors.HexColor("#22c55e"):

                label_y = y + 8

            else:

                label_y = y - 13

            # =====================================
            # CLAMP LABEL INSIDE TABLE
            # =====================================

            label_y = max(
                plot_top + 2,
                min(
                    label_y,
                    plot_bottom - 8
                )
            )

            # =====================================
            # LABEL BOX
            # =====================================

            c.setFillColor(color)

            c.roundRect(
                x - box_w / 2,
                label_y,
                box_w,
                box_h,
                1.5,
                fill=1,
                stroke=0
            )

            # =====================================
            # LABEL TEXT
            # =====================================

            c.setFillColor(colors.white)

            c.setFont(
                "Helvetica-Bold",
                4.8
            )

            c.drawCentredString(
                x,
                label_y + 1.8,
                label
            )


    # =====================================
    # MAIN DRAW
    # =====================================

    def draw(self):

        # draw table first
        super().draw()

        if not self.summary:
            return

        c = self.canv

        # =====================================
        # TABLE GEOMETRY
        # =====================================

        week_start_col = 4

        week_end_col = (
            week_start_col
            + len(self.summary)
            - 1
        )

        # =====================================
        # TASK BODY ROWS
        # =====================================

        first_task_row = 1

        last_task_row = (
            len(self._rowHeights)
            - self.SUMMARY_ROWS
            - 1
        )

        # =====================================
        # EXACT COORDINATE
        # =====================================

        x0 = self._colpositions[
            week_start_col
        ]

        x1 = self._colpositions[
            week_end_col + 1
        ]

        body_top = self._rowpositions[
            first_task_row
        ]

        body_bottom = self._rowpositions[
            last_task_row + 1
        ]

        # =====================================
        # SAFE PLOT AREA
        # =====================================

        plot_top = min(
            body_top,
            body_bottom
        ) + 2

        plot_bottom = max(
            body_top,
            body_bottom
        ) - 2

        usable_h = (
            plot_bottom
            - plot_top
        )

        if usable_h <= 0:
            return

        # =====================================
        # CLIP INSIDE GRID
        # =====================================

        c.saveState()

        p = c.beginPath()

        p.rect(
            x0,
            plot_top,
            x1 - x0,
            usable_h
        )

        c.clipPath(
            p,
            stroke=0,
            fill=0
        )

        # =====================================
        # BUILD CURVE POINTS
        # =====================================

        sched = []
        actual = []

        for i, s in enumerate(self.summary):

            cell_left = self._colpositions[
                week_start_col + i
            ]

            cell_right = self._colpositions[
                week_start_col + i + 1
            ]

            # center point
            x = (
                cell_left
                + cell_right
            ) / 2

            # =====================================
            # PLAN Y
            # =====================================

            y_plan = (
                plot_top
                + (
                    float(
                        s["plan_cum"]
                    ) / 100.0
                ) * usable_h
            )

            sched.append(
                (
                    x,
                    y_plan,
                    float(
                        s["plan_cum"]
                    )
                )
            )

            # =====================================
            # ACTUAL Y
            # =====================================

            if i < self.current_week:

                y_act = (
                    plot_top
                    + (
                        float(
                            s["actual_cum"]
                        ) / 100.0
                    ) * usable_h
                )

                actual.append(
                    (
                        x,
                        y_act,
                        float(
                            s["actual_cum"]
                        )
                    )
                )

        # =====================================
        # DRAW CURVES
        # =====================================

        self._draw_curve(
            sched,
            colors.HexColor("#22c55e"),
            draw_labels=False
        )

        self._draw_curve(
            actual,
            colors.HexColor("#f59e0b"),
            draw_labels=False
        )

        # =====================================
        # END CLIP
        # =====================================

        c.restoreState()

        # =====================================
        # DRAW LABELS
        # =====================================

        self._draw_curve(
            sched,
            colors.HexColor("#22c55e"),
            draw_labels=True,
            plot_top=plot_top,
            plot_bottom=plot_bottom
        )

        self._draw_curve(
            actual,
            colors.HexColor("#f59e0b"),
            draw_labels=True,
            plot_top=plot_top,
            plot_bottom=plot_bottom
        )

class ScurveExport(http.Controller):

    @http.route(
        "/pm_scurve/export_reportlab/<int:project_id>",
        auth="user",
    )
    def export_reportlab(self, project_id, **kw):

        project = request.env["pm.project"].browse(project_id)

        data = project.get_scurve_data(project_id)

        selected_week = int(
            kw.get(
                "week",
                data.get("current_week", 1),
            )
        )

        out = build_scurve_reportlab_pdf(
            project,
            selected_week=selected_week,
            page_size="A3",
        )

        return request.make_response(
            out,
            headers=[
                ("Content-Type", "application/pdf"),
                (
                    "Content-Disposition",
                    "inline; filename=scurve.pdf",
                ),
            ],
        )