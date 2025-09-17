import json
from fastapi import FastAPI
from routes import zoho_routes
from utils.utils import get_time_stamp,get_week_data
from service.supabase_serice import insert_deals_in_supabase,fetch_all_deals
from service.metric_serice import calculate_weekly_spreadsheet_metrics, format_metrics_for_spreadsheet
app = FastAPI()

# Include Zoho routes
# app.include_router(zoho_routes.router)

data = fetch_all_deals()
week_data = get_week_data(previous_week_count=0)

data = calculate_weekly_spreadsheet_metrics(data, 1)
print(data)
with open('weekly_metrics.json', 'w') as f:
    json.dump(data, f, default=str, indent=2)




