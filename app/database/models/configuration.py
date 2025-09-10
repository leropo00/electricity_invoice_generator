from enum import Enum
from typing import List

from sqlalchemy import (
    Boolean,
    Computed,
    CheckConstraint,
    Enum as SqlEnum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base
from ..mixins import TimestampMixin


class ElectricitySeason(Base, TimestampMixin):
    __tablename__ = "config_electricity_seasons"
    __table_args__ = (
        CheckConstraint(
            "start_month >= 1 AND start_month <= 12 AND end_month >= 1 AND end_month <= 12",
            name="electricity_seasons_month_values",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    season_key: Mapped[str] = mapped_column(String)
    season_name: Mapped[str] = mapped_column(String)
    start_month: Mapped[int] = mapped_column(Integer)
    end_month: Mapped[int] = mapped_column(Integer)

    crosses_calendar_year: Mapped[bool] = mapped_column(
        Boolean, Computed("start_month > end_month", persisted=True)
    )
    hours: Mapped[List["HourlyBlockLevel"]] = relationship(
        back_populates="electricity_season",
        cascade="all, delete",
    )


class SeasonDayType(Enum):
    WORKDAY = "workday"
    OFFDAY = "offday"


class HourlyBlockLevel(Base, TimestampMixin):
    __tablename__ = "config_hourly_block_levels"
    __table_args__ = (
        CheckConstraint("level >= 1 AND level <= 5", name="hourly_block_levels_valid"),
        CheckConstraint(
            "hour >= 0 AND hour <= 23", name="hourly_block_levels_hours_valid"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    level: Mapped[int] = mapped_column(Integer)
    hour: Mapped[int] = mapped_column(Integer)
    day_type: Mapped[SeasonDayType] = mapped_column(
        SqlEnum(SeasonDayType, name="hourly_block_levels_day_type", native_enum=True),
        nullable=False,
    )

    electricity_season_id: Mapped[int] = mapped_column(
        ForeignKey("config_electricity_seasons.id")
    )
    electricity_season: Mapped["ElectricitySeason"] = relationship(
        "ElectricitySeason", back_populates="hours"
    )
