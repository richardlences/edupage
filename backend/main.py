from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from models import User, Rating, Photo # Ensure models are registered

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://edupage.ddns.net", "http://localhost:5173", "http://localhost:4173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

from fastapi.staticfiles import StaticFiles
from routers import auth, lunches, social
import os

app.include_router(auth.router, prefix="/api")
app.include_router(lunches.router, prefix="/api")
app.include_router(social.router, prefix="/api")

# Mount uploads directory (keep for backward compatibility / local storage)
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
def read_root():
    return {"Hello": "World"}

