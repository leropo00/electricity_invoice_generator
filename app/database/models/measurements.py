from datetime import datetime

from sqlalchemy import DateTime, desc, ForeignKey, Float, Index
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base
from ..mixins import TimestampDBMixin


class ElectricityUsage(Base, TimestampDBMixin):
    __tablename__ = "measurements_electricity_usage"    
    __table_args__ = (
        Index("ix_customer_electricity_measurements", "customer_id", desc("measured_at")),
    )

    customer_id: Mapped[int] = mapped_column(ForeignKey("electricity_customers.id"), primary_key=True, nullable=False)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True, nullable=False )

    consumption_kwh: Mapped[float] = mapped_column(Float)
    price_per_kwh: Mapped[float] = mapped_column(Float)
