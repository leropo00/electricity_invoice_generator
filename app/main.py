from fastapi import APIRouter, FastAPI

from .endpoints.providers import router as router_providers
from .endpoints.customers import router as router_customers


app = FastAPI()

router = APIRouter()
router.include_router(router_providers)
router.include_router(router_customers)

app.include_router(router)
