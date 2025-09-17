import json
import os

TOKEN_FILE = "keys/zoho_tokens.json"

def save_tokens(token_data: dict):
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f)

def load_tokens() -> dict:
    if not os.path.exists(TOKEN_FILE):
        return {}
    with open(TOKEN_FILE, "r") as f:
        return json.load(f)
