from pathlib import Path
from decimal import Decimal
from html import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PDF_DIR = BASE_DIR / "generated_pdfs"
PDF_DIR.mkdir(exist_ok=True)


INK = colors.HexColor("#172923")
GREEN = colors.HexColor("#1e5d48")
GREEN_DARK = colors.HexColor("#153d32")
MUTED = colors.HexColor("#68766f")
PALE = colors.HexColor("#f2f6f2")
LINE = colors.HexColor("#d9e2db")


def format_money(value):
    formatted = f"{Decimal(str(value)):,.2f}"
    return "$" + formatted.replace(",", "X").replace(".", ",").replace("X", ".")


def generate_quote_pdf(quote):
    file_name = f"{quote.quote_number}.pdf"
    file_path = PDF_DIR / file_name

    doc = SimpleDocTemplate(
        str(file_path),
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=48,
    )

    styles = getSampleStyleSheet()
    company_style = ParagraphStyle(
        "CompanyName",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=GREEN_DARK,
        alignment=0,
        spaceAfter=0,
    )
    company_rut_style = ParagraphStyle(
        "CompanyRut",
        parent=styles["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=GREEN,
    )
    number_style = ParagraphStyle(
        "QuoteNumber",
        parent=styles["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=GREEN,
        alignment=2,
    )
    date_style = ParagraphStyle(
        "QuoteDate",
        parent=styles["BodyText"],
        fontSize=10,
        leading=14,
        textColor=MUTED,
        alignment=2,
    )
    meta_style = ParagraphStyle(
        "QuoteMeta",
        parent=styles["BodyText"],
        fontSize=9,
        leading=13,
        textColor=MUTED,
    )
    label_style = ParagraphStyle(
        "QuoteLabel",
        parent=styles["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=MUTED,
    )
    value_style = ParagraphStyle(
        "QuoteValue",
        parent=styles["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=INK,
    )
    cell_style = ParagraphStyle(
        "QuoteCell",
        parent=styles["BodyText"],
        fontSize=9,
        leading=12,
        textColor=INK,
    )
    header_cell_style = ParagraphStyle(
        "QuoteHeaderCell",
        parent=cell_style,
        fontName="Helvetica-Bold",
        textColor=colors.white,
    )

    header = Table([
        [
            Paragraph("ESIGN S.A.", company_style),
            Paragraph(f"Fecha de emisión<br/><b>{quote.created_at.strftime('%d-%m-%Y')}</b>", date_style),
        ],
        [
            Paragraph("RUT 99.551.740-K", company_rut_style),
            Paragraph(f"COTIZACIÓN {escape(quote.quote_number)}", number_style),
        ],
    ], colWidths=[365, 150])
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("LINEBELOW", (0, -1), (-1, -1), 1.5, GREEN),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))

    client_table = Table([
        [Paragraph("CLIENTE", label_style), Paragraph("RUT", label_style)],
        [Paragraph(escape(quote.client_razon_social), value_style), Paragraph(escape(quote.client_rut), value_style)],
    ], colWidths=[365, 150])
    client_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PALE),
        ("BOX", (0, 0), (-1, -1), 0.6, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))

    story = [header, Spacer(1, 18), client_table, Spacer(1, 20)]
    table_data = [[
        Paragraph("Producto", header_cell_style),
        Paragraph("Cant.", header_cell_style),
        Paragraph("Valor unitario", header_cell_style),
        Paragraph("Subtotal", header_cell_style),
    ]]
    for item in quote.items:
        product_name = item.product.name if item.product else "Producto eliminado"
        table_data.append([
            Paragraph(escape(product_name), cell_style),
            Paragraph(str(item.quantity), cell_style),
            Paragraph(format_money(item.unit_price), cell_style),
            Paragraph(format_money(item.subtotal), cell_style),
        ])

    table = Table(table_data, colWidths=[245, 45, 105, 120], repeatRows=1)
    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), GREEN_DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
            ("LINEBELOW", (0, 0), (-1, 0), 0.8, GREEN),
            ("LINEBELOW", (0, 1), (-1, -1), 0.4, LINE),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 9),
            ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ])
    )
    story.append(table)
    story.append(Spacer(1, 18))

    totals_data = [["Subtotal", format_money(quote.subtotal)]]
    if quote.discount_amount > 0:
        totals_data.append([f"Descuento ({quote.discount_percent}%)", f"-{format_money(quote.discount_amount)}"])
        totals_data.append(["Neto afecto", format_money(quote.subtotal - quote.discount_amount)])
    totals_data.extend([
        ["IVA (19%)", format_money(quote.iva)],
        ["TOTAL", format_money(quote.total)],
    ])
    totals = Table(totals_data, colWidths=[160, 120], hAlign="RIGHT")
    totals.setStyle(TableStyle([
        ("TEXTCOLOR", (0, 0), (-1, -1), INK),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("LINEABOVE", (0, 0), (-1, 0), 0.7, LINE),
        ("LINEABOVE", (0, -1), (-1, -1), 1.2, GREEN),
        ("BACKGROUND", (0, -1), (-1, -1), PALE),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, -1), (-1, -1), GREEN_DARK),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(totals)

    detail_rows = []
    if quote.payment_method:
        detail_rows.append([Paragraph("Forma de pago", label_style), Paragraph(escape(quote.payment_method), cell_style)])
    if quote.due_date:
        detail_rows.append([Paragraph("Vencimiento", label_style), Paragraph(quote.due_date.strftime("%d-%m-%Y"), cell_style)])
    if quote.bank_details:
        detail_rows.append([Paragraph("Datos bancarios", label_style), Paragraph(escape(quote.bank_details), cell_style)])
    if quote.conditions:
        conditions = escape(quote.conditions).replace("\n", "<br/>")
        detail_rows.append([Paragraph("Condiciones", label_style), Paragraph(conditions, cell_style)])

    if detail_rows:
        story.extend([Spacer(1, 22), Paragraph("DETALLES", label_style), Spacer(1, 6)])
        details = Table(detail_rows, colWidths=[115, 400])
        details.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        story.append(details)

    def draw_footer(canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(LINE)
        canvas.line(document.leftMargin, 30, A4[0] - document.rightMargin, 30)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(document.leftMargin, 18, f"Cotiza | {quote.quote_number}")
        canvas.drawRightString(A4[0] - document.rightMargin, 18, str(canvas.getPageNumber()))
        canvas.restoreState()

    doc.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)
    quote.pdf_path = str(file_path)
    return file_path
