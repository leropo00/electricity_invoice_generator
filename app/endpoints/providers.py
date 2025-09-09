from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.database.models.customer import ElectricityProvider


router = APIRouter(
    prefix="/providers",
    tags=["Providers"],
)

@router.get("/")
def all_providers(session: Session = Depends(get_db)):
    return session.execute(select(ElectricityProvider)).scalars().all()
