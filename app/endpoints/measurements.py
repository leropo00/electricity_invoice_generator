from datetime import datetime
from io import StringIO
import re
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, status, UploadFile
import pandas as pd
from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session

from app.database.models.customer import ElectricityCustomer
from app.database.session import get_db
from app.database.models.measurement import ElectricityUsage
from app.schema.custom_type import MonthType, YearType
from app.schema.measurement import (
    MeasurementDeleteRequests,
    MeasurementCreateResponse,
    MeasurementDeleteResponse,
    MeasurementStatsResponse,
)

router = APIRouter(
    prefix="/measurements",
    tags=["Electricity Measurements"],
)


@router.post("/upload-csv", status_code=status.HTTP_201_CREATED)
def upload_csv(
    file: UploadFile = File(...),
    session: Session = Depends(get_db),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Only CSV files are allowed"
        )

    regex_customer_id = re.search(r"-(\d+)\.csv$", file.filename.lower())
    if not regex_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename has no information about supplier id, this should be in form -id.csv",
        )

    customer_id = regex_customer_id.group(1)
    db_item = (
        session.query(ElectricityCustomer)
        .filter(ElectricityCustomer.id == customer_id)
        .first()
    )
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )

    sql_columns = [
        "customer_id",
        "measured_at",
        "consumption_kwh",
        "price_per_kwh",
        "created_at",
        "updated_at",
    ]
    df = pd.read_csv(file.file, sep=";", decimal=",")
    df = df.rename(
        columns={
            df.columns[0]: sql_columns[1],
            df.columns[1]: sql_columns[2],
            df.columns[2]: sql_columns[3],
        }
    )
    df["customer_id"] = customer_id
    df["created_at"] = datetime.now()
    df["updated_at"] = df["created_at"]
    df = df[sql_columns]

    buffer = StringIO()
    df.to_csv(buffer, index=False, header=False, sep=";")
    buffer.seek(0)

    connection = session.connection().connection
    cursor = connection.cursor()

    try:
        # Execute COPY FROM using psycopg2
        cursor.copy_from(buffer, "measurements_electricity_usage", sep=";")
        # Commit the transaction
        connection.commit()
        return MeasurementCreateResponse(records_added=len(df))
    except Exception as e:
        connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="str(e)"
        )
    finally:
        cursor.close()


@router.get("/stats")
def customer_id(
    customer_id: Optional[int] = None,
    month: Optional[MonthType] = None,
    year: Optional[YearType] = None,
    session: Session = Depends(get_db),
):
    query = session.query(func.count(ElectricityUsage.measured_at))
    if customer_id:
        query = query.filter(ElectricityUsage.customer_id == customer_id)
    if month:
        query = query.filter(extract("month", ElectricityUsage.measured_at) == month)
    if year:
        query = query.filter(extract("year", ElectricityUsage.measured_at) == year)
    return MeasurementStatsResponse(records_count=query.scalar())


# POST is used since DELETE with a body is not universally supported by all clients and proxies
@router.post("/remove-measurements")
def remove_measurements(
    data: MeasurementDeleteRequests, session: Session = Depends(get_db)
):
    query = (
        session.query(ElectricityUsage)
        .filter(ElectricityUsage.customer_id == data.customer_id)
        .filter(extract("month", ElectricityUsage.measured_at) == data.month)
        .filter(extract("year", ElectricityUsage.measured_at) == data.year)
    )
    records_removed = query.delete(synchronize_session=False)
    session.commit()
    return MeasurementDeleteResponse(records_removed=records_removed)
