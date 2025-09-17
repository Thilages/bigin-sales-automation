from datetime import datetime, timedelta, date
import calendar

def parse_iso_datetime(value: str):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)  # handles +05:30 tz offset
    except Exception:
        return None

def get_time_stamp(date,format="%Y-%m-%d"):
    date = str(date)
    try:
        
        dt = datetime.strptime(date, format)
        return int(dt.timestamp())
    except Exception as e:
        print(f"Error converting date to timestamp: {e}")
        return None
    
def get_week_data(previous_week_count=0):
    if previous_week_count > 0:
        today = date.today() - timedelta(weeks=previous_week_count)
    else:
        today = date.today()

    year = today.year
    month = today.strftime("%B").lower() 
    
    first_day = today.replace(day=1)
    week_num = (today.day - 1) // 7 + 1
    
    week_start = first_day + timedelta(days=(week_num - 1) * 7)
    week_end = week_start + timedelta(days=5)
    
    suffix = {1: "st", 2: "nd", 3: "rd"}.get(week_num if week_num < 20 else week_num % 10, "th")
    week_label = f"{week_num}{suffix}"
    
    return {
        "name": f"{year}_{month}_week_{week_label}",
        "start_date": get_time_stamp(week_start),
        "end_date": get_time_stamp(week_end)
    }