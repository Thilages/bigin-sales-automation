from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from service.spreadsheet_service import insert_deals_to_gsheet
from service.zoho_service import (
    get_all_deals_with_stage_history,
    get_all_stages,
    get_oauth_url,
    exchange_code_for_token,
    get_all_deals,
    refresh_access_token
)
from service.supabase_serice import  insert_deals_in_supabase
from utils.token import load_tokens

router = APIRouter()

@router.get("/get-oauth-code")
def oauth_redirect():
    return RedirectResponse(url=get_oauth_url())

@router.get("/auth")
def auth_callback(code: str):
    token_data = exchange_code_for_token(code)
    return {"message": "Tokens saved successfully", "token_data": token_data}

@router.get("/refresh-token")
def refresh_token_endpoint():
    tokens = refresh_access_token(load_tokens().get("refresh_token"))
    return {"message": "Token refreshed successfully", "tokens": tokens}

@router.get("/stages")
def get_stages():
    stages = get_all_stages()
    return {"stages": stages}

@router.get("/deals")
def get_deals():
    deals = get_all_deals()
    return {"deals": deals}

@router.get("/fetch-and-store-deals")
def fetch_and_store_deals():
    
    print("Fetching and storing deals...")
    deals = get_all_deals_with_stage_history()
    print(f"Total deals fetched: {len(deals)}")
    
    insert_deals_in_supabase(deals)
    print(f"Total deals stored: {len(deals)}")

    
    return {"message": f"{len(deals)} deals fetched and stored successfully."}

