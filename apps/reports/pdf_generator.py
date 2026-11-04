import io
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from django.utils import timezone


def generate_bookings_pdf(bookings_queryset, filter_meta=None):
    """
    Generates a high-quality PDF report for Black Eagles Zipline using ReportLab.
    Landscape orientation for full width table readability.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    story = []
    styles = getSampleStyleSheet()

    # Custom styles
    brand_color = colors.HexColor('#0F2A1D')
    accent_orange = colors.HexColor('#F77F00')
    dark_gray = colors.HexColor('#222222')

    title_style = ParagraphStyle(
        'BrandTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=brand_color,
        alignment=1  # Center
    )

    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=dark_gray,
        alignment=1  # Center
    )

    cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.black
    )

    cell_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )

    # Header / Branding
    story.append(Paragraph("🦅 BLACK EAGLES ZIPLINE", title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("OFFICIAL RESERVATION & PASSENGER MANIFEST REPORT", subtitle_style))
    story.append(Spacer(1, 8))

    # Metadata & KPI Summary Banner
    total_bookings = bookings_queryset.count()
    confirmed_bookings = bookings_queryset.filter(status='CONFIRMED')
    total_riders = sum(b.number_of_members for b in confirmed_bookings)
    cancelled_count = bookings_queryset.filter(status='CANCELLED').count()

    date_range_str = filter_meta.get('date_range', 'All Dates') if filter_meta else 'All Dates'
    gen_time_str = timezone.localtime(timezone.now()).strftime('%d-%b-%Y %I:%M %p')

    summary_data = [
        [
            Paragraph(f"<b>Date Range:</b> {date_range_str}", styles['Normal']),
            Paragraph(f"<b>Generated On:</b> {gen_time_str}", styles['Normal']),
            Paragraph(f"<b>Total Bookings:</b> {total_bookings}", styles['Normal']),
            Paragraph(f"<b>Confirmed Riders:</b> <font color='#0F2A1D'><b>{total_riders}</b></font>", styles['Normal']),
            Paragraph(f"<b>Cancelled:</b> {cancelled_count}", styles['Normal']),
        ]
    ]
    summary_table = Table(summary_data, colWidths=[150, 160, 110, 130, 90])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F4F6F4')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#D0D7D1')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 12))

    # Main Bookings Table
    table_headers = [
        Paragraph("Reference", cell_header_style),
        Paragraph("Customer Name", cell_header_style),
        Paragraph("Contact", cell_header_style),
        Paragraph("Place", cell_header_style),
        Paragraph("Flight Date", cell_header_style),
        Paragraph("Time Slot", cell_header_style),
        Paragraph("Pax", cell_header_style),
        Paragraph("Status", cell_header_style),
        Paragraph("Booked At", cell_header_style),
    ]

    table_data = [table_headers]

    for b in bookings_queryset:
        contact_str = f"{b.mobile_number}<br/>{b.email}"
        slot_str = f"{b.slot.name}<br/>({b.slot.formatted_time})"
        
        status_color = "#1B5E20" if b.status == 'CONFIRMED' else "#B71C1C"
        status_html = f"<font color='{status_color}'><b>{b.get_status_display()}</b></font>"

        row = [
            Paragraph(f"<b>{b.booking_reference}</b>", cell_style),
            Paragraph(b.full_name, cell_style),
            Paragraph(contact_str, cell_style),
            Paragraph(b.place, cell_style),
            Paragraph(b.booking_date.strftime('%d-%b-%Y'), cell_style),
            Paragraph(slot_str, cell_style),
            Paragraph(f"<para align='center'><b>{b.number_of_members}</b></para>", cell_style),
            Paragraph(status_html, cell_style),
            Paragraph(b.created_at.strftime('%d-%b %H:%M'), cell_style),
        ]
        table_data.append(row)

    if len(table_data) == 1:
        empty_row = [Paragraph("<para align='center'><i>No bookings found matching selected criteria.</i></para>", cell_style)] + [Paragraph("", cell_style)]*8
        table_data.append(empty_row)

    col_widths = [85, 100, 115, 75, 75, 110, 40, 65, 75]
    bookings_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    bookings_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), brand_color),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#DDDDDD')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FBFBFB')])
    ]))

    story.append(bookings_table)
    story.append(Spacer(1, 14))

    # Footer note
    footer_text = "Black Eagles Zipline • Confidential Commercial Passenger Record • Powered by PL SOFT TECH SOLUTIONS"
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CCCCCC'), spaceAfter=6, spaceBefore=4))
    story.append(Paragraph(footer_text, ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.gray, alignment=1)))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
