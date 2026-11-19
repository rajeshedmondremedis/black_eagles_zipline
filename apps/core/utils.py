def extract_validation_error_message(e):
    """
    Safely unpacks error messages from a Django ValidationError instance
    whether it contains a list of messages, a dict of field errors, or a single string.
    """
    if hasattr(e, 'messages') and e.messages:
        return ' '.join(e.messages)
    if hasattr(e, 'message_dict') and e.message_dict:
        lines = []
        for field, errs in e.message_dict.items():
            lines.append(f"{field}: {', '.join(errs)}")
        return ' '.join(lines)
    if hasattr(e, 'message'):
        return e.message
    return str(e)


def generate_qr_svg(data, size=110):
    """
    Generates a vector SVG string of a QR Code for the given string data.
    Uses ReportLab's built-in vector barcode engine.
    """
    from reportlab.graphics.shapes import Drawing
    from reportlab.graphics.barcode.qr import QrCodeWidget
    from reportlab.graphics import renderSVG
    import io

    try:
        qr = QrCodeWidget(str(data))
        bounds = qr.getBounds()
        w = max(bounds[2] - bounds[0], 1)
        scale = size / w
        d = Drawing(size, size, transform=[scale, 0, 0, scale, 0, 0])
        d.add(qr)
        buf = io.StringIO()
        renderSVG.drawToFile(d, buf)
        return buf.getvalue()
    except Exception:
        return ""


