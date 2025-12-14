from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models import User
from database import SessionLocal
from edupage_service import EdupageService
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class LoginRequest(BaseModel):
    username: str
    password: str
    subdomain: str

@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    service = EdupageService()
    if service.login(request.username, request.password, request.subdomain):
        # Login successful
        # Check if user exists
        user = db.query(User).filter(User.edupage_username == request.username).first()
        session_data = service.get_session_data()
        
        if not user:
            user = User(edupage_username=request.username, edupage_session_data=session_data)
            db.add(user)
        else:
            user.edupage_session_data = session_data
        
        db.commit()
        db.refresh(user)
        
        return {"id": user.id, "username": user.edupage_username}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@router.post("/logout")
def logout():
    return {"message": "Logged out"}

