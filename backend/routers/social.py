from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File, Form
from sqlalchemy.orm import Session
from ..models import User, Rating, Photo
from ..database import SessionLocal
from pydantic import BaseModel
import shutil
import os
import uuid

router = APIRouter(prefix="/social", tags=["social"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(user_id: str = Header(None), db: Session = Depends(get_db)):
    if not user_id:
        raise HTTPException(status_code=401, detail="Missing User ID")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid User")
    return user

class RateRequest(BaseModel):
    meal_identifier: str
    stars: int

@router.post("/rate")
def rate_lunch(request: RateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Check if rating exists
    rating = db.query(Rating).filter(Rating.user_id == user.id, Rating.meal_identifier == request.meal_identifier).first()
    if rating:
        rating.stars = request.stars
    else:
        rating = Rating(user_id=user.id, meal_identifier=request.meal_identifier, stars=request.stars)
        db.add(rating)
    
    db.commit()
    return {"message": "Rated"}

@router.post("/upload")
def upload_photo(meal_identifier: str = Form(...), file: UploadFile = File(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Check if user already has a photo for this meal
    existing_photo = db.query(Photo).filter(Photo.user_id == user.id, Photo.meal_identifier == meal_identifier).first()
    
    if existing_photo:
        # Remove old file
        if os.path.exists(existing_photo.photo_path):
            os.remove(existing_photo.photo_path)
        db.delete(existing_photo)
        db.commit()
    else:
        # Check total photos limit (max 5)
        count = db.query(Photo).filter(Photo.meal_identifier == meal_identifier).count()
        if count >= 5:
            raise HTTPException(status_code=400, detail="Max 5 photos per meal reached")

    # Save file
    os.makedirs("uploads", exist_ok=True)
    filename = f"{uuid.uuid4()}_{file.filename}"
    filepath = os.path.join("uploads", filename)
    
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    photo = Photo(user_id=user.id, meal_identifier=meal_identifier, photo_path=filepath)
    db.add(photo)
    db.commit()
    
    return {"message": "Uploaded", "path": filepath}

class DeletePhotoRequest(BaseModel):
    meal_identifier: str

@router.post("/delete_photo")
def delete_photo(request: DeletePhotoRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    photo = db.query(Photo).filter(Photo.user_id == user.id, Photo.meal_identifier == request.meal_identifier).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    
    if os.path.exists(photo.photo_path):
        os.remove(photo.photo_path)
        
    db.delete(photo)
    db.commit()
    
    return {"message": "Deleted"}
