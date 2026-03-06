from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django import template

register = template.Library()


def _to_decimal(value):
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


@register.filter
def mul(value, arg):
    return _to_decimal(value) * _to_decimal(arg)


@register.filter
def vnd(value):
    amount = _to_decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    sign = "-" if amount < 0 else ""
    integer_value = int(abs(amount))
    return f"{sign}{integer_value:,}".replace(",", ".")
