from __future__ import annotations
import os
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title="OpsAgent - AI Operational Assistant API",
    description="End-to-End Enterprise Operational AI Agent for Coal Distribution & Logistics.",
    version="1.0.0",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = (time.perf_counter() - start_time) * 1000.0
    response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
    return response


@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "ok",
        "service": "opsagent_backend",
        "version": "1.0.0",
        "environment": settings.APP_ENV,
        "llm_provider": settings.DEFAULT_LLM_PROVIDER,
        "router_model": settings.ROUTER_MODEL,
        "synthesis_model": settings.SYNTHESIS_MODEL,
    }

# Mount API Routers
from app.api.v1.endpoints.search import router as search_router
from app.api.v1.endpoints.chat import router as chat_router
from app.api.v1.endpoints.approval import router as approval_router

app.include_router(search_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(approval_router, prefix="/api")



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.BACKEND_HOST, port=settings.BACKEND_PORT, reload=True)
