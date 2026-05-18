from odoo import fields
import io
import base64
import tempfile

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image,
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import utils


def build_issue_report_pdf(issues):

    buf = io.BytesIO()

    pdf = SimpleDocTemplate(
        buf,
        pagesize=landscape(A3),
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )

    styles = getSampleStyleSheet()
    from reportlab.lib.enums import TA_CENTER

    cell_style = styles["BodyText"].clone("cell_style")
    cell_style.alignment = TA_CENTER
    cell_style.leading = 12
    story = []

    project = issues[0].project_id

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

    def fit_logo(path, max_w, max_h):
        if not path:
            return ""

        img = utils.ImageReader(path)
        iw, ih = img.getSize()

        ratio = min(max_w / iw, max_h / ih)

        return Image(
            path,
            width=iw * ratio,
            height=ih * ratio,
        )

    def make_image(binary_data, max_w=85 * mm, max_h=60 * mm):
        if not binary_data:
            return Paragraph("-", styles["Normal"])

        raw = base64.b64decode(binary_data)

        img = utils.ImageReader(io.BytesIO(raw))
        iw, ih = img.getSize()

        ratio = min(
            max_w / float(iw),
            max_h / float(ih),
        )

        new_w = iw * ratio
        new_h = ih * ratio

        image = Image(
            io.BytesIO(raw),
            width=new_w,
            height=new_h,
        )

        image.hAlign = "CENTER"

        return image

    logo_left = save_binary(project.logo_left)
    logo_right = save_binary(project.logo_right)

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
                """
                <para align='center' leading='20'>
                    <font size=16>
                        <b>LAPORAN INSPEKSI DAN</b><br/>
                        <b>TINDAKAN PERBAIKAN</b>
                    </font>
                </para>
                """,
                styles["Normal"],
            ),
            right_logo,
        ]],
        colWidths=[
            135 * mm,
            140 * mm,
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
    ]))

    story.append(header)
    story.append(Spacer(1, 20))

    rows = [[
        "NO",
        "FOTO TEMUAN",
        "DESKRIPSI TEMUAN",
        "TINDAKAN PERBAIKAN",
        "PENANGGUNG JAWAB",
        "STATUS",
        "FOTO TINDAKAN",
    ]]

    status_map = {
        "open": "SUBMITTED",
        "progress": "UNDER REVIEW",
        "closed": "SOLVED",
    }

    for idx, issue in enumerate(issues, 1):

        if issue.converted_task_id:
            pic = issue.converted_task_id.pic_id.name or "-"
            after_photos = issue.task_photo_ids
        else:
            pic = issue.reviewed_by.name if issue.reviewed_by else "-"
            after_photos = issue.after_photo_ids

        before_img = (
            make_image(issue.photo_ids[0].image)
            if issue.photo_ids else "-"
        )

        after_img = (
            make_image(after_photos[0].image)
            if after_photos else "-"
        )

        rows.append([
            Paragraph(str(idx), cell_style),
            before_img,
            Paragraph(issue.name or "-", cell_style),
            Paragraph(issue.corrective_action or "-", cell_style),
            Paragraph(pic, cell_style),
            Paragraph(status_map.get(issue.status, "-"), cell_style),
            after_img,
        ])

    tbl = Table(
        rows,
        colWidths=[
            12 * mm,   # NO
            90 * mm,   # FOTO TEMUAN
            75 * mm,   # DESKRIPSI
            75 * mm,   # TINDAKAN
            42 * mm,   # PIC
            30 * mm,   # STATUS
            90 * mm,   # FOTO TINDAKAN
        ],
        repeatRows=1,
    )

    tbl.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.7, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),

        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

        ("FONTSIZE", (0, 1), (-1, -1), 9),

        ("LEFTPADDING", (0, 1), (-1, -1), 4),
        ("RIGHTPADDING", (0, 1), (-1, -1), 4),
        ("TOPPADDING", (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),

        ("ALIGN", (0, 1), (0, -1), "CENTER"),
        ("ALIGN", (4, 1), (5, -1), "CENTER"),

        ("VALIGN", (0, 1), (-1, -1), "MIDDLE"),
    ]))

    story.append(tbl)

    pdf.build(story)

    out = buf.getvalue()
    buf.close()

    return out