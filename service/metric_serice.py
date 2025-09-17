from datetime import datetime, date, timedelta
import calendar

from utils.utils import get_time_stamp,get_week_data
from utils.constants import (
    CLOSED_QUAL_LOST, CLOSED_SALES_LOST, CLOSED_SLOWMO_LOST,
    CLOSED_QUAL_POSITIVE, CLOSED_SALES_POSITIVE, CLOSED_SLOWMO_POSITIVE
)



def get_deals_metrics(deals: list[dict]):
    """
    Takes a list of deals (from Supabase/DB) and splits them into
    - overdue: closing date < today
    - due_today: closing date == today
    Returns: (overdue, due_today)
    """
    today = date.today()
    overdue = []
    due_today = []

    sales_total = [deal for deal in deals if deal.get("pipeline") == "Sales"]
    qual_total = [deal for deal in deals if deal.get("pipeline") == "Qual"]
    slowmo_total = [deal for deal in deals if deal.get("pipeline") == "SloMo"]
    for deal in deals:
        closing_date = deal.get("closing_date")
        if not closing_date:
            continue  # skip if missing
                
        try:
            # Normalize closing_date to a date object
            if isinstance(closing_date, str):
                closing_date = datetime.strptime(closing_date, "%Y-%m-%d").date()
            elif isinstance(closing_date, datetime):
                closing_date = closing_date.date()
        except Exception:
            continue  # skip if bad format

        if closing_date < today:
            overdue.append(deal)
        elif closing_date == today:
            due_today.append(deal)

    sales_overdue = [deal for deal in overdue if deal.get("pipeline") == "Sales"]
    sales_due_today = [deal for deal in due_today if deal.get("pipeline") == "Sales"]

    quals_overdue = [deal for deal in overdue if deal.get("pipeline") == "Qual"]
    quals_due_today = [deal for deal in due_today if deal.get("pipeline") == "Qual"]
    
    slowmo_overdue = [deal for deal in overdue if deal.get("pipeline") == "SloMo"]
    slowmo_due_today = [deal for deal in due_today if deal.get("pipeline") == "SloMo"]

    metrics = {
        "total_deals": len(deals),
        "total_overdue": len(overdue),
        "total_due_today": len(due_today),
        "total_due_today_list":due_today,
        "sales_total": len(sales_total),
        "sales_overdue": sales_overdue,
        "sales_due_today": sales_due_today,
        "qual_total": len(qual_total),
        "quals_overdue": quals_overdue,
        "quals_due_today": quals_due_today,
        "slowmo_total": len(slowmo_total),
        "slowmo_overdue": slowmo_overdue,
        "slowmo_due_today": slowmo_due_today,
    }
    
    return metrics


def get_metrics_by_week(deals: list[dict],week_data):
    """
    Takes a list of deals (from Supabase/DB) and splits them into
    weekly metrics based on the provided week data. 
    """
    
    pipelines = {"Sales": [], "Qual": [], "SloMo": []}
    for deal in deals:
        pipeline = deal.get("pipeline")
        if pipeline in pipelines:
            pipelines[pipeline].append(deal)

    print(pipelines)


def calculate_weekly_spreadsheet_metrics(deals: list[dict], week_offset: int = 0):
    """
    Calculate weekly metrics for spreadsheet for a specific week:
    - week: Week identifier
    - pipeline: Sales/Qual/SloMo
    - new deals: Deals created in that week
    - closed deals: Deals closed (won/lost) in that week  
    - total movements: All deals that had stage changes in that week
    - win %: Percentage of closed deals that were won
    
    Args:
        deals: List of deal dictionaries
        week_offset: Number of weeks back from current week (0 = current week, 1 = last week, etc.)
    
    Returns:
        List of dictionaries with weekly metrics for each pipeline (one week only)
    """
    
    # Get all closed stage names for each pipeline
    closed_stages = {
        "Qual": CLOSED_QUAL_LOST + CLOSED_QUAL_POSITIVE,
        "Sales": CLOSED_SALES_LOST + CLOSED_SALES_POSITIVE, 
        "SloMo": CLOSED_SLOWMO_LOST + CLOSED_SLOWMO_POSITIVE
    }
    
    # Get positive (won) stage names for each pipeline
    positive_stages = {
        "Qual": CLOSED_QUAL_POSITIVE,
        "Sales": CLOSED_SALES_POSITIVE,
        "SloMo": CLOSED_SLOWMO_POSITIVE
    }
    
    results = []
    
    # Get week data for the specified week offset
    week_data = get_week_data(week_offset)
    week_start_timestamp = week_data["start_date"]
    week_end_timestamp = week_data["end_date"]
    week_name = week_data["name"]
    
    # Convert timestamps back to dates for comparison
    week_start_date = datetime.fromtimestamp(week_start_timestamp).date()
    week_end_date = datetime.fromtimestamp(week_end_timestamp).date()
    
    # Calculate metrics for each pipeline
    for pipeline in ["Sales", "Qual", "SloMo"]:
        pipeline_deals = [deal for deal in deals if deal.get("pipeline") == pipeline]
        
        # New deals: created in this week
        new_deals = []
        for deal in pipeline_deals:
            created_time = deal.get("created_time")
            if created_time:
                try:
                    if isinstance(created_time, str):
                        created_date = datetime.fromisoformat(created_time.replace('Z', '+00:00')).date()
                    else:
                        created_date = created_time.date()
                    
                    if week_start_date <= created_date <= week_end_date:
                        new_deals.append(deal)
                except Exception:
                    continue
        
        # Closed deals: deals that moved to a closed stage in this week
        closed_deals = []
        won_deals = []
        
        for deal in pipeline_deals:
            stage_history = deal.get("stage_history", [])
            current_stage = deal.get("stage")
            
            # Check if deal is currently in a closed stage and was closed this week
            if current_stage in closed_stages.get(pipeline, []):
                # Look at stage history to see when it was closed
                for stage_entry in stage_history:
                    stage_name = stage_entry.get("Stage")
                    modified_time = stage_entry.get("Modified_Time")
                    
                    if stage_name in closed_stages.get(pipeline, []) and modified_time:
                        try:
                            # Parse the modified time
                            if isinstance(modified_time, str):
                                # Handle timezone format like "2025-09-13T10:39:20+05:30"
                                modified_date = datetime.fromisoformat(modified_time).date()
                            else:
                                modified_date = modified_time.date()
                            
                            if week_start_date <= modified_date <= week_end_date:
                                closed_deals.append(deal)
                                
                                # Check if it's a won deal
                                if stage_name in positive_stages.get(pipeline, []):
                                    won_deals.append(deal)
                                break
                        except Exception:
                            continue
        
        # Total movements: any deals that had stage changes in this week
        movements = []
        for deal in pipeline_deals:
            stage_history = deal.get("stage_history", [])
            
            for stage_entry in stage_history:
                modified_time = stage_entry.get("Modified_Time")
                if modified_time:
                    try:
                        if isinstance(modified_time, str):
                            modified_date = datetime.fromisoformat(modified_time).date()
                        else:
                            modified_date = modified_time.date()
                        
                        if week_start_date <= modified_date <= week_end_date:
                            if deal not in movements:
                                movements.append(deal)
                            break
                    except Exception:
                        continue
        
        # Calculate win percentage
        win_percentage = 0
        if len(closed_deals) > 0:
            win_percentage = round((len(won_deals) / len(closed_deals)) * 100, 1)
        
        # Add metrics for this week and pipeline
        results.append({
            "week": week_name,
            "pipeline": pipeline,
            "new_deals": len(new_deals),
            "closed_deals": len(closed_deals),
            "total_movements": len(movements),
            "win_percentage": win_percentage,
            "new_deals_list": new_deals,
            "closed_deals_list": closed_deals,
            "won_deals_list": won_deals,
            "movements_list": movements
        })
    
    return results


def format_metrics_for_spreadsheet(weekly_metrics: list[dict]):
    """
    Format the weekly metrics for easy spreadsheet export
    
    Args:
        weekly_metrics: List of weekly metrics from calculate_weekly_spreadsheet_metrics
    
    Returns:
        List of dictionaries ready for spreadsheet export
    """
    
    formatted_data = []
    
    # Add header row
    formatted_data.append({
        "Week": "Week",
        "Pipeline": "Pipeline", 
        "New Deals": "New Deals",
        "Closed Deals": "Closed Deals",
        "Total Movements": "Total Movements",
        "Win %": "Win %"
    })
    
    # Add data rows
    for metric in weekly_metrics:
        formatted_data.append({
            "Week": metric["week"],
            "Pipeline": metric["pipeline"],
            "New Deals": metric["new_deals"],
            "Closed Deals": metric["closed_deals"], 
            "Total Movements": metric["total_movements"],
            "Win %": f"{metric['win_percentage']}%"
        })
    
    return formatted_data
