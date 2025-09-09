from datetime import datetime
from typing import List

from sqlalchemy import  DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship, Mapped, mapped_column

from ..base import Base
from ..mixins import TimestampMixin


class ElectricityInvoice(Base, TimestampMixin):
    __tablename__ = "electricity_invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    contract_id: Mapped[int] = mapped_column(ForeignKey("electricity_customers_contracts.id"))

    invoice_number: Mapped[str] = mapped_column(String)    
    issued_date: Mapped[datetime] = mapped_column(DateTime)    
    service_date: Mapped[datetime] = mapped_column(DateTime)
    location_issued: Mapped[str] = mapped_column(String)
    due_date: Mapped[datetime] = mapped_column(DateTime)

    # koda namena
    invoice_code: Mapped[str] = mapped_column(String)
    # payment reason
    payment_reason: Mapped[str] = mapped_column(String)
    # IBAN prejemnika    
    receiver_IBAN: Mapped[str] = mapped_column(String)
    # referenca prejemnika    
    receiver_reference: Mapped[str] = mapped_column(String)

    base_amount: Mapped[float] = mapped_column(Float)
    tax_amount: Mapped[float] = mapped_column(Float)
    total_amount: Mapped[float] = mapped_column(Float)
    
    items: Mapped[List["ElectricityInvoiceItem"]] = relationship(
        back_populates="electricity_invoice",
        cascade="all, delete",
    )


class ElectricityInvoiceItem(Base, TimestampMixin):
    __tablename__ = "electricity_invoices_items"

    id: Mapped[int] = mapped_column(primary_key=True)

    electricity_invoice_id: Mapped[int] = mapped_column(ForeignKey("electricity_invoices.id"))
    electricity_invoice: Mapped["ElectricityInvoice"] = relationship("ElectricityInvoice", back_populates="items")

    name: Mapped[str] = mapped_column(String)
    unit: Mapped[str] = mapped_column(String)
    quantity: Mapped[int] = mapped_column(Integer)
    amount: Mapped[float] = mapped_column(Float)

    date_from: Mapped[datetime] = mapped_column(DateTime)
    date_to: Mapped[datetime] = mapped_column(DateTime)
