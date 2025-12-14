from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from models import User
from database import SessionLocal
from edupage_service import EdupageService
from datetime import date, datetime

router = APIRouter(prefix="/lunches", tags=["lunches"])

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

from sqlalchemy import func
from models import Rating, Photo

@router.get("/")
def get_lunches(day: str = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # day format YYYY-MM-DD
    if day:
        try:
            target_date = datetime.strptime(day, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")
    else:
        target_date = date.today()

    service = EdupageService()
    service.load_session_data(user.edupage_session_data)
    
    try:
        lunches = service.get_lunches(target_date)
    except Exception as e:
        print(f"Error fetching lunches: {e}")
        return []  # Return empty list if fetching fails
    
    # Serialize and enrich
    results = []
    
    # Check if we have a Meals object and if it has a lunch
    current_lunch_meal = None
    if lunches and hasattr(lunches, 'lunch') and lunches.lunch:
        current_lunch_meal = lunches.lunch
        
        # Get the deadline for changes (from the Meal object)
        # This is when you can no longer order/cancel/change this lunch
        can_be_changed_until = None
        if hasattr(current_lunch_meal, 'can_be_changed_until'):
            can_be_changed_until = current_lunch_meal.can_be_changed_until
        
        # Limit to first 7 meals (soup + 6 main meals)
        # The rest are often weird text or invalid data
        meals_to_process = list(current_lunch_meal)[:7]
        
        # Iterate over menus in the lunch
        for i, menu in enumerate(meals_to_process):
            # menu is a Menu object
            meal_name = menu.name
            
            # Get average rating from OUR database only (not edupage ratings)
            avg_rating = db.query(func.avg(Rating.stars)).filter(Rating.meal_identifier == meal_name).scalar()
            
            from storage import get_storage_service
            
            # Get all photos
            photos = db.query(Photo).filter(Photo.meal_identifier == meal_name).all()
            photo_list = []
            user_has_photo = False
            storage = get_storage_service()
            for p in photos:
                photo_list.append(storage.get_url(p.photo_path))
                if p.user_id == user.id:
                    user_has_photo = True
            
            photo_url = photo_list[0] if photo_list else None
            
            # Check if ordered
            # IMPORTANT: The edupage API uses DIFFERENT formats for ordered status:
            # - ordered_meal is a LETTER: "A", "B", "C", "D", "E", "F", etc.
            # - menu.number is a STRING NUMBER: "1", "2", "3", "4", "5", "6", etc. (or "None" for soup)
            # We must convert: A=1, B=2, C=3, D=4, E=5, F=6, etc.
            is_ordered = False
            if current_lunch_meal.ordered_meal:
                # Convert letter to number: A->1, B->2, C->3, etc.
                ordered_letter = current_lunch_meal.ordered_meal.strip().upper()
                if ordered_letter and ordered_letter in "ABCDEFGH":
                    ordered_number = str(ord(ordered_letter) - ord('A') + 1)  # A=1, B=2, etc.
                    
                    # Compare with menu.number
                    menu_number = str(menu.number).strip() if menu.number else ""
                    is_ordered = (menu_number == ordered_number)
            
            results.append({
                "index": i,  # Use 0-based index for ordering (this is what the API expects)
                "name": meal_name,
                "number": menu.number,  # Add menu number (e.g. "1", "2", "3" or "None" for soup)
                "is_ordered": is_ordered,
                "avg_rating": round(avg_rating, 1) if avg_rating else None,  # Only our app's rating
                "photo_url": photo_url,
                "photos": photo_list,
                "user_has_photo": user_has_photo,
                "date": target_date.isoformat(),  # Add date for frontend logic
                "can_be_changed_until": can_be_changed_until if can_be_changed_until else None  # Deadline for changes
            })
        
    return results

@router.post("/order")
def order_lunch(meal_index: int, day: str, user: User = Depends(get_current_user)):
    # We need to fetch lunches again to get the meal object
    target_date = datetime.strptime(day, "%Y-%m-%d").date()
    service = EdupageService()
    service.load_session_data(user.edupage_session_data)
    lunches = service.get_lunches(target_date)
    
    if lunches and lunches.lunch:
        # We are ordering a specific menu item from the lunch
        # meal_index is 1-based index of the menu
        try:
            # We need to pass the EdupageModule to choose()
            # But service.edupage is the Edupage object, which inherits/uses Module?
            # The choose method expects 'edupage: EdupageModule'.
            # The Edupage class in edupage-api seems to be the main entry point.
            # Let's assume service.edupage is compatible.
            lunches.lunch.choose(service.edupage, meal_index)
            return {"message": "Ordered"}
        except Exception as e:
            print(f"Order error: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to order: {str(e)}")
    else:
        raise HTTPException(status_code=404, detail="No lunch found for this day")

@router.post("/cancel")
def cancel_lunch(meal_index: int, day: str, user: User = Depends(get_current_user)):
    target_date = datetime.strptime(day, "%Y-%m-%d").date()
    service = EdupageService()
    service.load_session_data(user.edupage_session_data)
    lunches = service.get_lunches(target_date)
    
    if lunches and lunches.lunch:
        try:
            lunches.lunch.sign_off(service.edupage)
            return {"message": "Canceled"}
        except Exception as e:
            print(f"Cancel error: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to cancel: {str(e)}")
    else:
        raise HTTPException(status_code=404, detail="No lunch found for this day")

