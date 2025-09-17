import requests
from utils.token import save_tokens, load_tokens
from datetime import datetime
import os
from dotenv import load_dotenv
load_dotenv()


CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8000/auth")
SCOPE = "ZohoBigin.modules.ALL,ZohoBigin.settings.ALL"

AUTH_BASE_URL = "https://accounts.zoho.in/oauth/v2/auth"
TOKEN_URL = "https://accounts.zoho.in/oauth/v2/token"

API_BASE_URL = "https://www.zohoapis.in/bigin/v2/"

def get_oauth_url() -> str:
    return (
        f"{AUTH_BASE_URL}?"
        f"client_id={CLIENT_ID}&"
        f"scope={SCOPE}&"
        f"response_type=code&"
        f"access_type=offline&"
        f"redirect_uri={REDIRECT_URI}"
    )

def exchange_code_for_token(code: str) -> dict:
    payload = {
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    response = requests.post(TOKEN_URL, data=payload)
    token_data = response.json()
    expiry_delay = token_data.get("expires_in", 0)
    token_data["expiry_time"] = datetime.now().timestamp() + expiry_delay
    save_tokens(token_data)
    return token_data

def refresh_access_token(refresh_token: str) -> dict:
    payload = {
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token"
    }
    response = requests.post(TOKEN_URL, data=payload)
    new_tokens = response.json()
    tokens = load_tokens()
    tokens.update(new_tokens)
    expiry_delay = new_tokens.get("expires_in", 0)
    tokens["expiry_time"] = datetime.now().timestamp() + expiry_delay
    save_tokens(tokens)
    return tokens

def get_access_token() -> str:
    tokens = load_tokens()
    if not tokens:
        raise ValueError("No tokens found. Authenticate first.")
    if datetime.now().timestamp() > tokens.get("expiry_time", 0):
        tokens = refresh_access_token(tokens["refresh_token"])
    return tokens["access_token"]


def get_all_stages():
    access_token = get_access_token()
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}"
    }
    response = requests.get(f"{API_BASE_URL}settings/fields?module=Pipelines", headers=headers)

    if response.status_code == 200:
        response_data = response.json()

    stages = (field for field in response_data.get("fields") if field.get("field_label", "").lower() == "stage")

    return stages


def get_all_deals(all_deals: list = None, next_page_token: str = None):
    if all_deals is None: 
        all_deals = []

    print("Fetching deals... Current count:", len(all_deals))
    access_token = get_access_token()
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}"
    }

    request_url = f"{API_BASE_URL}Pipelines?fields=Deal_Name,Id,Stage,Amount,Closing_Date,Contact_Name,Pipeline,Created_Time,Modified_Time,Timeline,Other_Info"
    if next_page_token:
        request_url += f"&page_token={next_page_token}"

    response = requests.get(request_url, headers=headers)

    if response.status_code == 200:
        data = response.json()

        all_deals.extend(data.get("data", []))

        next_token = data.get("info", {}).get("next_page_token")
        if next_token:
            return get_all_deals(all_deals, next_token)  # recursive call
        else:
            return all_deals

    print(f"Error {response.status_code}: {response.text}")
    return all_deals



def get_all_deals_with_stage_history():
    deals = get_all_deals()
    for deal in deals:
        deal_id = deal.get("id")
        print(f"[{deals.index(deal) + 1}/{len(deals)}] Fetching stage history for deal ID: {deal_id}")
        if deal_id:
            stage_history = get_deal_stage_history(deal_id)
            deal["stage_history"] = stage_history
    return deals



def get_deal_stage_history(deal_id: str):
    access_token = get_access_token()
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}"
    }
    response = requests.get(f"{API_BASE_URL}Pipelines/{deal_id}/Stage_History?fields=Stage,Modified_Time,Changed_By", headers=headers)

    if response.status_code == 200:
        return response.json().get("data", [])
    print(f"Error {response.status_code}: {response.text}")
    return []







