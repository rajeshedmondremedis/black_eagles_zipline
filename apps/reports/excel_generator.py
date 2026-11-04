import io
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from django.utils import timezone


def generate_bookings_excel(bookings_queryset, filter_meta=None):
    """
    Generates a beautifully styled Excel spreadsheet of zipline bookings using OpenPyXL.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Zipline Bookings"

    # Color Palette: Dark Forest Green (#0F2A1D), White, Subtle Gray
    HEADER_FILL = PatternFill(start_color="0F2A1D", end_color="0F2A1D", fill_type="solid")
    TITLE_FONT = Font(name="Calibri", size=16, bold=True, color="0F2A1D")
    SUBTITLE_FONT = Font(name="Calibri", size=11, italic=True, color="555555")
    HEADER_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    DATA_FONT = Font(name="Calibri", size=10)
    TOTAL_FONT = Font(name="Calibri", size=11, bold=True, color="000000")

    THIN_BORDER = Border(
        left=Side(style='thin', color='CCCCCC'),
        right=Side(style='thin', color='CCCCCC'),
        top=Side(style='thin', color='CCCCCC'),
        bottom=Side(style='thin', color='CCCCCC')
    )

    # 1. Company Header
    ws.merge_cells('A1:J1')
    ws['A1'] = "BLACK EAGLES ZIPLINE – BOOKING REPORT"
    ws['A1'].font = TITLE_FONT
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 30

    # 2. Metadata / Filter subtitle
    meta_text = f"Generated on: {timezone.localtime(timezone.now()).strftime('%d-%b-%Y %I:%M %p')}"
    if filter_meta:
        meta_text += f" | Range: {filter_meta.get('date_range', 'All Dates')} | Status: {filter_meta.get('status', 'All')}"
    ws.merge_cells('A2:J2')
    ws['A2'] = meta_text
    ws['A2'].font = SUBTITLE_FONT
    ws['A2'].alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[2].height = 20

    # Blank row 3
    ws.row_dimensions[3].height = 10

    # 3. Table Column Headers
    headers = [
        "Booking Reference",
        "Customer Name",
        "Mobile Number",
        "Email",
        "Place",
        "Booking Date",
        "Slot",
        "Number of Members",
        "Booking Status",
        "Created Date",
    ]

    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=4, column=col_idx, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = THIN_BORDER
    ws.row_dimensions[4].height = 26

    # 4. Data Rows
    row_num = 5
    total_members = 0

    for b in bookings_queryset:
        ws.cell(row=row_num, column=1, value=b.booking_reference)
        ws.cell(row=row_num, column=2, value=b.full_name)
        ws.cell(row=row_num, column=3, value=b.mobile_number)
        ws.cell(row=row_num, column=4, value=b.email)
        ws.cell(row=row_num, column=5, value=b.place)
        ws.cell(row=row_num, column=6, value=b.booking_date.strftime('%Y-%m-%d'))
        ws.cell(row=row_num, column=7, value=f"{b.slot.name} ({b.slot.formatted_time})")
        
        mem_cell = ws.cell(row=row_num, column=8, value=b.number_of_members)
        mem_cell.alignment = Alignment(horizontal='center')
        
        status_cell = ws.cell(row=row_num, column=9, value=b.get_status_display())
        status_cell.alignment = Alignment(horizontal='center')
        if b.status == 'CONFIRMED':
            status_cell.font = Font(name="Calibri", size=10, bold=True, color="1B5E20")
        else:
            status_cell.font = Font(name="Calibri", size=10, bold=True, color="B71C1C")

        ws.cell(row=row_num, column=10, value=b.created_at.strftime('%Y-%m-%d %H:%M'))

        for c in range(1, 11):
            cell = ws.cell(row=row_num, column=c)
            if c != 9:
                cell.font = DATA_FONT
            cell.border = THIN_BORDER

        if b.status == 'CONFIRMED':
            total_members += b.number_of_members

        ws.row_dimensions[row_num].height = 20
        row_num += 1

    # 5. Summary / Total Row
    ws.cell(row=row_num, column=1, value="TOTAL CONFIRMED RIDERS").font = TOTAL_FONT
    ws.cell(row=row_num, column=8, value=total_members).font = TOTAL_FONT
    ws.cell(row=row_num, column=8).alignment = Alignment(horizontal='center')
    for c in range(1, 11):
        cell = ws.cell(row=row_num, column=c)
        cell.border = THIN_BORDER
        cell.fill = PatternFill(start_color="EEEEEE", end_color="EEEEEE", fill_type="solid")
    ws.row_dimensions[row_num].height = 22

    # Auto-adjust column widths safely
    for col_idx in range(1, 11):
        max_len = max(len(str(ws.cell(row=r, column=col_idx).value or '')) for r in range(4, row_num + 1))
        col_letter = get_column_letter(col_idx)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 14)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()
