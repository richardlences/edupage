
import pickle
import base64
from typing import Dict
from edupage_internal import EdupageClient

# In-memory store: user_id (int) -> EdupageClient
_sessions: Dict[int, EdupageClient] = {}

def get_client(user) -> EdupageClient:
    """
    Get an active EdupageClient for the user.
    If in memory, return it.
    If in DB, deserialize, add to memory, return it.
    Else return a new (not logged in) client.
    """
    if user.id in _sessions:
        return _sessions[user.id]
    
    # Not in memory, try to load from DB
    if user.edupage_session_data:
        try:
            client = EdupageClient()
            # Deserialize
            # Format: base64(pickle(dict))
            
            # Handle string vs bytes
            session_data = user.edupage_session_data
            if isinstance(session_data, bytes):
                session_data = session_data.decode('utf-8')
                
            data = base64.b64decode(session_data)
            state = pickle.loads(data)
            
            client.session.cookies.update(state.get('cookies', {}))
            client.subdomain = state.get('subdomain')
            client.username = state.get('username')
            client.gsec_hash = state.get('gsec_hash')
            client.is_logged_in = True 
            
            # Additional check: parsing login data might be needed if we want 'client.data'
            # but we usually don't serialize 'client.data'. 
            # It's fine, we fetch what we need.
            
            _sessions[user.id] = client
            return client
        except Exception as e:
            print(f"Failed to load session for user {user.id}: {e}")
            # fall through to return fresh client
            
    # Return fresh client (caller will likely redirect to login)
    return EdupageClient()

def create_session(user, username, password, subdomain) -> EdupageClient:
    """
    Creates a new session by logging in, and then updates storage.
    """
    client = EdupageClient()
    client.login(username, password, subdomain)
    update_session(user, client)
    return client

def update_session(user, client: EdupageClient):
    """
    Update the in-memory session and DB persistence.
    Should be called after a fresh login.
    """
    # Key point: we are storing the client instance in memory
    _sessions[user.id] = client
    
    # Serialize for DB persistence
    state = {
        'cookies': client.session.cookies,
        'subdomain': client.subdomain,
        'username': client.username,
        'gsec_hash': client.gsec_hash
    }
    pickled = pickle.dumps(state)
    b64_data = base64.b64encode(pickled).decode('utf-8')
    
    user.edupage_session_data = b64_data
    # Note: caller must commit DB transaction

def clear_session(user_id: int):
    """
    Remove from memory. Caller should also clear DB if needed.
    """
    if user_id in _sessions:
        del _sessions[user_id]
