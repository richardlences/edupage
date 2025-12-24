
import json
import base64
import functools
import urllib.parse
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional, List, Dict
from enum import Enum
import requests

# --- Exceptions ---
class EdupageException(Exception): pass
class NotLoggedInException(EdupageException): pass
class SessionExpiredException(EdupageException): pass
class BadCredentialsException(EdupageException): pass
class InvalidMealsData(EdupageException): pass
class FailedToChangeMealError(EdupageException): pass

# --- Core Edupage Class ---
class EdupageClient:
    def __init__(self, request_timeout=5):
        self.session = requests.Session()
        self.session.request = functools.partial(self.session.request, timeout=request_timeout)
        self.subdomain = None
        self.username = None
        self.gsec_hash = None
        self.is_logged_in = False
        self.data = {} # Holds user data from login

    def login(self, username, password, subdomain):
        # Initial request to get CSRF token
        url_login = f"https://{subdomain}.edupage.org/login/?cmd=MainLogin"
        try:
            resp = self.session.get(url_login)
            if resp.status_code != 200:
                raise BadCredentialsException("Failed to access login page")
            
            content = resp.text
            if '"csrftoken":"' not in content:
                 # Ensure we have a valid session or subdomain. Sometimes redirect happens.
                 pass

            # Extract CSRF
            try:
                csrf_token = content.split('"csrftoken":"')[1].split('"')[0]
            except IndexError:
                 # Fallback/Error
                 raise BadCredentialsException("Could not extract CSRF token")

            # Login POST
            post_url = f"https://{subdomain}.edupage.org/login/edubarLogin.php"
            params = {
                "csrfauth": csrf_token,
                "username": username,
                "password": password
            }
            resp_post = self.session.post(post_url, data=params)
            
            if "bad=1" in resp_post.url:
                 raise BadCredentialsException("Invalid credentials")

            # Update internal state
            resp_content = resp_post.text
            
            # If subdomain was login1, update it
            if subdomain == "login1":
                try:
                    subdomain = resp_content.split("-->")[0].split(" ")[-1]
                except:
                    pass
            
            self.subdomain = subdomain
            self.username = username
            
            # Parse user data and gsec_hash
            self._parse_login_data(resp_content)

        except Exception as e:
            print(f"Login error: {e}")
            raise BadCredentialsException(f"Login failed: {e}")

    def _parse_login_data(self, html_content):
        # Extract userhome json
        try:
            if "userhome(" in html_content:
                json_str = html_content.split("userhome(", 1)[1].rsplit(");", 2)[0]
                # Cleanup potential formatting
                json_str = json_str.replace("\t", "").replace("\n", "").replace("\r", "")
                self.data = json.loads(json_str)
                self.is_logged_in = True
            
            if 'ASC.gsechash="' in html_content:
                self.gsec_hash = html_content.split('ASC.gsechash="')[1].split('"')[0]
        except Exception:
             # If we can't parse, we might not be fully logged in or page changed
             pass

    def get_meals_for_date(self, target_date: date):
        """
        Optimized fetch. 
        Instead of just fetching one day, we fetch the week view (standard edupage behavior)
        and return a dictionary of { date_str: MealObject }.
        """
        if not self.is_logged_in:
             raise NotLoggedInException()

        date_str = target_date.strftime("%Y%m%d")
        url = f"https://{self.subdomain}.edupage.org/menu/?date={date_str}"
        
        resp = self.session.get(url)
        content = resp.text
        
        if "edupageData: " not in content:
             raise SessionExpiredException("Invalid response (no edupageData)")

        # Parse the JSON data embedded in HTML
        try:
            # logic from original: response.split("edupageData: ")[1].split(",\r\n")[0]
            # using more robust generic split if possible
            json_part = content.split("edupageData: ")[1]
            # find end of json object. usually it ends with , followed by newline or similar.
            # but splitting by ",\r\n" is risky if minified.
            # Original code used: .split(",\r\n")[0]
            # Let's try to match original logic but be safe
            if ",\r\n" in json_part:
                json_part = json_part.split(",\r\n")[0]
            elif ",\n" in json_part:
                json_part = json_part.split(",\n")[0]
            
            data = json.loads(json_part)
        except Exception as e:
            raise SessionExpiredException(f"Failed to parse edupageData: {e}")

        # Drill down
        school_data = data.get(self.subdomain, {})
        
        try:
             novyListok = school_data.get("novyListok", {})
             boarder_id = novyListok.get("addInfo", {}).get("stravnikid")
             if not boarder_id:
                 # Try to find boarder id elsewhere or fail?
                 # It seems critical for rating/ordering
                 pass
        except:
             # Structure mismatch
             return {}

        # novyListok contains keys like "2023-12-20", "2023-12-21" etc.
        # We need to parse ALL of them.
        parsed_days = {}
        
        for d_str, day_data in novyListok.items():
             # Sketchy check if key is a date YYYY-MM-DD
             if not (len(d_str) == 10 and d_str[4] == '-' and d_str[7] == '-'):
                 continue
             
             # Parse lunch (ID 2). ID 1 is snack, 3 is afternoon. Lunch is main.
             # User app mainly cares about Lunch (ID 2). 
             # Original code parsed all. We can parse '2' and maybe others if needed.
             # User specifically mentioned "lunches".
             
             lunch_raw = day_data.get("2")
             if lunch_raw:
                 lunch_obj = self._parse_single_meal(lunch_raw, boarder_id, d_str, "2")
                 if lunch_obj:
                     parsed_days[d_str] = lunch_obj

        return parsed_days

    def _parse_single_meal(self, raw, boarder_id, date_str, meal_index):
        if raw.get("isCooking") is False:
            return None
        
        # Meal object structure for our App
        # We want: title, can_be_changed_until, ordered_meal (status), menus
        
        # Status parsing
        ordered_meal_status = None
        evidencia = raw.get("evidencia")
        if evidencia:
            status = evidencia.get("stav")
            # Correct logic based on debugging:
            # 1. If 'stav' is the letter itself (e.g. "B"), use it.
            # 2. If 'stav' is "V" (or "E" - observed in wild), use 'obj'.
            if status and status in "ABCDEFGH":
                ordered_meal_status = status
            elif status == "V" or status == "E":
                ordered_meal_status = evidencia.get("obj")

        # Deadline
        can_change_str = raw.get("zmen_do")
        can_change = datetime.fromisoformat(can_change_str) if can_change_str else None

        # Menus
        menus = []
        rows = raw.get("rows", [])
        for row in rows:
            if not row: continue
            
            # Extract basic info
            name = row.get("nazov")
            menu_num = row.get("menusStr")
            if menu_num:
                menu_num = menu_num.replace(": ", "")
            
            # Simple menu object
            menus.append({
                "name": name,
                "number": menu_num, # "1", "2" or None
            })

        return {
            "date": date_str,
            "can_be_changed_until": can_change,
            "ordered_meal": ordered_meal_status, # "A", "B", etc.
            "menus": menus,
            # We need these for actions (ordering/canceling)
            "boarder_id": boarder_id,
            "meal_index": meal_index
        }

    def order(self, meal_data, letter_choice):
        """
        meal_data: dict returned from _parse_single_meal
        letter_choice: "A", "B", etc.
        """
        return self._send_change_request(meal_data, letter_choice)

    def cancel(self, meal_data):
        return self._send_change_request(meal_data, "AX")

    def _send_change_request(self, meal_data, choice_str):
        if not self.is_logged_in:
             raise NotLoggedInException()
             
        url = f"https://{self.subdomain}.edupage.org/menu/"
        
        boarder_menu = {
            "stravnikid": meal_data["boarder_id"],
            "mysqlDate": meal_data["date"],
            "jids": {meal_data["meal_index"]: choice_str},
            "view": "pc_listok",
            "pravo": "Student"
        }
        
        payload = {
            "akcia": "ulozJedlaStravnika",
            "jedlaStravnika": json.dumps(boarder_menu)
        }
        
        resp = self.session.post(url, data=payload)
        try:
            res_json = resp.json()
            if res_json.get("error") != "":
                 raise FailedToChangeMealError(res_json.get("error"))
        except:
             # If not json or other error
             pass
        return True

