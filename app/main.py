from fastapi import APIRouter, FastAPI

from .endpoints.customers import router as router_customers
from .endpoints.invoices import router as router_invoices
from .endpoints.measurements import router as router_measurements
from .endpoints.providers import router as router_providers


app = FastAPI()

router = APIRouter()
router.include_router(router_customers)
router.include_router(router_invoices)
router.include_router(router_measurements)
router.include_router(router_providers)

app.include_router(router)
