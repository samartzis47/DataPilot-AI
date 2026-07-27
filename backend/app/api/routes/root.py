from fastapi import APIRouter

router = APIRouter(
    tags=["General"],
)

@router.get("/")
def read_root():
    return{
        "name": "DataPilot-AI",
        "message": "DataPilot -AI API is running",
        "version": "0.1.0",
        "documentation": "/docs",
    }