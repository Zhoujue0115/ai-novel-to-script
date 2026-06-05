from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.script import router as script_router

app = FastAPI(title="AI Novel to Script", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(script_router, prefix="/api/script")


@app.get("/health")
def health():
    return {"status": "ok"}
