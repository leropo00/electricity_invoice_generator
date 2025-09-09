from pydantic import BaseModel, EmailStr

from app.database.models.customer import CustomerType
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

class CustomerContractCreate(BaseModel):
    provider_id: int
    customer_type: CustomerType
    contract_number: str
    energy_meter_number: str
    package_name: str


class CustomerContractUpdate(BaseModel):
    provider_id: int
    customer_type: CustomerType
    contract_number: str
    energy_meter_number: str
    package_name: str
