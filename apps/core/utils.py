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
