from sqlalchemy import  Boolean, Computed, CheckConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base
from ..mixins import TimestampMixin


class ElectricitySeasons(Base, TimestampMixin):
    __tablename__ = "config_electricity_seasons"
    __table_args__ = (
        CheckConstraint("start_month >= 1 AND start_month <= 12 AND end_month >= 1 AND end_month <= 12", name="electricity_seasons_month_values"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    season_key: Mapped[str] = mapped_column(String)
    season_name: Mapped[str] = mapped_column(String)
    
    start_month: Mapped[int] = mapped_column(Integer)
    end_month: Mapped[int] = mapped_column(Integer)

    crosses_calendar_year: Mapped[bool] = mapped_column(
        Boolean,
        Computed("start_month > end_month", persisted=True)
    )
