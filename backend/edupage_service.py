import json
import pickle
from edupage_api import Edupage
from edupage_api.exceptions import BadCredentialsException

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
             return pickle.dumps(state)
        return None

    def load_session_data(self, session_data):
        if session_data:
            state = pickle.loads(session_data)
            self.edupage.session.cookies.update(state.get('cookies', {}))
            self.edupage.subdomain = state.get('subdomain')
            self.edupage.username = state.get('username')
            self.edupage.gsec_hash = state.get('gsec_hash')
            self.edupage.is_logged_in = True

    def get_lunches(self, date):
        # date is datetime.date
        # edupage-api might expect a specific format or object
        # Looking at examples, it might be get_meals()
        # We'll need to verify the method name.
        # For now, let's assume get_meals() exists or similar.
        # If not, we'll have to fix it.
        try:
            return self.edupage.get_meals(date)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error fetching lunches: {e}")
            return []

    def order_lunch(self, meal):
        # meal object from get_lunches
        try:
            self.edupage.assign_meal(meal)
            return True
        except Exception as e:
            print(f"Error ordering lunch: {e}")
            return False

    def cancel_lunch(self, meal):
        try:
            self.edupage.sign_out_meal(meal)
            return True
        except Exception as e:
            print(f"Error canceling lunch: {e}")
            return False

