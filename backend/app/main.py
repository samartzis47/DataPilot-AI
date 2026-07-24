from fastapi import FastAPI

app = FastAPI(
    title="DataPilot-AI",
    description="DataPilot-AI is a powerful AI-powered data analysis tool that helps you extract insights from your data.",
    version="0.1.0",
)

@app.get("/health")
def health_check():
    return {
        "status": "running",
        "service": "DataPilot-AI",
    }