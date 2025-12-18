import json
import pickle
import base64
from datetime import date
from edupage_api import Edupage
from edupage_api.exceptions import (
    BadCredentialsException,
    NotLoggedInException,
    ExpiredSessionException as EdupageExpiredSessionException,
    InvalidMealsData
)


class SessionExpiredException(Exception):
    """Raised when the Edupage session has expired and needs re-authentication."""
    pass


class EdupageService:
    def __init__(self):
        self.edupage = Edupage()

    def login(self, username, password, subdomain):
        try:
            self.edupage.login(username, password, subdomain)
            return True
        except BadCredentialsException:
            return False


    def get_session_data(self):
        if self.edupage.is_logged_in:
             state = {
                 'cookies': self.edupage.session.cookies,
                 'subdomain': self.edupage.subdomain,
                 'username': self.edupage.username,
                 'gsec_hash': self.edupage.gsec_hash
             }
             pickled = pickle.dumps(state)
             return base64.b64encode(pickled).decode('utf-8')
        return None

    def load_session_data(self, session_data):
        if session_data:
            try:
                # Ensure it's treated as string before decoding if it's somehow bytes (unlikely with Text column)
                if isinstance(session_data, bytes):
                    session_data = session_data.decode('utf-8')
                
                # Check if it might be the old "b'...'" string representation from previous bug
                if session_data.startswith("b'") and session_data.endswith("'"):
                    # This is tricky to recover safely without eval, so let's just invalidate it
                    # or assume it's lost. 
                    # But actually, if we just try base64 decode on it, it will fail, which is caught below.
                    pass

                state_bytes = base64.b64decode(session_data)
                state = pickle.loads(state_bytes)
                self.edupage.session.cookies.update(state.get('cookies', {}))
                self.edupage.subdomain = state.get('subdomain')
                self.edupage.username = state.get('username')
                self.edupage.gsec_hash = state.get('gsec_hash')
                self.edupage.is_logged_in = True
            except Exception as e:
                print(f"Error loading session data: {e}")
                # Reset login state if needed, though default is not logged in
                self.edupage.is_logged_in = False

    def get_lunches(self, target_date):
        """
        Get meals for a specific date.
        Raises SessionExpiredException if session is invalid.
        """
        try:
            return self.edupage.get_meals(target_date)
        except (NotLoggedInException, EdupageExpiredSessionException, InvalidMealsData) as e:
            raise SessionExpiredException(f"Session expired: {e}")
        except IndexError as e:
            # This happens when edupage returns a login page instead of data
            # The library tries to parse "edupageData:" but it's not there
            raise SessionExpiredException(f"Session expired (parse error): {e}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error fetching lunches: {e}")
            # Re-raise as SessionExpiredException if it looks like an auth issue
            error_str = str(e).lower()
            if 'login' in error_str or 'auth' in error_str or 'session' in error_str:
                raise SessionExpiredException(f"Session expired: {e}")
            return []

    def order_lunch(self, meal):
        """Order a meal. Raises SessionExpiredException if session is invalid."""
        try:
            self.edupage.assign_meal(meal)
            return True
        except (NotLoggedInException, EdupageExpiredSessionException) as e:
            raise SessionExpiredException(f"Session expired: {e}")
        except Exception as e:
            print(f"Error ordering lunch: {e}")
            return False

    def cancel_lunch(self, meal):
        """Cancel a meal. Raises SessionExpiredException if session is invalid."""
        try:
            self.edupage.sign_out_meal(meal)
            return True
        except (NotLoggedInException, EdupageExpiredSessionException) as e:
            raise SessionExpiredException(f"Session expired: {e}")
        except Exception as e:
            print(f"Error canceling lunch: {e}")
            return False

    def ping_session(self):
        """
        Check if the session is still valid by making a lightweight API call.
        Raises SessionExpiredException if the session is expired.
        """
        try:
            # Try to get today's meals as a simple validity check
            self.edupage.get_meals(date.today())
        except (NotLoggedInException, EdupageExpiredSessionException, InvalidMealsData) as e:
            raise SessionExpiredException(f"Session expired: {e}")
        except IndexError as e:
            raise SessionExpiredException(f"Session expired (parse error): {e}")
        except Exception as e:
            error_str = str(e).lower()
            if 'login' in error_str or 'auth' in error_str or 'session' in error_str:
                raise SessionExpiredException(f"Session expired: {e}")
            # For other errors (network, etc.), don't treat as expired
            raise
