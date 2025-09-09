from pydantic import BaseModel

class CreateInvoice(BaseModel):
    customer_id: int
    month: int
    year: int