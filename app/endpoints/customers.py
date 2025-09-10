from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.database.models.customer import (
    ElectricityCustomer,
    CustomerContract,
    ElectricityProvider,
)
from app.schema.customer import (
    CustomerCreate,
    CustomerUpdate,
    CustomerContractCreate,
    CustomerContractUpdate,
)


router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
)


@router.get("/")
def all_customers(session: Session = Depends(get_db)):
    return session.execute(select(ElectricityCustomer)).scalars().all()


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_customer(
    data: CustomerCreate,
    session: Session = Depends(get_db),
):
    db_item = ElectricityCustomer(
        fullname=data.fullname,
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


@router.get("/{customer_id}")
def customer_details(customer_id: int, session: Session = Depends(get_db)):
    customer_item = (
        session.query(ElectricityCustomer)
        .filter(ElectricityCustomer.id == customer_id)
        .first()
    )
    if not customer_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )

    active_contract = (
        session.query(CustomerContract)
        .filter(CustomerContract.customer_id == customer_id)
        .filter(CustomerContract.termination_date == None)
        .first()
    )
    if active_contract:
        customer_item.active_contract = active_contract

    return customer_item


@router.put("/{customer_id}")
def update_customer(
    customer_id: int, data: CustomerUpdate, session: Session = Depends(get_db)
):
    db_item = (
        session.query(ElectricityCustomer)
        .filter(ElectricityCustomer.id == customer_id)
        .first()
    )
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )
    db_item.fullname = data.fullname
    db_item.email = data.email
    db_item.tax_code = data.tax_code
    db_item.zip_name = data.zip_name
    db_item.zip_code = data.zip_code
    db_item.street_address = data.street_address

    session.commit()
    session.refresh(db_item)
    return db_item


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(customer_id: int, session: Session = Depends(get_db)):
    db_item = (
        session.query(ElectricityCustomer)
        .filter(ElectricityCustomer.id == customer_id)
        .first()
    )
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )

    session.delete(db_item)
    session.commit()


@router.post("/{customer_id}/electricity_contract", status_code=status.HTTP_201_CREATED)
def create_customer_contract(
    customer_id: int,
    data: CustomerContractCreate,
    session: Session = Depends(get_db),
):
    customer_item = (
        session.query(ElectricityCustomer)
        .filter(ElectricityCustomer.id == customer_id)
        .first()
    )
    if not customer_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )

    active_contract = (
        session.query(CustomerContract)
        .filter(CustomerContract.customer_id == customer_id)
        .filter(CustomerContract.termination_date == None)
        .first()
    )
    if active_contract:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Active contract for customer already exists",
        )

    existing_contract_number = (
        session.query(CustomerContract)
        .filter(CustomerContract.contract_number == data.contract_number)
        .first()
    )
    if existing_contract_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contract number already exits. Contract number must be unique over all users",
        )

    db_item = CustomerContract(
        customer_id=customer_id,
        provider_id=data.provider_id,
        customer_type=data.customer_type,
        contract_number=data.contract_number,
        energy_meter_number=data.energy_meter_number,
        package_name=data.package_name,
    )

    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


@router.put("/{customer_id}/electricity_contract/{contract_id}")
def update_customer_contract(
    customer_id: int,
    contract_id: int,
    data: CustomerContractUpdate,
    session: Session = Depends(get_db),
):
    customer_item = (
        session.query(ElectricityCustomer)
        .filter(ElectricityCustomer.id == customer_id)
        .first()
    )
    if not customer_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found"
        )

    db_item = (
        session.query(CustomerContract)
        .filter(CustomerContract.id == contract_id)
        .first()
    )
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer contract not found"
        )

    existing_contract_number = (
        session.query(CustomerContract)
        .filter(CustomerContract.contract_number == data.contract_number)
        .filter(CustomerContract.id != data.customer_id)
        .first()
    )
    if existing_contract_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contract number already exits. Contract number must be unique over all users",
        )

    db_item.customer_id = customer_id
    db_item.provider_id = data.provider_id
    db_item.customer_type = data.customer_type
    db_item.contract_number = data.contract_number
    db_item.energy_meter_number = data.energy_meter_number
    db_item.package_name = data.customer_typackage_namepe

    session.commit()
    session.refresh(db_item)
    return db_item


@router.post("/{customer_id}/electricity_contract/{contract_id}/terminate")
def terminate_customer_contract(
    customer_id: int,
    contract_id: int,
    session: Session = Depends(get_db),
):
    db_item = (
        session.query(CustomerContract)
        .filter(CustomerContract.id == contract_id)
        .first()
    )
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer contract not found"
        )

    if db_item.termination_date is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contract already terminated",
        )

    db_item.termination_date = datetime.now()

    session.commit()
    session.refresh(db_item)
    return db_item
