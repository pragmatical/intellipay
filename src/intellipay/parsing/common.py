from datetime import datetime
from decimal import Decimal


def decimal_value(value: object) -> Decimal:
    text = str(value or "0").strip().replace("$", "").replace(",", "").replace("O", "0")
    return Decimal(text)


def normalize_date(value: object) -> str:
    text = str(value or "").strip().replace("2O", "20")
    for date_format in ("%Y-%m-%d", "%m/%d/%Y", "%b %d %Y", "%d-%b-%Y", "%B %d, %Y"):
        try:
            return datetime.strptime(text, date_format).date().isoformat()
        except ValueError:
            continue
    return text
