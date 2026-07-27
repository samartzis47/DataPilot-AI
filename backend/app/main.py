from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.root import router as root_router


app = FastAPI(
    title="DataPilot-AI",
    description=(
        "DataPilot-AI is a powerful AI-powered data analysis tool "
        "that helps you extract insights from your data."
    ),
    version="0.1.0",
)


app.include_router(root_router)
app.include_router(health_router)