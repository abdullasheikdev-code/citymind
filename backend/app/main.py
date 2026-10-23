from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import (
    auth_router,
    simulate_router,
    simulate_extra_router,
    scenarios_router,
    reports_router,
    knowledge_base_router,
    city_router,
    analytics_router,
)

app = FastAPI(
    title="CityMind API",
    description="Intelligent Urban Simulation and Decision Support Platform",
    version="1.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Deployed Vercel frontend
        "https://citymind-g88k.vercel.app",

        # Local development
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
        "http://localhost:3003",
        "http://127.0.0.1:3003",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(auth_router.router)
app.include_router(simulate_router.router)
app.include_router(simulate_extra_router.router)
app.include_router(scenarios_router.router)
app.include_router(reports_router.router)
app.include_router(knowledge_base_router.router)
app.include_router(city_router.router)
app.include_router(analytics_router.router)


# Root endpoint
@app.get("/")
def root():
    return {
        "name": "CityMind API",
        "status": "running",
        "version": "1.0.0",
    }


# Health-check endpoint
@app.get("/health")
def health():
    return {
        "status": "healthy",
    }