from pydantic import BaseModel, EmailStr, HttpUrl

from app.database.models.customer import CustomerType
from app.schema.custom_type import ZipCode

class ProviderCreate(BaseModel):
    full_title: str
    email: EmailStr
    webpage: HttpUrl
    tax_code: str
    iban_number: str
    street_address: str
    zip_code: ZipCode
    zip_name: str


class ProviderUpdate(BaseModel):
    full_title: str
    email: EmailStr
    webpage: HttpUrl
    tax_code: str
    iban_number: str
    street_address: str
    zip_code: ZipCode
    zip_name: str

