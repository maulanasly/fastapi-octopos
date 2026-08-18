from decimal import ROUND_HALF_UP, Decimal

MoneyInput = Decimal | float | int | str | None

_MONEY_QUANT = Decimal("0.01")


def to_decimal(value: MoneyInput, default: str = "0") -> Decimal:
    if value is None:
        return Decimal(default)
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def quantize_money(value: MoneyInput) -> Decimal:
    return to_decimal(value).quantize(_MONEY_QUANT, rounding=ROUND_HALF_UP)


def money_to_float(value: MoneyInput, default: str = "0") -> float:
    """Quantize a money value and return it as a float (API boundary only)."""
    return float(quantize_money(to_decimal(value, default)))
