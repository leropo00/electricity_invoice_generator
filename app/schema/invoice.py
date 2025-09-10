from app.schema.custom_type import MonthType, YearType

from pydantic import BaseModel


class CreateInvoice(BaseModel):
    customer_id: int
    month: MonthType
    year: YearType
    payment_reason: str
    receiver_reference: str
    invoice_number: str
    location_issued: str
    invoice_code: str = "OTHR"
    days_payment_due: int = 15
