from pydantic import AfterValidator
from typing import Annotated

def validate_four_digit_zip(value: int) -> int:
    if not (1000 <= value <= 9999):
        raise ValueError("zip_code must be exactly 4 digits")
    return value


ZipCode = Annotated[int, AfterValidator(validate_four_digit_zip)]
