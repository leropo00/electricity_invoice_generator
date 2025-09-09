from pydantic import BaseModel, EmailStr

from app.schema.custom_type import ZipCode


class CustomerCreate(BaseModel):
    fullname: str
    email: EmailStr
    tax_code: str
    street_address: str
    zip_code: ZipCode
    zip_name: str


class CustomerUpdate(BaseModel):
    fullname: str
    email: EmailStr
    tax_code: str
    street_address: str
    zip_code: ZipCode
    zip_name: str
