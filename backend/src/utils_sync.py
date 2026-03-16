from collections import Counter
from datetime import datetime, timezone, timedelta, date
import requests
import pytz
from src.logger import get_logger

logger = get_logger(__name__)

def most_common_number(arr):
    count = Counter(arr)
    
    most_common = count.most_common(1)[0][0]
    
    return most_common

def is_recent_date(date_input, window_days=60):
    if not date_input or str(date_input).upper() == "NULL" or "Restricted" in str(date_input):
        return False

    try:
        clean_input = str(date_input).split('+')[0].replace('T', ' ').replace('Z', '').strip()
        dt_input = datetime.strptime(clean_input, "%Y-%m-%d %H:%M:%S")

        today = datetime.today()
        years = [today.year, today.year - 1]
        months = [1, 6, 8]

        candidates = [datetime(y, m, 1) for y in years for m in months]
        dt_reference = min(candidates, key=lambda d: abs((d - today).days))

        return abs((dt_input - dt_reference).days) <= window_days

    except (ValueError, TypeError):
        return False

def is_upcoming(date_str):
    try:
        if not date_str or str(date_str).upper() == "NULL":
            return False
            
        clean_date = str(date_str).replace('Z', '+00:00').replace(' ', 'T')
        input_dt = datetime.fromisoformat(clean_date)
        
        now = datetime.now(timezone.utc)
        
        if 'T' not in str(date_str) and ' ' not in str(date_str):
            return input_dt.date() >= now.date()
            
        if input_dt.tzinfo is None:
            input_dt = input_dt.replace(tzinfo=timezone.utc)
            
        return input_dt >= now
    except (TypeError, ValueError):
        return False

def find_index(nested_dict, target):
    # Loop through the keys and values in the dictionary
    for key, value in nested_dict.items():
        # Check if both 'name' and 'date' match the target values
        if value['name'] == target or value['date'] == target:
            return key  # Return the key if a match is found
    return None  # Return None if no match is found

def checkdbsTodoist(todoist, canvas, name):
    indexn = find_index(todoist, name)
    indexc = find_index(canvas, name)
    
    if indexn is None:
        return True

    try:
        ndateog = todoist[indexn]['date']
        cdateog = canvas[indexc]['date']

        # 1. Normalize Todoist date (handles date objects and strings)
        if isinstance(ndateog, date) and not isinstance(ndateog, datetime):
            # Convert date to datetime at midnight UTC
            n_dt = datetime.combine(ndateog, datetime.min.time()).replace(tzinfo=timezone.utc)
        else:
            # It's a string, treat it as you did before
            n_dt = datetime.fromisoformat(str(ndateog).replace("Z", "+00:00"))

        # 2. Normalize Canvas string
        c_dt = datetime.fromisoformat(str(cdateog).replace("Z", "+00:00"))

        # 3. Ensure both are timezone-aware for the subtraction
        if n_dt.tzinfo is None: n_dt = n_dt.replace(tzinfo=timezone.utc)
        if c_dt.tzinfo is None: c_dt = c_dt.replace(tzinfo=timezone.utc)

        # 4. Calculate difference
        diff = abs((n_dt - c_dt).total_seconds())
        
        return diff > 60
        
    except (TypeError, ValueError, AttributeError) as e:
        logger.error(f"Sync Check Error for {name}: {e}")
        return True # Default to True to trigger a re-sync if logic fails

def checkdbsNotion(notion, canvas, name):
    indexn = find_index(notion, name)
    indexc = find_index(canvas, name)
    
    if indexn is None:
        return True

    try:
        ndateog = notion[indexn]['date']
        cdateog = canvas[indexc]['date']

        n_dt = datetime.fromisoformat(ndateog.replace("Z", "+00:00"))
        c_dt = datetime.fromisoformat(cdateog.replace("Z", "+00:00"))

        if n_dt.tzinfo is None: 
            n_dt = n_dt.replace(tzinfo=timezone.utc)
        if c_dt.tzinfo is None: 
            c_dt = c_dt.replace(tzinfo=timezone.utc)

        diff = abs((n_dt - c_dt).total_seconds())
        
        return diff > 60

    except (ValueError, TypeError, KeyError):
        return True

def getTimeZone(token):
    # The new unified endpoint for user data
    url = "https://api.todoist.com/sync/v1/sync"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Use the new v1 parameters
    params = {
        "sync_token": "*",
        "resource_types": '["user"]'
    }

    try:
        # Note: Some v1 endpoints now prefer GET for read-only data, 
        # but the sync endpoint remains a POST.
        response = requests.post(url, data=params, headers=headers)
        response.raise_for_status() 
        
        user_data = response.json().get("user", {})
        
        # In the v1 unified response, the path is standardized:
        return user_data.get("tz_info", {}).get("timezone") or user_data.get("timezone")

    except Exception as error:
        logger.error(f"Error getting timezone from Todoist v1: {error}")
        return None

def getViewDate(date, timezone_str):
    try:
        if not date or str(date).upper() == "NULL":
            return "No Date"

        clean_date = str(date).replace('Z', '+00:00').replace(' ', 'T')
        
        tempdate = datetime.fromisoformat(clean_date)
        
        if tempdate.tzinfo is None:
            tempdate = tempdate.replace(tzinfo=pytz.utc)
            
        if not timezone_str:
            # Fallback to UTC if no timezone is provided
            logger.warning("No timezone provided to getViewDate, defaulting to UTC")
            target_timezone = pytz.utc
        else:
            try:
                target_timezone = pytz.timezone(timezone_str)
            except pytz.exceptions.UnknownTimeZoneError:
                 logger.warning(f"Unknown timezone '{timezone_str}', defaulting to UTC")
                 target_timezone = pytz.utc

        tempdate = tempdate.astimezone(target_timezone)
        
        return tempdate.strftime("%B %d %I:%M %p")

    except (ValueError, TypeError) as e:
        logger.error(f"Error in getViewDate: {e}")
        return str(date)

def createdata(title, duedate, url):
    data = {
        "Title": {
            "title": [{"text": {"content": title}}]
        },
        "Due Date": {
            "date": {
                "start": duedate
            }
        },
        "URL": {
            "url": url
        }
    }
    return data