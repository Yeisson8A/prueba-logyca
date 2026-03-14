from fastapi import FastAPI
import uvicorn
from app.config.database_config import engine, Base
from app.routes import sales_routes
from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Logyca Automation API",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Agregar rutas
app.include_router(sales_routes.router)