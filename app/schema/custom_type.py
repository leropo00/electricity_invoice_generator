from typing import Annotated

from pydantic import AfterValidator


def validate_four_digit_zip(value: int) -> int:
    if not (1000 <= value <= 9999):
        raise ValueError("zip_code must be exactly 4 digits")
    return value


ZipCode = Annotated[int, AfterValidator(validate_four_digit_zip)]


def validate_month(value: int) -> int:
    if not (1 <= value <= 12):
        raise ValueError("month must be inside 1 -12 range")
    return value


MonthType = Annotated[int, AfterValidator(validate_month)]


def validate_year(value: int) -> int:
    if not (value >= 1990):
        raise ValueError("aloowed year are from 1990 onwards")
    return value


YearType = Annotated[int, AfterValidator(validate_year)]
