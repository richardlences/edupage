from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models import User
from database import SessionLocal
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
    from session_manager import create_session
    from edupage_internal import BadCredentialsException
    
    # Check if user exists first to get ID if updating
    user = db.query(User).filter(User.edupage_username == request.username).first()
    
    if not user:
        # Create user temporarily (or handle this differently if you want to verify login first)
        # Actually session_manager needs a user object to store session. 
        # But we can verify login *before* creating user, then create user, then save session.
        # Let's verify login explicitly first.
        from edupage_internal import EdupageClient
        temp_client = EdupageClient()
        try:
            temp_client.login(request.username, request.password, request.subdomain)
        except BadCredentialsException:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        except Exception:
             raise HTTPException(status_code=500, detail="Login failed")
            
        # Create user
        user = User(edupage_username=request.username, edupage_session_data=None)
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Now create managed session
        from session_manager import update_session
        update_session(user, temp_client)
        db.commit() # Save session data
        
        return {"id": user.id, "username": user.edupage_username}

    else:
        # User exists, try login and update
        try:
            client = create_session(user, request.username, request.password, request.subdomain)
            db.commit() # Save session data
            return {"id": user.id, "username": user.edupage_username}
        except BadCredentialsException:
             raise HTTPException(status_code=401, detail="Invalid credentials")
        except Exception as e:
             print(f"Login exception: {e}")
             raise HTTPException(status_code=500, detail="Login failed")

@router.post("/logout")
def logout():
    return {"message": "Logged out"}

