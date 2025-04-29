# Utilities
from datetime import datetime


def parse_date(date_str):
    formats = ["%Y年%m月%d日", "%d/%m/%Y", "%Y-%m-%d"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except:
            continue
    return None