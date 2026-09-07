"""Placeholders for FF_FACTORING_CESSION (appendix table + header)."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

ALMATY_TZ = ZoneInfo("Asia/Almaty")
DEFAULT_TARIFF = Decimal("0.12")
DEFAULT_DISCOUNT_BY_PERIOD = {
    3: Decimal("0.045"),
    6: Decimal("0.07"),
    9: Decimal("0.10"),
    12: Decimal("0.12"),
    24: Decimal("0.17"),
}
PARTNER_NAME = 'ТОО "Freedom Mobile"'
DEFAULT_STATUS = "Выдано"

_MONTHS_RU = (
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
)
_MONTHS_KZ = (
    "қаңтар",
    "ақпан",
    "наурыз",
    "сәуір",
    "мамыр",
    "маусым",
    "шілде",
    "тамыз",
    "қыркүйек",
    "қазан",
    "қараша",
    "желтоқсан",
)

_ONES_RU = (
    "",
    "один",
    "два",
    "три",
    "четыре",
    "пять",
    "шесть",
    "семь",
    "восемь",
    "девять",
)
_ONES_FEM_RU = (
    "",
    "одна",
    "две",
    "три",
    "четыре",
    "пять",
    "шесть",
    "семь",
    "восемь",
    "девять",
)
_TEENS_RU = (
    "десять",
    "одиннадцать",
    "двенадцать",
    "тринадцать",
    "четырнадцать",
    "пятнадцать",
    "шестнадцать",
    "семнадцать",
    "восемнадцать",
    "девятнадцать",
)
_TENS_RU = (
    "",
    "",
    "двадцать",
    "тридцать",
    "сорок",
    "пятьдесят",
    "шестьдесят",
    "семьдесят",
    "восемьдесят",
    "девяносто",
)
_HUNDREDS_RU = (
    "",
    "сто",
    "двести",
    "триста",
    "четыреста",
    "пятьсот",
    "шестьсот",
    "семьсот",
    "восемьсот",
    "девятьсот",
)

_ONES_KZ = (
    "",
    "бір",
    "екі",
    "үш",
    "төрт",
    "бес",
    "алты",
    "жеті",
    "сегіз",
    "тоғыз",
)
_TEENS_KZ = (
    "он",
    "он бір",
    "он екі",
    "он үш",
    "он төрт",
    "он бес",
    "он алты",
    "он жеті",
    "он сегіз",
    "он тоғыз",
)
_TENS_KZ = (
    "",
    "",
    "жиырма",
    "отыз",
    "қырық",
    "елу",
    "алпыс",
    "жетпіс",
    "сексен",
    "тоқсан",
)
_HUNDREDS_KZ = (
    "",
    "жүз",
    "екі жүз",
    "үш жүз",
    "төрт жүз",
    "бес жүз",
    "алты жүз",
    "жеті жүз",
    "сегіз жүз",
    "тоғыз жүз",
)


def _as_date(value: date | datetime | str | None) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=ALMATY_TZ).date()
        return value.astimezone(ALMATY_TZ).date()
    if isinstance(value, date):
        return value
    raw = str(value).strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def _as_datetime(value: date | datetime | str | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=ALMATY_TZ)
        return value.astimezone(ALMATY_TZ)
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=ALMATY_TZ)
    raw = str(value).strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=ALMATY_TZ)
    return parsed.astimezone(ALMATY_TZ)


def _money(amount: Decimal) -> str:
    return f"{amount.quantize(Decimal('1')):,}".replace(",", " ")


def _triad_ru(n: int, feminine: bool) -> str:
    hundreds, rest = divmod(n, 100)
    ones_src = _ONES_FEM_RU if feminine else _ONES_RU
    parts: list[str] = []
    if hundreds:
        parts.append(_HUNDREDS_RU[hundreds])
    if rest >= 10 and rest <= 19:
        parts.append(_TEENS_RU[rest - 10])
    else:
        tens, ones = divmod(rest, 10)
        if tens:
            parts.append(_TENS_RU[tens])
        if ones:
            parts.append(ones_src[ones])
    return " ".join(parts)


def amount_text_ru(amount: Decimal) -> str:
    n = int(amount)
    if n == 0:
        return "ноль"
    parts: list[str] = []
    billions, n = divmod(n, 1_000_000_000)
    millions, n = divmod(n, 1_000_000)
    thousands, rest = divmod(n, 1000)
    if billions:
        word = _triad_ru(billions, False)
        parts.append(f"{word} миллиард{_ru_suffix(billions, '', 'а', 'ов')}")
    if millions:
        word = _triad_ru(millions, False)
        parts.append(f"{word} миллион{_ru_suffix(millions, '', 'а', 'ов')}")
    if thousands:
        word = _triad_ru(thousands, True)
        parts.append(f"{word} тысяч{_ru_suffix(thousands, 'а', 'и', '')}")
    if rest:
        parts.append(_triad_ru(rest, False))
    return " ".join(parts)


def _ru_suffix(n: int, one: str, few: str, many: str) -> str:
    n = n % 100
    if 11 <= n <= 14:
        return many
    n = n % 10
    if n == 1:
        return one
    if 2 <= n <= 4:
        return few
    return many


def _triad_kz(n: int) -> str:
    hundreds, rest = divmod(n, 100)
    parts: list[str] = []
    if hundreds:
        parts.append(_HUNDREDS_KZ[hundreds])
    if rest >= 10 and rest <= 19:
        parts.append(_TEENS_KZ[rest - 10])
    else:
        tens, ones = divmod(rest, 10)
        if tens:
            parts.append(_TENS_KZ[tens])
        if ones:
            parts.append(_ONES_KZ[ones])
    return " ".join(parts)


def amount_text_kz(amount: Decimal) -> str:
    n = int(amount)
    if n == 0:
        return "нөл"
    parts: list[str] = []
    billions, n = divmod(n, 1_000_000_000)
    millions, n = divmod(n, 1_000_000)
    thousands, rest = divmod(n, 1000)
    if billions:
        parts.append(f"{_triad_kz(billions)} миллиард")
    if millions:
        parts.append(f"{_triad_kz(millions)} миллион")
    if thousands:
        parts.append(f"{_triad_kz(thousands)} мың")
    if rest:
        parts.append(_triad_kz(rest))
    return " ".join(parts)


def product_name(period: int | None) -> str:
    months = period or 12
    return f"Freedom Mobile факторинг {months} месяцев"


def parse_discount_by_period(raw: Any) -> dict[int, Decimal]:
    if not isinstance(raw, dict) or not raw:
        return dict(DEFAULT_DISCOUNT_BY_PERIOD)
    parsed: dict[int, Decimal] = {}
    for key, value in raw.items():
        try:
            period = int(key)
            rate = Decimal(str(value))
        except (TypeError, ValueError):
            continue
        if period > 0 and rate >= 0:
            parsed[period] = rate
    return parsed or dict(DEFAULT_DISCOUNT_BY_PERIOD)


def allowed_periods(config: dict[str, Any] | None) -> list[int]:
    raw = (config or {}).get("periods")
    if isinstance(raw, list) and raw:
        periods: list[int] = []
        for item in raw:
            try:
                period = int(item)
            except (TypeError, ValueError):
                continue
            if period > 0:
                periods.append(period)
        if periods:
            return periods
    return sorted(parse_discount_by_period((config or {}).get("discount_by_period")))


def tariff_for_period(
    discount_by_period: dict[int, Decimal] | None,
    period: int | None,
) -> Decimal:
    mapping = discount_by_period or DEFAULT_DISCOUNT_BY_PERIOD
    if period is not None and period in mapping:
        return mapping[period]
    return mapping.get(12, DEFAULT_TARIFF)


def format_tariff_percent(rate: Decimal) -> str:
    percent = (rate * 100).quantize(Decimal("0.1"))
    if percent == percent.to_integral():
        return f"{int(percent)}%"
    return f"{percent.normalize()}%"


def build_cession_placeholders(
    *,
    contract_number: str,
    issue_date: date,
    company_name: str = "",
    company_iik: str = "",
    client_signer: str = "",
    applications: list[dict[str, Any]],
    discount_by_period: dict[int, Decimal] | None = None,
) -> tuple[dict[str, str], list[dict[str, str]]]:
    rates = discount_by_period or DEFAULT_DISCOUNT_BY_PERIOD
    total_claims = Decimal("0")
    total_financing = Decimal("0")
    rows: list[dict[str, str]] = []
    for index, item in enumerate(applications, start=1):
        principal = Decimal(str(item.get("principal") or 0))
        period = item.get("period")
        period_int = int(period) if period is not None else 12
        tariff = tariff_for_period(rates, period_int)
        discount = (principal * tariff).quantize(Decimal("1"))
        financing = principal - discount
        total_claims += principal
        total_financing += financing
        issued = _as_datetime(item.get("issued_at"))
        rows.append(
            {
                "n": str(index),
                "uuid": str(item.get("uuid") or ""),
                "issued_date": issued.strftime("%d.%m.%Y") if issued else "",
                "issued_time": issued.strftime("%H:%M") if issued else "",
                "principal": _money(principal),
                "period": str(period_int),
                "tariff": format_tariff_percent(tariff),
                "discount": _money(discount),
                "purchase_amount": _money(principal),
                "partner_name": PARTNER_NAME,
                "product_name": product_name(period_int),
                "status": DEFAULT_STATUS,
                "credit_contract": str(item.get("credit_contract") or ""),
                "financing_amount": _money(financing),
            }
        )

    header = {
        "contract_number": contract_number,
        "issue_date": issue_date.strftime("%d.%m.%Y"),
        "issue_day": f"{issue_date.day:02d}",
        "issue_month": _MONTHS_RU[issue_date.month - 1],
        "issue_month_kz": _MONTHS_KZ[issue_date.month - 1],
        "issue_year": str(issue_date.year),
        "company_name": company_name,
        "company_iik": company_iik,
        "client_signer": client_signer,
        "total_claims": _money(total_claims),
        "total_claims_text": amount_text_ru(total_claims),
        "total_claims_text_kz": amount_text_kz(total_claims),
        "total_financing": _money(total_financing),
        "total_financing_text": amount_text_ru(total_financing),
        "total_financing_text_kz": amount_text_kz(total_financing),
        "payment_amount": _money(total_claims),
        "payment_amount_text": amount_text_ru(total_claims),
        "partner": PARTNER_NAME,
        "applications_count": str(len(applications)),
    }
    return header, rows
