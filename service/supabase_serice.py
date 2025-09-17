import psycopg2
from psycopg2 import sql
import json
import os
from dotenv import load_dotenv
from utils.utils import parse_iso_datetime
load_dotenv()

DB_URL = os.getenv("DB_URL")
schema_name = "Bigin"
table_name = "deals"

def get_db_connection():
    return psycopg2.connect(DB_URL)

def insert_deals_in_supabase(deals: list[dict]):
    """
    Upsert deals into the Bigin.Deals table.
    If a deal with the same id exists, overwrite it; otherwise, create a new row.
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    
    for deal in deals:

        print(f"[{deals.index(deal) + 1}/{len(deals)}] Inserting/Updating deal ID: {deal['id']}")
        flat_row = {
            "id": int(deal["id"]),
            "deal_name": deal.get("Deal_Name", None),
            "amount": deal.get("Amount", None),
            "stage": deal.get("Stage", None),
            "contact_id": int(deal["Contact_Name"]["id"]) if deal.get("Contact_Name") else None,
            "contact_name": deal["Contact_Name"]["name"] if deal.get("Contact_Name") else None,
            "closing_date": deal.get("Closing_Date", None),
            "stage_history": json.dumps(deal.get("stage_history")) if deal.get("stage_history") else None,
            "pipeline": deal.get("Pipeline", {}).get("name", None) if deal.get("Pipeline") else None,
            "created_time": parse_iso_datetime(deal.get("Created_Time", None)),
            "modified_time": parse_iso_datetime(deal.get("Modified_Time", None)),
            
        }
        
        columns = flat_row.keys()
        values = [flat_row[col] for col in columns]
        
        # Columns to update if conflict occurs (exclude primary key 'id')
        update_cols = [col for col in columns if col != "id"]
        
        insert_stmt = sql.SQL(
            "INSERT INTO {}.{} ({fields}) VALUES ({placeholders}) "
            "ON CONFLICT (id) DO UPDATE SET {updates}"
        ).format(
            sql.Identifier(schema_name),
            sql.Identifier(table_name),
            fields=sql.SQL(", ").join(map(sql.Identifier, columns)),
            placeholders=sql.SQL(", ").join(sql.Placeholder() * len(values)),
            updates=sql.SQL(", ").join(
                sql.SQL("{} = EXCLUDED.{}").format(sql.Identifier(col), sql.Identifier(col)) for col in update_cols
            )
        )
        
        cursor.execute(insert_stmt, values)
    
    connection.commit()
    cursor.close()
    connection.close()
    print(f"{len(deals)} deals inserted/updated successfully!")


def fetch_all_deals():
    """
    Fetch all deals from the Bigin.Deals table.
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    
    query = sql.SQL("SELECT * FROM {}.{}").format(
        sql.Identifier(schema_name),
        sql.Identifier(table_name)
    )
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    # Fetch column names
    colnames = [desc[0] for desc in cursor.description]
    
    # Convert rows to list of dicts
    deals = [dict(zip(colnames, row)) for row in rows]
    
    cursor.close()
    connection.close()
    
    return deals