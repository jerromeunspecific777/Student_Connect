"""
Automated Sync Scheduler
Uses APScheduler with MongoDB job store to run syncs at user-defined intervals.
Jobs persist across server restarts.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.triggers.interval import IntervalTrigger
from src.database import db
from src.logger import get_logger
import threading

logger = get_logger(__name__)

# Valid intervals (in hours) — server-side validation
# 24 = 1 day, 72 = 3 days, 168 = 1 week
VALID_INTERVALS = {24, 72, 168}

# Global scheduler instance
scheduler = None


def init_scheduler(app):
    """
    Initialize the APScheduler with MongoDB job store.
    Call once at Flask app startup.
    Reschedules existing user preferences on boot.
    """
    global scheduler

    jobstores = {
        'default': MongoDBJobStore(
            database='Sync',
            collection='scheduler_jobs',
            client=db.client
        )
    }

    scheduler = BackgroundScheduler(jobstores=jobstores)
    scheduler.start()
    logger.info("APScheduler started with MongoDB job store")

    # Reschedule existing user preferences on boot
    _restore_schedules()


def _restore_schedules():
    """
    On server restart, restore scheduled jobs from user preferences in MongoDB.
    APScheduler's MongoDBJobStore handles persistence, but we also check
    user documents to ensure consistency.
    """
    try:
        users = db['user']
        auto_sync_users = users.find(
            {"auto_sync": True, "sync_interval": {"$in": list(VALID_INTERVALS)}},
            {"email": 1, "sync_interval": 1}
        )
        count = 0
        for user in auto_sync_users:
            email = user.get("email")
            interval = user.get("sync_interval")
            if email and interval:
                _add_or_replace_job(email, interval)
                count += 1
        logger.info(f"Restored {count} scheduled sync jobs on startup")
    except Exception as e:
        logger.error(f"Error restoring schedules: {e}")


def _add_or_replace_job(email, interval_hours):
    """Add or replace a recurring sync job for a user."""
    global scheduler
    job_id = f"sync_{email}"

    # Remove existing job if present
    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass

    scheduler.add_job(
        func=_run_scheduled_sync,
        trigger=IntervalTrigger(hours=interval_hours),
        id=job_id,
        args=[email],
        replace_existing=True,
        name=f"Auto-sync for {email}",
        misfire_grace_time=3600  # Allow 1 hour grace for misfired jobs
    )
    logger.info(f"Scheduled sync for {email} every {interval_hours}h")


def schedule_sync(email, interval_hours):
    """
    Public API: Enable or update a user's sync schedule.
    Returns True on success, False on invalid interval.
    """
    if interval_hours not in VALID_INTERVALS:
        logger.warning(f"Invalid interval {interval_hours} for {email}")
        return False

    # Save preference to MongoDB
    users = db['user']
    users.update_one(
        {"email": email},
        {"$set": {"auto_sync": True, "sync_interval": interval_hours}}
    )

    _add_or_replace_job(email, interval_hours)
    return True


def remove_schedule(email):
    """
    Public API: Disable a user's sync schedule.
    """
    global scheduler
    job_id = f"sync_{email}"

    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass

    # Update preference in MongoDB
    users = db['user']
    users.update_one(
        {"email": email},
        {"$set": {"auto_sync": False, "sync_interval": None}}
    )
    logger.info(f"Removed scheduled sync for {email}")


def get_schedule(email):
    """
    Public API: Get a user's current schedule preference.
    Returns dict with auto_sync and sync_interval.
    """
    users = db['user']
    user = users.find_one(
        {"email": email},
        {"auto_sync": 1, "sync_interval": 1, "_id": 0}
    )
    if user:
        return {
            "auto_sync": user.get("auto_sync", False),
            "sync_interval": user.get("sync_interval", None)
        }
    return {"auto_sync": False, "sync_interval": None}


def _run_scheduled_sync(email):
    """
    The actual job function executed by the scheduler.
    Fetches tokens, runs sync, sends email, logs results.
    """
    from src.utils import getDB, decrypt, addSyncLog, update_sync_time
    from src.sync import sync_CanvasTodist, sync_CanvasNotion
    from src.email_service import send_sync_email

    logger.info(f"Running scheduled sync for {email}")

    try:
        whichT = getDB(email, "UseTToken")
        url = getDB(email, "url")

        # Decrypt Canvas token
        raw_ctoken = getDB(email, "CToken")
        if not raw_ctoken:
            logger.error(f"Scheduled sync failed for {email}: No Canvas token")
            return
        CToken = decrypt(raw_ctoken)

        response = None
        service_name = "Todoist" if whichT else "Notion"

        if whichT:
            raw_ttoken = getDB(email, "TToken")
            if not raw_ttoken:
                logger.error(f"Scheduled sync failed for {email}: No Todoist token")
                return
            TToken = decrypt(raw_ttoken)
            stored_timezone = getDB(email, "timezone")
            response = sync_CanvasTodist(CToken, TToken, url, stored_timezone)
        else:
            raw_ntoken = getDB(email, "NToken")
            raw_ndb = getDB(email, "NDatabase")
            if not raw_ntoken or not raw_ndb:
                logger.error(f"Scheduled sync failed for {email}: Incomplete Notion credentials")
                return
            NToken = decrypt(raw_ntoken)
            NDatabase = decrypt(raw_ndb)
            Ntimezone = getDB(email, "timezone")
            response = sync_CanvasNotion(CToken, NToken, NDatabase, Ntimezone, url)

        if response and isinstance(response, dict):
            update_sync_time(email)

            added = response.get("Added", "0")
            updated = response.get("Updated", "0")
            new_assignments = response.get("newDB", [])
            updated_assignments = response.get("updateDB", [])

            addSyncLog(email, added, updated, service_name)

            # Send email in a thread to not block the scheduler
            thread = threading.Thread(
                target=send_sync_email,
                args=(email, added, updated, new_assignments, updated_assignments, service_name)
            )
            thread.daemon = True
            thread.start()

            logger.info(f"Scheduled sync completed for {email}: Added={added}, Updated={updated}")
        else:
            logger.warning(f"Scheduled sync for {email} returned no response")

    except Exception as e:
        logger.error(f"Scheduled sync failed for {email}: {e}")
