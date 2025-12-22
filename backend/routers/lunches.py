from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import User, Rating, Photo
from database import SessionLocal
from datetime import date, datetime
from cache import lunch_cache
from storage import get_storage_service
from session_manager import get_client
from edupage_internal import SessionExpiredException, EdupageException

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
    # Cast to int for DB lookup
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid User")
    return user

@router.get("/")
def get_lunches(day: str = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if day:
        try:
            target_date = datetime.strptime(day, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")
    else:
        target_date = date.today()
    
    date_str = target_date.isoformat()
    
    # Check cache first
    lunches = lunch_cache.get(user.id, date_str)
    
    if lunches is None:
        # Cache miss - fetch from Edupage
        client = get_client(user)
        try:
            # fetch_week returns { "YYYY-MM-DD": meal_dict, ... }
            week_data = client.get_meals_for_date(target_date)
            
            # Populate cache for ALL fetched days
            for d_str, m_data in week_data.items():
                lunch_cache.set(user.id, d_str, m_data)
                
            lunches = week_data.get(date_str)
            
        except SessionExpiredException:
            user.edupage_session_data = None
            db.commit()
            raise HTTPException(status_code=401, detail="Session expired, please log in again")
        except Exception as e:
            print(f"Error fetching lunches: {e}")
            return []
    
    if not lunches:
        return []

    # Prepare response
    results = []
    
    # 'lunches' is a dict with keys: date, can_be_changed_until, ordered_meal, menus, boarder_id...
    current_lunch_meal = lunches
    can_be_changed_until = current_lunch_meal.get('can_be_changed_until')
    
    # Ordered logic: 'ordered_meal' is "A", "B", ...
    ordered_letter = current_lunch_meal.get('ordered_meal')
    ordered_number = None
    if ordered_letter and ordered_letter in "ABCDEFGH":
         ordered_number = str(ord(ordered_letter) - ord('A') + 1)

    # Menus
    menus = current_lunch_meal.get('menus', [])[:7] # Limit to 7 items
    
    storage = get_storage_service()
    
    for i, menu in enumerate(menus):
        meal_name = menu['name']
        menu_number = menu['number'] # e.g. "1", "2"
        if menu_number:
            menu_number = str(menu_number).strip()

        # DB Queries for metadata
        avg_rating = db.query(func.avg(Rating.stars)).filter(Rating.meal_identifier == meal_name).scalar()
        user_rating = db.query(Rating.stars).filter(
            Rating.user_id == user.id,
            Rating.meal_identifier == meal_name
        ).scalar()
        
        photos = db.query(Photo).filter(Photo.meal_identifier == meal_name).all()
        photo_list = [storage.get_url(p.photo_path) for p in photos]
        user_has_photo = any(p.user_id == user.id for p in photos)
        photo_url = photo_list[0] if photo_list else None
        
        # Determine if this specific menu item is ordered
        is_ordered = False
        if ordered_number and menu_number:
            is_ordered = (menu_number == ordered_number)
            
        results.append({
            "index": i, 
            "name": meal_name,
            "number": menu_number,
            "is_ordered": is_ordered,
            "avg_rating": round(avg_rating, 1) if avg_rating else None,
            "user_rating": user_rating,
            "photo_url": photo_url,
            "photos": photo_list,
            "user_has_photo": user_has_photo,
            "date": date_str,
            "can_be_changed_until": can_be_changed_until
        })
        
    return results


@router.post("/order")
def order_lunch(meal_index: int, day: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # meal_index expects 1-based index (menu number 1..N) corresponding to A..N
    target_date = datetime.strptime(day, "%Y-%m-%d").date()
    client = get_client(user)
    
    # We need meal data first (to get boarder_id, etc.)
    # Check cache first or fetch
    lunches = lunch_cache.get(user.id, day)
    
    if not lunches:
        try:
            week_data = client.get_meals_for_date(target_date)
            for d_str, m_data in week_data.items():
                lunch_cache.set(user.id, d_str, m_data)
            lunches = week_data.get(day)
        except SessionExpiredException:
            user.edupage_session_data = None
            db.commit()
            raise HTTPException(status_code=401, detail="Session expired")

    if not lunches:
        raise HTTPException(status_code=404, detail="No lunch found for this day")
        
    # Convert index to letter
    letters = "ABCDEFGH"
    if 1 <= meal_index <= len(letters):
        calc_letter = letters[meal_index - 1]
    else:
        raise HTTPException(status_code=400, detail="Invalid meal index")

    try:
        client.order(lunches, calc_letter)
        # Invalidate cache
        lunch_cache.invalidate(user.id, day)
        return {"message": "Ordered"}
    except SessionExpiredException:
        user.edupage_session_data = None
        db.commit()
        raise HTTPException(status_code=401, detail="Session expired")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to order: {str(e)}")

@router.post("/cancel")
def cancel_lunch(meal_index: int, day: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # meal_index is ignored for cancel usually? Or strictly "sign off"?
    # internal client cancel method takes meal_data
    target_date = datetime.strptime(day, "%Y-%m-%d").date()
    client = get_client(user)
    
    lunches = lunch_cache.get(user.id, day)
    if not lunches:
        try:
            week_data = client.get_meals_for_date(target_date)
            for d_str, m_data in week_data.items():
                lunch_cache.set(user.id, d_str, m_data)
            lunches = week_data.get(day)
        except SessionExpiredException:
            user.edupage_session_data = None
            db.commit()
            raise HTTPException(status_code=401, detail="Session expired")

    if not lunches:
         raise HTTPException(status_code=404, detail="No lunch found")
         
    try:
        client.cancel(lunches)
        lunch_cache.invalidate(user.id, day)
        return {"message": "Canceled"}
    except SessionExpiredException:
        user.edupage_session_data = None
        db.commit()
        raise HTTPException(status_code=401, detail="Session expired")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel: {str(e)}")
