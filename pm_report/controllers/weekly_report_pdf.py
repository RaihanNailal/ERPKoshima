from io import BytesIO
import base64

from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from odoo import http
from odoo.http import request
from odoo.addons.pm_scurve.controllers.reportlab_export import build_scurve_reportlab_pdf
from odoo.addons.pm_gantt.controllers.exportexcel import build_timeline_pdf

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    from PyPDF2 import PdfReader, PdfWriter


DOC_FRAME_LEFT = 50
DOC_FRAME_RIGHT = 50
DOC_FRAME_TOP = 32
DOC_FRAME_BOTTOM = 32
DOC_HEADER_HEIGHT = 68
DOC_CONTENT_PADDING = 14


def _as_base64_text(value):
    if not value:
        return ""

    return (
        value.decode("utf-8")
        if isinstance(value, bytes)
        else value
    )


def _draw_image_fit(pdf, image_base64, x, y, box_width, box_height, border=False):
    image_bytes = base64.b64decode(image_base64)
    image = Image.open(BytesIO(image_bytes))
    width, height = image.size

    ratio = min(box_width / width, box_height / height)
    draw_width = width * ratio
    draw_height = height * ratio
    draw_x = x + ((box_width - draw_width) / 2)
    draw_y = y + ((box_height - draw_height) / 2)

    if border:
        pdf.setLineWidth(1)
        pdf.setStrokeColorRGB(0, 0, 0)
        pdf.rect(
            draw_x,
            draw_y,
            draw_width,
            draw_height,
            stroke=1,
            fill=0,
        )

    pdf.drawImage(
        ImageReader(BytesIO(image_bytes)),
        draw_x,
        draw_y,
        width=draw_width,
        height=draw_height,
        preserveAspectRatio=True,
        mask="auto",
    )


def _draw_documentation_frame(pdf, page_width, page_height):
    left = DOC_FRAME_LEFT
    bottom = DOC_FRAME_BOTTOM
    width = page_width - DOC_FRAME_LEFT - DOC_FRAME_RIGHT
    height = page_height - DOC_FRAME_TOP - DOC_FRAME_BOTTOM

    frame_top = page_height - DOC_FRAME_TOP
    header_bottom = frame_top - DOC_HEADER_HEIGHT

    pdf.setLineWidth(1)
    pdf.setStrokeColorRGB(0, 0, 0)
    pdf.rect(
        left,
        bottom,
        width,
        height,
        stroke=1,
        fill=0,
    )
    pdf.line(
        left,
        header_bottom,
        left + width,
        header_bottom,
    )


def _draw_documentation_header(pdf, project, page_width, page_height):
    _draw_documentation_frame(pdf, page_width, page_height)

    left_logo = _as_base64_text(project.logo_left)
    right_logo = _as_base64_text(project.logo_right)

    frame_top = page_height - DOC_FRAME_TOP
    header_bottom = frame_top - DOC_HEADER_HEIGHT
    header_center_y = header_bottom + (DOC_HEADER_HEIGHT / 2)

    if left_logo:
        _draw_image_fit(
            pdf,
            left_logo,
            DOC_FRAME_LEFT + 10,
            header_center_y - 24,
            110,
            48,
        )

    if right_logo:
        _draw_image_fit(
            pdf,
            right_logo,
            page_width - DOC_FRAME_RIGHT - 132,
            header_center_y - 22,
            122,
            44,
        )

    pdf.setFont("Times-Roman", 22)
    pdf.drawCentredString(
        page_width / 2,
        header_center_y - 8,
        "Dokumentasi",
    )


def build_documentation_pdf(project, photos):
    output = BytesIO()
    pdf = canvas.Canvas(output, pagesize=letter)
    page_width, page_height = letter

    left = DOC_FRAME_LEFT + DOC_CONTENT_PADDING
    right = page_width - DOC_FRAME_RIGHT - DOC_CONTENT_PADDING
    top = page_height - DOC_FRAME_TOP - DOC_HEADER_HEIGHT - DOC_CONTENT_PADDING
    bottom = DOC_FRAME_BOTTOM + DOC_CONTENT_PADDING
    gap = 12

    column_gap = 14
    column_width = (right - left - (2 * column_gap)) / 3
    portrait_height = 174
    landscape_height = 250

    current_y = top
    portrait_row = []

    def new_page():
        nonlocal current_y
        pdf.showPage()
        _draw_documentation_header(pdf, project, page_width, page_height)
        current_y = top

    def flush_portrait_row():
        nonlocal current_y, portrait_row
        if not portrait_row:
            return

        if current_y - portrait_height < bottom:
            new_page()

        for index, photo in enumerate(portrait_row):
            x = left + (index * (column_width + column_gap))
            _draw_image_fit(
                pdf,
                photo["image"],
                x,
                current_y - portrait_height,
                column_width,
                portrait_height,
            )

        current_y -= portrait_height + gap
        portrait_row = []

    _draw_documentation_header(pdf, project, page_width, page_height)

    for photo in photos:
        if photo.get("is_landscape"):
            flush_portrait_row()

            if current_y - landscape_height < bottom:
                new_page()

            _draw_image_fit(
                pdf,
                photo["image"],
                left,
                current_y - landscape_height,
                right - left,
                landscape_height,
            )
            current_y -= landscape_height + gap
            continue

        portrait_row.append(photo)

        if len(portrait_row) == 3:
            flush_portrait_row()

    flush_portrait_row()

    pdf.save()
    return output.getvalue()


class WeeklyReportPDFController(http.Controller):

    @http.route(
        "/pm_report/weekly_export_pdf/<int:project_id>",
        type="http",
        auth="user"
    )
    def weekly_export_pdf(self, project_id):

        project = request.env["pm.project"].sudo().browse(project_id)

        if not project.exists():
            return request.not_found()

        writer = PdfWriter()

        weekly_pdf, _ = request.env["ir.actions.report"]._render_qweb_pdf(
            "pm_report.action_weekly_report_pdf",
            [project.id]
        )

        for page in PdfReader(BytesIO(weekly_pdf)).pages:
            writer.add_page(page)

        timeline_pdf = build_timeline_pdf(project)

        if timeline_pdf:
            for page in PdfReader(BytesIO(timeline_pdf)).pages:
                writer.add_page(page)

        scurve_pdf = build_scurve_reportlab_pdf(
            project,
            page_size="A3",
        )

        if scurve_pdf:
            for page in PdfReader(BytesIO(scurve_pdf)).pages:
                writer.add_page(page)

        photos = []

        for photo in project.photo_ids:
            if not photo.image:
                continue

            image = (
                photo.image.decode("utf-8")
                if isinstance(photo.image, bytes)
                else photo.image
            )

            try:
                img = Image.open(BytesIO(base64.b64decode(image)))
                width, height = img.size
                is_portrait = height > width
                is_landscape = width >= height
            except Exception:
                is_portrait = False
                is_landscape = True

            photos.append({
                "name": photo.name or "",
                "image": image,
                "is_portrait": is_portrait,
                "is_landscape": is_landscape,
            })

        if photos:
            documentation_pdf = build_documentation_pdf(
                project,
                photos,
            )

            for page in PdfReader(BytesIO(documentation_pdf)).pages:
                writer.add_page(page)

        output = BytesIO()
        writer.write(output)

        filename = "%s - Weekly Report.pdf" % project.name

        return request.make_response(
            output.getvalue(),
            headers=[
                ("Content-Type", "application/pdf"),
                (
                    "Content-Disposition",
                    'attachment; filename="%s"' % filename
                ),
            ]
        )
