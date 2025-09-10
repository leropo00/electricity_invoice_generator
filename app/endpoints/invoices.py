from collections import defaultdict
from datetime import date
import io

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import extract, select
from sqlalchemy.orm import Session, joinedload, selectinload
from weasyprint import HTML

from app.database.models.configuration import SeasonDayType
from app.database.models.customer import ElectricityCustomer, CustomerContract
from app.database.models.invoice import ElectricityInvoice, ElectricityInvoiceItem
from app.database.models.measurement import ElectricityUsage
from app.database.session import get_db
from app.schema.invoice import CreateInvoice
from app.utils.invoice import calculate_measurements_total_usage, calculate_measurements_time_block_usage
from app.utils.serialization import orm_object_to_dict_exclude_default

router = APIRouter(
    prefix="/invoices",
    tags=["Electricity Invoices"],
)


@router.get("/")
def all_invoices(session: Session = Depends(get_db)):
    return session.execute(select(ElectricityInvoice)).scalars().all()

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

    total_price, total_consumption = calculate_measurements_total_usage(session, data.year, data.month, customer.id)
    timeblock_usage = calculate_measurements_time_block_usage(session, data.year, data.month, customer.id)

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


@router.post("/{invoice_id}/document")
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