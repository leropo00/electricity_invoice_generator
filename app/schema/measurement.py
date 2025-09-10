from app.schema.custom_type import MonthType, YearType

from pydantic import BaseModel


class MeasurementDeleteRequests(BaseModel):
    customer_id: int
    month: MonthType
    year: YearType


class MeasurementStatsResponse(BaseModel):
    records_count: int


class MeasurementCreateResponse(BaseModel):
    records_added: int


class MeasurementDeleteResponse(BaseModel):
    records_removed: int
