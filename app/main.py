from fastapi import APIRouter, FastAPI

from .endpoints.providers import router as router_providers


app = FastAPI()

router = APIRouter()
router.include_router(router_providers)

app.include_router(router)
