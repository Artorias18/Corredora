import json
import os
from datetime import datetime, timedelta
from cryptography.fernet import Fernet

class SessionStorage:
    APP_NAME = "Corredora"

    @staticmethod
    def _get_storage_dir():
        base = os.getenv("LOCALAPPDATA") or os.path.expanduser("~")
        path = os.path.join(base, SessionStorage.APP_NAME)
        os.makedirs(path, exist_ok=True)
        return path

    @staticmethod
    def _key_path():
        return os.path.join(SessionStorage._get_storage_dir(), "secret.key")

    @staticmethod
    def _session_path():
        return os.path.join(SessionStorage._get_storage_dir(), "session.dat")

    @staticmethod
    def generate_key():
        key = Fernet.generate_key()
        with open(SessionStorage._key_path(), "wb") as f:
            f.write(key)

    @staticmethod
    def load_key():
        key_path = SessionStorage._key_path()
        if not os.path.exists(key_path):
            SessionStorage.generate_key()
        with open(key_path, "rb") as f:
            return f.read()

    @staticmethod
    def save_session(data: dict):
        key = SessionStorage.load_key()
        fernet = Fernet(key)

        data["expires_at"] = (
            datetime.utcnow() + timedelta(seconds=data["expires_in"])
        ).timestamp()

        encrypted = fernet.encrypt(json.dumps(data).encode())

        with open(SessionStorage._session_path(), "wb") as f:
            f.write(encrypted)

    @staticmethod
    def load_session():
        session_path = SessionStorage._session_path()
        if not os.path.exists(session_path):
            return None

        key = SessionStorage.load_key()
        fernet = Fernet(key)

        with open(session_path, "rb") as f:
            encrypted = f.read()

        decrypted = fernet.decrypt(encrypted)
        return json.loads(decrypted.decode())

    @staticmethod
    def clear_session():
        session_path = SessionStorage._session_path()
        if os.path.exists(session_path):
            os.remove(session_path)
