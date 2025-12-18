"""
Session Keep-Alive Service

Periodically pings all active Edupage sessions to keep them alive.
If a session is expired, it clears the session data from the database.
"""
import logging
from datetime import date
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from database import SessionLocal
from models import User
from edupage_service import EdupageService, SessionExpiredException

logger = logging.getLogger(__name__)

# How often to ping sessions (in minutes)
KEEP_ALIVE_INTERVAL_MINUTES = 30

scheduler = BackgroundScheduler()


def ping_all_sessions():
    """
    Iterate through all users with session data and ping their sessions.
    Clears session data for any expired sessions.
    """
    logger.info("Session keeper: Starting session ping cycle")
    
    db: Session = SessionLocal()
    try:
        # Get all users with session data
        users = db.query(User).filter(User.edupage_session_data.isnot(None)).all()
        
        if not users:
            logger.info("Session keeper: No active sessions to ping")
            return
        
        logger.info(f"Session keeper: Pinging {len(users)} active session(s)")
        
        for user in users:
            try:
                service = EdupageService()
                service.load_session_data(user.edupage_session_data)
                
                # Try to ping the session by fetching today's meals
                # This is a lightweight call that will fail if session is expired
                service.ping_session()
                
                logger.debug(f"Session keeper: Session for user {user.id} is still alive")
                
            except SessionExpiredException:
                logger.warning(f"Session keeper: Session expired for user {user.id}, clearing session data")
                user.edupage_session_data = None
                db.commit()
                
            except Exception as e:
                # Don't clear on other errors (network issues, etc.)
                logger.error(f"Session keeper: Error pinging session for user {user.id}: {e}")
                
    except Exception as e:
        logger.error(f"Session keeper: Error during ping cycle: {e}")
    finally:
        db.close()
    
    logger.info("Session keeper: Ping cycle complete")


def start_scheduler():
    """Start the background scheduler for session keep-alive."""
    if scheduler.running:
        logger.warning("Session keeper: Scheduler already running")
        return
    
    scheduler.add_job(
        ping_all_sessions,
        trigger=IntervalTrigger(minutes=KEEP_ALIVE_INTERVAL_MINUTES),
        id='session_keep_alive',
        name='Keep Edupage sessions alive',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info(f"Session keeper: Started (pinging every {KEEP_ALIVE_INTERVAL_MINUTES} minutes)")


def stop_scheduler():
    """Stop the background scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Session keeper: Stopped")
