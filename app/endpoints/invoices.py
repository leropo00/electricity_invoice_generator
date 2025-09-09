import io

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import extract
from sqlalchemy.orm import Session
from weasyprint import HTML

from app.database.models.customer import ElectricityCustomer
from app.database.models.measurements import ElectricityUsage
from app.database.session import get_db
from app.schema.invoice import CreateInvoice

router = APIRouter(
    prefix="/invoices",
    tags=["Electricity Invoices"],
)

@router.post("", status_code=status.HTTP_201_CREATED)
def create_invoice_pdf_document(
    data: CreateInvoice,
    session: Session = Depends(get_db),
 ):
    db_item = session.query(ElectricityCustomer).filter(ElectricityCustomer.id == data.customer_id).first()
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Customer not found"
        )

    count = session.query(ElectricityUsage).filter(
        extract("year", ElectricityUsage.measured_at) == data.year,
        extract("month", ElectricityUsage.measured_at) == data.month
    ).count()
    if count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No records found for the selected time"
        )


    ## create invoice

    return {"status": "success", "count": str(count)}

@router.post("/{invoice_id}/document", status_code=status.HTTP_201_CREATED)
def create_invoice_pdf_document(
    invoice_id: int,
    session: Session = Depends(get_db),
 ):
    
    environment = Environment(loader=FileSystemLoader("templates"))
    report = environment.get_template("electricity_invoice.html")

    render_data: dict = {'company_name': 'Bisol Doo', 'invoice_number': '1234567890', 'due_date': '12.12.2024'}
    
    render_data['usage_details'] = []
    
    
    pdf_buffer = io.BytesIO()
    HTML(string=report.render(render_data)).write_pdf(pdf_buffer)
    pdf_buffer.seek(0)

    # Step 3: Return as StreamingResponse
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=invoice.pdf"}
    )
