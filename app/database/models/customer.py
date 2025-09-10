from datetime import datetime
from enum import Enum
from typing import List

from sqlalchemy import  DateTime, Enum as SqlEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base
from ..mixins import TimestampMixin


class CustomerType(Enum):
    # gospodinjstvo value as present on invoice
    RESIDENTIAL = "residential"
    # values I personaly defined
    BUSINESS = "business"
    MUNICIPIAL = "municipal"


class ElectricityCustomer(Base, TimestampMixin):
    __tablename__ = "electricity_customers"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    fullname: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String)
    tax_code: Mapped[str] = mapped_column(String)

    street_address: Mapped[str] = mapped_column(String)
    zip_code: Mapped[int] = mapped_column(Integer)
    zip_name: Mapped[str] = mapped_column(String)
    
    contracts: Mapped[List["CustomerContract"]] = relationship(
        back_populates="customer",
        cascade="all, delete",
    )

class ElectricityProvider(Base, TimestampMixin):
    __tablename__ = "electricity_providers"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    full_title: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String)    
    webpage: Mapped[str] = mapped_column(String)

    tax_code: Mapped[str] = mapped_column(String)
    iban_number: Mapped[str] = mapped_column(String)

    street_address: Mapped[str] = mapped_column(String)
    zip_code: Mapped[int] = mapped_column(Integer)
    zip_name: Mapped[str] = mapped_column(String)

    contracts: Mapped[List["CustomerContract"]] = relationship(
        back_populates="provider",
        cascade="all, delete",
    )


class CustomerContract(Base, TimestampMixin):
    __tablename__ = "electricity_customers_contracts"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider_id: Mapped[int] = mapped_column(ForeignKey("electricity_providers.id"))
    provider: Mapped["ElectricityProvider"] = relationship("ElectricityProvider", back_populates="contracts")

    customer_id: Mapped[int] = mapped_column(ForeignKey("electricity_customers.id"))
    customer: Mapped["ElectricityCustomer"] = relationship("ElectricityCustomer", back_populates="contracts")

    customer_type: Mapped[CustomerType] = mapped_column(
        SqlEnum(CustomerType, name="electricity_customers_contracts_type", native_enum=True), nullable=False
    )

    contract_number: Mapped[str] = mapped_column(String, unique=True)
    energy_meter_number: Mapped[str] = mapped_column(String)
    package_name: Mapped[str] = mapped_column(String)

    # when terminated, it is no longer an active contract
    termination_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
