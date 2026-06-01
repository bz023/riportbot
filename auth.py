import os
import json
from cryptography.fernet import Fernet

DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

CONFIG_FILE = os.path.join(DATA_DIR, "config.enc")
KEY_FILE = os.path.join(DATA_DIR, "secret.key")

def get_or_create_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as kf:
            kf.write(key)
        return key
    with open(KEY_FILE, "rb") as kf:
        return kf.read()

def save_credentials(email, password):
    key = get_or_create_key()
    fernet = Fernet(key)
    data = {"email": email, "password": password}
    encrypted_data = fernet.encrypt(json.dumps(data).encode())
    with open(CONFIG_FILE, "wb") as cf:
        cf.write(encrypted_data)

def load_credentials():
    if not os.path.exists(CONFIG_FILE) or not os.path.exists(KEY_FILE):
        return None
    try:
        key = get_or_create_key()
        fernet = Fernet(key)
        with open(CONFIG_FILE, "rb") as cf:
            encrypted_data = cf.read()
        decrypted_data = fernet.decrypt(encrypted_data).decode()
        return json.loads(decrypted_data)
    except Exception:
        return None