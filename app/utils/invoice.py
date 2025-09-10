from collections import defaultdict
from datetime import date
import io

from dateutil.relativedelta import relativedelta
from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

from app.database.models.configuration import SeasonDayType

__all__ = [
    "calculate_measurements_total_usage",
    "calculate_measurements_time_block_usage",
]


def calculate_measurements_total_usage(
    session: Session, year: int, month: int, customer_id: int
):
    start_date = date(year, month, 1)
    end_date = start_date + relativedelta(months=1)

    # Raw SQL query with named parameters
    query = text("""
        SELECT 
            COALESCE(SUM(eem.consumption_kwh * eem.price_per_kwh), 0) AS total_price,
            COALESCE(SUM(eem.consumption_kwh), 0) AS total_consumption
        FROM measurements_electricity_usage eem
        WHERE eem.customer_id = :customer_id
        AND eem.measured_at >= :start_date
        AND eem.measured_at < :end_date
    """)

    # Execute with parameters
    result = session.execute(
        query,
        {"customer_id": customer_id, "start_date": start_date, "end_date": end_date},
    ).fetchone()

    # Access results
    total_price = result.total_price
    total_consumption = result.total_consumption

    return total_price, total_consumption


def calculate_measurements_time_block_usage(
    session: Session, year: int, month: int, customer_id: int
):
    workday_blocks_with_hours = defaultdict(list)
    offday_blocks_with_hours = defaultdict(list)

    query = text("""
        SELECT l.level, l.hour, l.day_type
        FROM config_electricity_seasons s
        JOIN config_hourly_block_levels l on s.id = l.electricity_season_id
        WHERE  (s.crosses_calendar_year = FALSE AND s.start_month <= :month AND  s.end_month  >= :month )
        OR (s.crosses_calendar_year = TRUE AND ( s.start_month <= :month AND  s.end_month  >= :month ) )
        ORDER BY l.day_type, l.level, l.hour
    """)

    result = session.execute(
        query,
        {
            "month": month,
        },
    ).all()

    for row in result:
        level, hour, day_type = row
        if day_type == SeasonDayType.WORKDAY.name:
            workday_blocks_with_hours[level].append(hour)
        elif day_type == SeasonDayType.OFFDAY.name:
            offday_blocks_with_hours[level].append(hour)

    union_keys = set(workday_blocks_with_hours.keys()) | set(
        offday_blocks_with_hours.keys()
    )
    possible_time_blocks = sorted(list(union_keys))

    start_date = date(year, month, 1)
    end_date = start_date + relativedelta(months=1)

    # this is final date of the range
    final_date_measurements = end_date - relativedelta(days=1)

    timeblock_usage = []

    for time_block in possible_time_blocks:
        price_sum, consumption_sum = 0.0, 0.0

        if time_block in workday_blocks_with_hours:
            price, consumption = _calculate_time_block(
                session,
                start_date,
                end_date,
                customer_id,
                workday_blocks_with_hours[time_block],
                SeasonDayType.WORKDAY,
            )
            price_sum += price
            consumption_sum += consumption

        if time_block in offday_blocks_with_hours:
            price, consumption = _calculate_time_block(
                session,
                start_date,
                end_date,
                customer_id,
                offday_blocks_with_hours[time_block],
                SeasonDayType.OFFDAY,
            )
            price_sum += price
            consumption_sum += consumption

        # it could be possible that price is 0 fro time block, but consumtion should still be present
        if consumption_sum > 0:
            timeblock_usage.append(
                {
                    "time_block": time_block,
                    "consumption": consumption_sum,
                    "price": price_sum,
                    "start_date": start_date,
                    "end_date": final_date_measurements,
                }
            )

    return timeblock_usage


def _calculate_time_block(
    session: Session,
    start_date: date,
    end_date: date,
    customer_id: int,
    hours: list,
    day_type: SeasonDayType,
):
    query_string = """
    SELECT COALESCE(SUM(eem.consumption_kwh * eem.price_per_kwh), 0) as total_price,
        COALESCE(SUM(eem.consumption_kwh), 0) as total_consumption
        FROM measurements_electricity_usage eem 
        WHERE  eem.customer_id = :customer_id
        AND  eem.measured_at >= DATE :start_date
        AND eem.measured_at < DATE :end_date
        AND EXTRACT(HOUR FROM eem.measured_at) IN :hours
    """

    # national holidays are currently ignored in the calculation for offdays
    if day_type == SeasonDayType.OFFDAY:
        query_string += " AND EXTRACT(DOW FROM eem.measured_at) IN (0, 6) "

    elif day_type == SeasonDayType.WORKDAY:
        query_string += " AND EXTRACT(DOW FROM eem.measured_at) BETWEEN 1 AND 5"

    query = text(query_string).bindparams(bindparam("hours", expanding=True))

    result = session.execute(
        query,
        {
            "customer_id": customer_id,
            "start_date": start_date,
            "end_date": end_date,
            "hours": hours,
        },
    ).fetchone()

    total_price = result.total_price
    total_consumption = result.total_consumption
    return total_price, total_consumption
