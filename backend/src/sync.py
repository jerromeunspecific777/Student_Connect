from canvasapi import Canvas
from itertools import chain
from todoist_api_python.api import TodoistAPI
import time
import json
from datetime import datetime
import pytz
import requests
import os
from tabulate import tabulate
from src.utils_sync import most_common_number, is_recent_date, is_upcoming, getTimeZone, getViewDate, checkdbsTodoist, checkdbsNotion, find_index, createdata
from src.logger import get_logger

logger = get_logger(__name__)

def sync_CanvasTodist(tokenC, tokenT, url, user_timezone_backup=None):
    # Initialize the Canvas and Todoist API clients
    canvas = Canvas(url, tokenC)
    todoist = TodoistAPI(tokenT)
    
    # Get the user timezone using the provided token
    user_timezone = getTimeZone(tokenT)
    if not user_timezone and user_timezone_backup:
        logger.info(f"Using backup timezone: {user_timezone_backup}")
        user_timezone = user_timezone_backup
    
    # Get all the available courses from Canvas
    courses = canvas.get_courses()
    
    available_courses = []

    # Filter courses that are available and belong to the most common term
    for course in courses:
        try:
            fullcourse = canvas.get_course(course.id)
            if fullcourse.workflow_state == "available" and is_recent_date(fullcourse.start_at_date):
                available_courses.append(course)
        except AttributeError:
            pass
        except Exception:
            pass
    
    # Initialize the databases for Todoist and Canvas tasks
    o = 0
    i = 0
    todoistDB = {}
    canvasDB = {}

    tasks_iterator = todoist.get_tasks()
    tasks = chain.from_iterable(tasks_iterator)

    # Loop through the Todoist tasks and store upcoming ones in the todoistDB
    for task in tasks:
        tdateo = task.due.date
        if is_upcoming(tdateo):
            todoistDB[o] = {'name': task.content, 'date': tdateo, 'id': task.id}
            o += 1
    
    # Loop through Canvas courses to store upcoming assignments in the canvasDB
    for course in available_courses:
        firstcourse = canvas.get_course(course.id)
        assingments = firstcourse.get_assignments()
        for a in assingments:
            adate = a.due_at
            if is_upcoming(adate):
                canvasDB[i] = {'name': a.name, 'date': adate}
                i += 1

    numofupdate = 0
    numofnew = 0
    newDB = []
    updateDB = []
    updated = False
    
    # Compare and update tasks in Todoist based on Canvas assignments
    for course in available_courses:
        firstcourse = canvas.get_course(course.id)
        assingments = firstcourse.get_assignments()
        for a in assingments:
            adate = a.due_at
            if is_upcoming(adate):
                viewdate = getViewDate(adate, user_timezone)
                clean_date = adate.replace('Z', '+00:00').replace(' ', 'T')
                due_dt_obj = datetime.fromisoformat(clean_date)
                if checkdbsTodoist(todoistDB, canvasDB, a.name):
                    tindex = find_index(todoistDB, a.name)
                    if tindex is not None:
                        todoist.delete_task(todoistDB[tindex]['id'])
                        oduedate = getViewDate(todoistDB[tindex]['date'], user_timezone)
                        numofupdate += 1
                        updateDB.append([a.name, oduedate, viewdate])
                        updated = True    
                    todoist.add_task(
                        content=a.name,
                        description=a.html_url,
                        due_datetime=due_dt_obj,
                    )
                    numofnew += 1
                    if not updated:
                        newDB.append([a.name, viewdate])
                    elif updated:
                        updated = False
                    time.sleep(1)
    
    logger.info(f"Sync complete. Added: {numofnew - numofupdate}, Updated: {numofupdate}")
    return {"Added": f"{numofnew-numofupdate}", "Updated": f"{numofupdate}", "newDB": newDB, "updateDB": updateDB}


def sync_CanvasNotion(tokenC, tokenN, database_id, timezone, canvas_url):
    canvas = Canvas(canvas_url, tokenC)
    headers = {
        "Authorization": "Bearer " + tokenN,
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    def create_page(data: dict):
        create_url = "https://api.notion.com/v1/pages"

        payload = {"parent": {"database_id": database_id}, "properties": data}
        try:
            res = requests.post(create_url, headers=headers, json=payload)
            return res
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create page: {e}")
            return None

    def get_pages(num_pages=None):
        """
        If num_pages is None, get all pages, otherwise just the defined number.
        """
        url = f"https://api.notion.com/v1/databases/{database_id}/query"

        get_all = num_pages is None
        page_size = 100 if get_all else num_pages

        payload = {"page_size": page_size}
        response = requests.post(url, json=payload, headers=headers)

        data = response.json()

        import json
        with open('db.json', 'w', encoding='utf8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        results = data["results"]
        while data["has_more"] and get_all:
            payload = {"page_size": page_size, "start_cursor": data["next_cursor"]}
            url = f"https://api.notion.com/v1/databases/{database_id}/query"
            response = requests.post(url, json=payload, headers=headers)
            data = response.json()
            results.extend(data["results"])

        return results

    def archive_page(page_id):
        url = f"https://api.notion.com/v1/pages/{page_id}"

        payload = {
            "archived": True
        }

        try:
            response = requests.patch(url, headers=headers, json=payload)

            if response.status_code == 200:
                pass
            else:
                print(
                    f"Failed to archive page: {page_id}, Status code: {response.status_code}, Response: {response.text}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error archiving page: {e}")

    pages = get_pages()
    notionDB = {}
    canvasDB = {}

    for index, page in enumerate(pages):
        page_id = page["id"]
        props = page["properties"]
        if "Title" in props and "title" in props["Title"] and len(props["Title"]["title"]) > 0:
            title = props["Title"]["title"][0]["text"]["content"]
            duedate = props["Due Date"]["date"]["start"]
            notionDB[index] = {'name': title, 'date': duedate.replace(".000", ""), 'id': page_id.replace("-", "")}
        else:
            continue

    courses = canvas.get_courses()
    available_courses = []

    # Filter courses that are available and belong to the most common term
    for course in courses:
        try:
            fullcourse = canvas.get_course(course.id)
            if fullcourse.workflow_state == "available" and is_recent_date(fullcourse.start_at_date):
                available_courses.append(course)
        except AttributeError:
            pass
        except Exception:
            pass
    
    i = 0
    for course in available_courses:
        firstcourse = canvas.get_course(course.id)
        assingments = firstcourse.get_assignments()
        for a in assingments:
            adate = a.due_at
            if is_upcoming(adate):
                canvasDB[i] = {'name': a.name, 'date': adate}
                i += 1

    numofupdate = 0
    numofnew = 0
    newDB = []
    updateDB = []
    updated = False

    for course in available_courses:
        firstcourse = canvas.get_course(course.id)
        assingments = firstcourse.get_assignments()
        for a in assingments:
            adate = a.due_at
            if is_upcoming(adate):
                utctime = datetime.fromisoformat(adate.replace("Z", "+00:00"))
                user_timezone = pytz.timezone(timezone)
                duedate = utctime.astimezone(user_timezone).isoformat()
                tempdate = utctime.astimezone(user_timezone)
                viewdate = tempdate.strftime("%B %d %I:%M %p")
                if checkdbsNotion(notionDB, canvasDB, a.name):
                    nindex = find_index(notionDB, a.name)
                    if nindex is not None or nindex in notionDB:
                        archive_page(notionDB[nindex]['id'])
                        odate = datetime.fromisoformat(notionDB[nindex]['date'].replace("Z", "+00:00"))
                        oduedate = odate.strftime("%B %d %I:%M %p")
                        numofupdate += 1
                        updateDB.append([a.name, oduedate, viewdate])
                        updated = True
                    create_page(createdata(a.name, duedate, a.html_url))
                    numofnew += 1
                    if not updated:
                        newDB.append([a.name, viewdate])
                    elif updated:
                        updated = False
                    time.sleep(1)
    
    logger.info(f"Sync complete. Added: {numofnew - numofupdate}, Updated: {numofupdate}")
    return {"Added": f"{numofnew - numofupdate}", "Updated": f"{numofupdate}", "newDB": newDB, "updateDB": updateDB}
