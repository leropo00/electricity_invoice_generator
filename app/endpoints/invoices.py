from collections import defaultdict
from datetime import date
import io

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import bindparam, extract, text
from sqlalchemy.orm import Session, joinedload, selectinload
from weasyprint import HTML

from app.database.models.configuration import SeasonDayType
from app.database.models.customer import ElectricityCustomer, CustomerContract
from app.database.models.invoice import ElectricityInvoice, ElectricityInvoiceItem
from app.database.models.measurement import ElectricityUsage
from app.database.session import get_db
from app.schema.invoice import CreateInvoice

router = APIRouter(
    prefix="/invoices",
    tags=["Electricity Invoices"],
)

@router.post("", status_code=status.HTTP_201_CREATED)
def create_invoice_record(
    data: CreateInvoice,
    session: Session = Depends(get_db),
 ):
    customer = session.query(ElectricityCustomer).filter(ElectricityCustomer.id == data.customer_id).first()    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Customer not found"
        )

    customer_contract = session.query(CustomerContract).options(
            joinedload(CustomerContract.provider, innerjoin=True)
        ).filter(CustomerContract.customer_id == data.customer_id).filter(CustomerContract.termination_date == None).first()    
    if not customer_contract:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Customer does not have an active contract"
        )
        
    count = session.query(ElectricityUsage).filter(
        extract("year", ElectricityUsage.measured_at) == data.year,
        extract("month", ElectricityUsage.measured_at) == data.month
    ).count()
    if count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No invoice records found for the selected time range"
        )

    total_price, total_consumption = calculate_total(session, data.year, data.month, customer.id)
    timeblock_usage = calculate_time_block_ranges(session, data.year, data.month, customer.id)

    issued_date = date.today()
    due_date = issued_date + relativedelta(days=data.days_payment_due)
    start_date = date(data.year, data.month, 1)
    service_date = start_date + relativedelta(months=1) - relativedelta(days=1)
    
    base_amount = total_price
    tax_amount = total_price * 0.22
    total_amount = base_amount + tax_amount
    
    invoice = ElectricityInvoice(
        contract_id=customer_contract.id,
        payment_reason=data.payment_reason,
        receiver_reference=data.receiver_reference,
        invoice_number=data.invoice_number,
        location_issued=data.location_issued,
        invoice_code=data.invoice_code,
        receiver_IBAN=customer_contract.provider.iban_number,
        due_date=issued_date,
        issued_date=due_date,
        service_date=service_date,
        base_amount=base_amount,
        tax_amount=tax_amount,
        total_amount=total_amount,
    )
    
    session.add(invoice)
    session.flush()
    
    for item in timeblock_usage:
        invoice_item = ElectricityInvoiceItem(
            electricity_invoice_id = invoice.id,
            name = 'Časovni block ' + str(item['time_block']),
            unit = 'kWh',
            quantity = item['consumption'],
            amount = item['price'],
            date_from = item['start_date'],
            date_to = item['end_date'],
        )
        session.add(invoice_item)

    session.commit()
    session.refresh(invoice)
    return invoice


@router.post("/{invoice_id}/document", status_code=status.HTTP_201_CREATED)
def create_invoice_pdf_document(
    invoice_id: int,
    session: Session = Depends(get_db),
 ):
    
    environment = Environment(loader=FileSystemLoader("templates"))
    report = environment.get_template("electricity_invoice.html")

    invoice = session.query(ElectricityInvoice).options(
        selectinload(ElectricityInvoice.items)
    ).filter(ElectricityInvoice.id == invoice_id).first()    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invoice not found"
        )
        
    customer_contract = session.query(CustomerContract).options(
            joinedload(CustomerContract.provider, innerjoin=True),
            joinedload(CustomerContract.customer, innerjoin=True)
        ).filter(CustomerContract.id == invoice.contract_id).first()    
    if not customer_contract:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Customer contract for invoice does not exists"
        )
        
    invoice_template_data = orm_object_to_dict_exclude_default(invoice, ['contract_id'])
    invoice_template_data['invoice_items'] = [orm_object_to_dict_exclude_default(item) for item in invoice.items]
            
    render_data = {
        'invoice': invoice_template_data,
        'contract': orm_object_to_dict_exclude_default(customer_contract, ['customer_id', 'provider_id', 'termination_date']),
        'provider': orm_object_to_dict_exclude_default(customer_contract.provider),
        'customer': orm_object_to_dict_exclude_default(customer_contract.customer),
    }
    
    print(render_data)
        
    pdf_buffer = io.BytesIO()
    HTML(string=report.render(render_data)).write_pdf(pdf_buffer)
    pdf_buffer.seek(0)
    
    filename = "Racun_" + invoice.invoice_number + ".pdf"
    # Step 3: Return as StreamingResponse
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename="+filename}
    )



def calculate_total(session: Session, year: int, month: int, customer_id: int):
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
    result = session.execute(query, {
        "customer_id": customer_id,
        "start_date": start_date,
        "end_date": end_date
    }).fetchone()

    # Access results
    total_price = result.total_price
    total_consumption = result.total_consumption

    return total_price, total_consumption


    
def calculate_time_block_ranges(session: Session, year: int, month: int, customer_id: int):     
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

    result = session.execute(query, {
        "month": month,
    }).all()
    
    for row in result:
        level, hour, day_type = row
        if day_type == SeasonDayType.WORKDAY.name:
            workday_blocks_with_hours[level].append(hour)
        elif day_type == SeasonDayType.OFFDAY.name:
            offday_blocks_with_hours[level].append(hour)

    union_keys = set(workday_blocks_with_hours.keys()) | set(offday_blocks_with_hours.keys())
    possible_time_blocks = sorted(list(union_keys))
    
    start_date = date(year, month, 1)
    end_date = start_date + relativedelta(months=1)
    
    timeblock_usage = []
        
    for time_block in possible_time_blocks:           
        price_sum, consumption_sum = 0.0, 0.0
          
        if time_block in workday_blocks_with_hours:
            price, consumption = calculate_time_block(session, start_date, end_date, customer_id, workday_blocks_with_hours[time_block], SeasonDayType.WORKDAY)
            price_sum += price
            consumption_sum += consumption

        if time_block in offday_blocks_with_hours:
            price, consumption = calculate_time_block(session, start_date, end_date, customer_id, offday_blocks_with_hours[time_block], SeasonDayType.OFFDAY)
            price_sum += price
            consumption_sum += consumption

        # it could be possible that price is 0 fro time block, but consumtion should still be present
        if consumption_sum > 0:
            timeblock_usage.append({'time_block': time_block, 'consumption': consumption_sum, 'price': price_sum, 'start_date': start_date, 'end_date': end_date})
        
    return timeblock_usage

def calculate_time_block(session: Session, start_date: date, end_date: date, customer_id: int, hours:list, day_type: SeasonDayType):

    query_string = '''
    SELECT COALESCE(SUM(eem.consumption_kwh * eem.price_per_kwh), 0) as total_price,
        COALESCE(SUM(eem.consumption_kwh), 0) as total_consumption
        FROM measurements_electricity_usage eem 
        WHERE  eem.customer_id = :customer_id
        AND  eem.measured_at >= DATE :start_date
        AND eem.measured_at < DATE :end_date
        AND EXTRACT(HOUR FROM eem.measured_at) IN :hours
    '''    
    
    # national holidays are currently ignored in the calculation for offdays
    if day_type == SeasonDayType.OFFDAY:
        query_string += ' AND EXTRACT(DOW FROM eem.measured_at) IN (0, 6) '
    
    elif day_type == SeasonDayType.WORKDAY:
        query_string += ' AND EXTRACT(DOW FROM eem.measured_at) BETWEEN 1 AND 5'

    query = text(query_string).bindparams(bindparam("hours", expanding=True))

    result = session.execute(query, {
        "customer_id": customer_id,
        "start_date": start_date,
        "end_date": end_date,
        "hours": hours,
    }).fetchone()

    total_price = result.total_price
    total_consumption = result.total_consumption
    return total_price, total_consumption


def orm_object_to_dict_exclude_default(obj, exclude_fields=None):
    exclude_default = ['id', 'created_at', 'updated_at']
    if exclude_fields:
        exclude_default.extend(exclude_fields)
    return orm_object_to_dict(obj, set(exclude_default))

def orm_object_to_dict(obj, exclude_fields=None):
    exclude_fields = exclude_fields or set()
    #Relationships aren’t part of __table__.columns, so they’re already excluded by default. 
    return {
        column.name: getattr(obj, column.name)
        for column in obj.__table__.columns
        if column.name not in exclude_fields
    }