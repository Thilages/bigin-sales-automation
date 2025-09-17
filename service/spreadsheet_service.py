import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
from datetime import datetime, date

# === CONFIG ===
TAB_NAME = "Deals"
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Auth client
def get_gsheet_client():
    creds = ServiceAccountCredentials.from_json_keyfile_name("keys/spreadsheet_service_account.json", scope)
    return gspread.authorize(creds)

def get_or_create_worksheet(spreadsheet, tab_name="Deals", rows=100, cols=20):
    try:
        worksheet = spreadsheet.worksheet(tab_name)
        print(f"✅ Found worksheet: {tab_name}")
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=tab_name, rows=rows, cols=cols)
        print(f"🆕 Created worksheet: {tab_name}")
    return worksheet

# need to work on upsert logic
def insert_deals_to_gsheet(deals: list[dict]):
    """
    Upsert deals into the Google Sheet.
    If a deal with the same id exists, update it; otherwise, append new.
    """
    client = get_gsheet_client()
    spreadsheet = client.open_by_key(os.getenv("SPREAD_SHEET_ID"))
    worksheet = get_or_create_worksheet(spreadsheet, TAB_NAME)

    # Existing rows (as dicts)
    existing = worksheet.get_all_records()
    id_map = {str(row["id"]): i+2 for i, row in enumerate(existing)}  # +2 because headers + 1-indexed

    for idx, deal in enumerate(deals, 1):
        print(f"[{idx}/{len(deals)}] Upserting deal ID: {deal['id']}")

        flat_row = {
            "id": int(deal["id"]),
            "deal_name": deal.get("Deal_Name"),
            "amount": deal.get("Amount"),
            "stage": deal.get("Stage"),
            "contact_id": int(deal["Contact_Name"]["id"]) if deal.get("Contact_Name") else None,
            "contact_name": deal["Contact_Name"]["name"] if deal.get("Contact_Name") else None,
            "closing_date": deal.get("Closing_Date"),
            "stage_history": json.dumps(deal.get("Stage_History")) if deal.get("Stage_History") else None
        }

        row_values = list(flat_row.values())

        if str(flat_row["id"]) in id_map:
            row_index = id_map[str(flat_row["id"])]
            worksheet.update(f"A{row_index}:H{row_index}", [row_values])  # update in place
        else:
            worksheet.append_row(row_values)  # add new row

    print(f"✅ {len(deals)} deals upserted successfully!")

def number_to_column(n: int) -> str:
    """Convert 1-indexed column number to Excel/Sheets column letters."""
    result = ""
    while (n and n > 0):
        n, remainder = divmod(n - 1, 26)
        result = chr(65 + remainder) + result
    return result


def get_row_and_col(worksheet, search_value):
    print(f"Searching for '{search_value}' in the worksheet..."
          )
    cell = worksheet.find(search_value)
    if cell:
        return cell.row, cell.col
    return None, None

def update_summary(worksheet, summary, summary_data):
    
    row,col = get_row_and_col(worksheet, summary)
    
    if row and col:
        col = number_to_column(col)
        values_row = row + 3  # Assuming values are 3 rows below the summary title
        worksheet.update(f"{col}{values_row}", [summary_data])
    else:
        print(f"Summary '{summary}' not found.") 


def update_due_today_list(worksheet, due_today):
    row, col = get_row_and_col(worksheet, "Due_Today")
    print(row)
    due_today = [[deal.get("deal_name"), deal.get("stage"), deal.get("pipeline")] for deal in due_today]

    if row and col:
        values_row = row + 3  # Assuming values are 3 rows below the summary title
        worksheet.update(f"A{values_row}", due_today)
    else:
        print(f"Due Today list not found.")


def update_table(worksheet, table_name,table_data):
    row, col = get_row_and_col(worksheet, table_name)
    
    col = number_to_column(col)
    if row and col:
        start_row = row + 3
        table_data = [
            [
                data.get("deal_name"), 
                data.get("stage"), 
                (data.get("closing_date").strftime("%Y-%m-%d") 
                if isinstance(data.get("closing_date"), (datetime, date)) 
                else str(data.get("closing_date")))
            ]
            for data in table_data
        ]        
        worksheet.update(f"{col}{start_row}", table_data)
    else:
        print(f"Table '{table_name}' not found.")
    


def update_deals_sheet_summary(deals_object:dict[str:any], table_name="pipeline_summary"):
    """
    Update the Google Sheet with categorized deals.
    """
    client = get_gsheet_client()
    spreadsheet = client.open_by_key("18UncISysDR82lgZ9gOHkk64MXLVz3nWhZNTgYaZ-gZA")
    worksheet = get_or_create_worksheet(spreadsheet, table_name)

    overall_summary = [deals_object.get("total_deals", 0), deals_object.get("total_overdue", 0), deals_object.get("total_due_today", 0)]
    sales_summary = [deals_object.get("sales_total", 0), len(deals_object.get("sales_overdue", [])), len(deals_object.get("sales_due_today", []))]
    qual_summary = [deals_object.get("qual_total", 0), len(deals_object.get("quals_overdue", [])), len(deals_object.get("quals_due_today", []))]
    slowmo_summary = [deals_object.get("slowmo_total", 0), len(deals_object.get("slowmo_overdue", [])), len(deals_object.get("slowmo_due_today", []))]

    update_summary(worksheet, "Overall_Summary", overall_summary)
    update_summary(worksheet, "Sales_Summary", sales_summary)
    update_summary(worksheet, "Quals_Summary", qual_summary)
    update_summary(worksheet, "Slowmo_Summary", slowmo_summary)

    
    
    
def update_deals_sheet_tables(deals_object:dict[str:any], table_name="todos_summary"):
    """
    Update the Google Sheet with categorized deals.
    """
    client = get_gsheet_client()
    spreadsheet = client.open_by_key("18UncISysDR82lgZ9gOHkk64MXLVz3nWhZNTgYaZ-gZA")
    worksheet = get_or_create_worksheet(spreadsheet, table_name)
    
    update_due_today_list(worksheet, deals_object.get("total_due_today_list", []))
    
    
    update_table(worksheet, "Sales_Overdue", deals_object.get("sales_overdue", []))
    
    update_table(worksheet, "Quals_Overdue", deals_object.get("quals_overdue", []))
    
    update_table(worksheet, "Slowmo_Overdue", deals_object.get("slowmo_overdue", []))





