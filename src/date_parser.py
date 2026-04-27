from datetime import date

def parse_iso_date(date_string):
    try:
        return date.fromisoformat(date_string.strip())
    except (ValueError, AttributeError):
        return None

def validate_date(date_range):
    if not isinstance(date_range, str):
        return None, None

    parts = [part.strip() for part in date_range.split(",")]

    if len(parts) != 2:
        return None, None

    start_date_str, end_date_str = parts

    start_date = parse_iso_date(start_date_str)
    end_date = parse_iso_date(end_date_str)

    if start_date is None or end_date is None:
        return None, None

    if start_date > end_date:
        return None, None

    return start_date_str, end_date_str

