from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.database.models.customer import ElectricityProvider
from app.schema.provider import ProviderCreate, ProviderUpdate

router = APIRouter(
    prefix="/providers",
    tags=["Providers"],
)


@router.get("/")
def all_providers(session: Session = Depends(get_db)):
    return session.execute(select(ElectricityProvider)).scalars().all()


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_provider(data: ProviderCreate, session: Session = Depends(get_db)):
    db_item = ElectricityProvider(
        full_title=data.full_title,
        email=data.email,
        webpage=str(data.webpage),
        tax_code=data.tax_code,
        iban_number=data.iban_number,
        street_address=data.street_address,
        zip_code=data.zip_code,
        zip_name=data.zip_name,
    )
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


@router.put("/{provider_id}")
def update_provider(
    provider_id: int, data: ProviderUpdate, session: Session = Depends(get_db)
):
    db_item = (
        session.query(ElectricityProvider)
        .filter(ElectricityProvider.id == provider_id)
        .first()
    )
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found"
        )
    db_item.full_title = data.full_title
    db_item.email = data.email
    db_item.webpage = str(data.webpage)
    db_item.tax_code = data.tax_code
    db_item.iban_number = data.iban_number
    db_item.street_address = data.street_address
    db_item.zip_code = data.zip_code
    db_item.zip_name = data.zip_name

    session.commit()
    session.refresh(db_item)
    return db_item


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_provider(provider_id: int, session: Session = Depends(get_db)):
    db_item = (
        session.query(ElectricityProvider)
        .filter(ElectricityProvider.id == provider_id)
        .first()
    )
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found"
        )

    session.delete(db_item)
    session.commit()
