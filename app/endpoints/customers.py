from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.database.models.customer import ElectricityCustomer
from app.schema.customer import CustomerCreate


router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
)

@router.get("/")
def all_customers(session: Session = Depends(get_db)):
    return session.execute(select(ElectricityCustomer)).scalars().all()



@router.post("/")
def create_customer(
       data: CustomerCreate,
       session: Session = Depends(get_db)
 ):
    db_item = ElectricityCustomer(fullname=data.fullname,
                      email=data.email,
                      tax_code=data.tax_code, 
                      zip_name=data.zip_name,
                      zip_code=data.zip_code,
                      street_address=data.street_address,
                )
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item



@router.put("/{customer_id}")
def update_customer(
    customer_id: int,
    data: CustomerCreate,
    session: Session = Depends(get_db)
 ):    
    db_item = session.query(ElectricityCustomer).filter(ElectricityCustomer.id == customer_id).first()
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )
    db_item.fullname=data.fullname,
    db_item.email=data.email,
    db_item.tax_code=data.tax_code, 
    db_item.zip_name=data.zip_name,
    db_item.zip_code=data.zip_code,
    db_item.street_address=data.street_address,
    
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item