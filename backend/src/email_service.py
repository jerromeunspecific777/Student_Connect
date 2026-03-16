"""
Sync Completion Email Service
Sends a detailed HTML email report after each successful sync.
"""

import yagmail
import os
import datetime
from dotenv import load_dotenv
from src.logger import get_logger

logger = get_logger(__name__)


def _truncate(text, max_len=60):
    """Truncate long assignment names so the table stays compact."""
    return text if len(text) <= max_len else text[:max_len - 1] + "…"


def build_sync_email_html(added_count, updated_count, new_assignments, updated_assignments, service_name):
    """
    Build a professional HTML email matching the Student Connect template style.

    Args:
        added_count (int): Number of newly added assignments.
        updated_count (int): Number of updated assignments.
        new_assignments (list): [[name, due_date], ...]
        updated_assignments (list): [[name, old_date, new_date], ...]
        service_name (str): "Todoist" or "Notion"

    Returns:
        str: Complete HTML email body.
    """

    year = datetime.datetime.now().year

    # ── Build added-assignments rows ──────────────────────
    added_rows = ""
    if new_assignments:
        for item in new_assignments:
            name = _truncate(item[0])
            due = item[1]
            added_rows += f"""
            <tr>
                <td style="padding: 10px 12px; border-bottom: 1px solid #f0f0f0; font-size: 13px; color: #333;">{name}</td>
                <td style="padding: 10px 12px; border-bottom: 1px solid #f0f0f0; font-size: 13px; color: #555; white-space: nowrap;">{due}</td>
            </tr>"""

    added_section = ""
    if new_assignments:
        added_section = f"""
        <div style="margin-top: 28px;">
            <h3 style="margin: 0 0 12px; font-size: 15px; font-weight: 700; color: #1a1a1a;">
                ✅ New Assignments Added ({added_count})
            </h3>
            <table style="width: 100%; border-collapse: collapse; border: 1px solid #eee; border-radius: 10px; overflow: hidden;">
                <thead>
                    <tr style="background: #f8f8f8;">
                        <th style="padding: 10px 12px; text-align: left; font-size: 12px; font-weight: 600; color: #888; text-transform: uppercase; letter-spacing: 0.5px;">Assignment</th>
                        <th style="padding: 10px 12px; text-align: left; font-size: 12px; font-weight: 600; color: #888; text-transform: uppercase; letter-spacing: 0.5px;">Due Date</th>
                    </tr>
                </thead>
                <tbody>
                    {added_rows}
                </tbody>
            </table>
        </div>"""

    # ── Build updated-assignments rows ────────────────────
    updated_rows = ""
    if updated_assignments:
        for item in updated_assignments:
            name = _truncate(item[0])
            old_date = item[1]
            new_date = item[2]
            updated_rows += f"""
            <tr>
                <td style="padding: 10px 12px; border-bottom: 1px solid #f0f0f0; font-size: 13px; color: #333;">{name}</td>
                <td style="padding: 10px 12px; border-bottom: 1px solid #f0f0f0; font-size: 13px; color: #999; text-decoration: line-through; white-space: nowrap;">{old_date}</td>
                <td style="padding: 10px 12px; border-bottom: 1px solid #f0f0f0; font-size: 13px; color: #333; font-weight: 600; white-space: nowrap;">{new_date}</td>
            </tr>"""

    updated_section = ""
    if updated_assignments:
        updated_section = f"""
        <div style="margin-top: 28px;">
            <h3 style="margin: 0 0 12px; font-size: 15px; font-weight: 700; color: #1a1a1a;">
                🔄 Assignments Updated ({updated_count})
            </h3>
            <table style="width: 100%; border-collapse: collapse; border: 1px solid #eee; border-radius: 10px; overflow: hidden;">
                <thead>
                    <tr style="background: #f8f8f8;">
                        <th style="padding: 10px 12px; text-align: left; font-size: 12px; font-weight: 600; color: #888; text-transform: uppercase; letter-spacing: 0.5px;">Assignment</th>
                        <th style="padding: 10px 12px; text-align: left; font-size: 12px; font-weight: 600; color: #888; text-transform: uppercase; letter-spacing: 0.5px;">Old Date</th>
                        <th style="padding: 10px 12px; text-align: left; font-size: 12px; font-weight: 600; color: #888; text-transform: uppercase; letter-spacing: 0.5px;">New Date</th>
                    </tr>
                </thead>
                <tbody>
                    {updated_rows}
                </tbody>
            </table>
        </div>"""

    # ── No changes case ───────────────────────────────────
    no_changes = ""
    if not new_assignments and not updated_assignments:
        no_changes = """
        <div style="text-align: center; margin-top: 28px; padding: 20px; background: #f8f8f8; border-radius: 12px;">
            <p style="margin: 0; font-size: 14px; color: #666;">No new or updated assignments found during this sync.</p>
        </div>"""

    # ── Full email template ───────────────────────────────
    total = int(added_count) + int(updated_count)
    html = f"""
    <div style="font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 560px; margin: 0 auto; padding: 40px; border: 1px solid #f0f0f0; border-radius: 20px; color: #1a1a1a;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="margin: 0; font-size: 24px; font-weight: 800; letter-spacing: -1px; color: #000;">Student Connect</h1>
        </div>

        <div style="text-align: center; margin-bottom: 8px;">
            <div style="display: inline-block; padding: 14px 28px; background-color: #000; border-radius: 12px; color: #fff; font-size: 18px; font-weight: 700; box-shadow: 0 10px 20px rgba(0,0,0,0.1);">
                Sync Complete — {service_name}
            </div>
        </div>

        <div style="text-align: center; margin-bottom: 20px;">
            <p style="margin: 12px 0 0; font-size: 14px; color: #555;">
                {total} assignment{"s" if total != 1 else ""} processed &nbsp;·&nbsp; <strong>{added_count}</strong> added &nbsp;·&nbsp; <strong>{updated_count}</strong> updated
            </p>
        </div>

        {added_section}
        {updated_section}
        {no_changes}

        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">

        <div style="text-align: center; font-size: 12px; color: #aaa;">
            <p style="margin: 0;">&copy; {year} Student Connect. All rights reserved.</p>
        </div>
    </div>
    """
    return html


def send_sync_email(recipient_email, added_count, updated_count, new_assignments, updated_assignments, service_name):
    """
    Send a sync completion email to the user.

    Args:
        recipient_email (str): The user's email address.
        added_count (int/str): Number of newly added assignments.
        updated_count (int/str): Number of updated assignments.
        new_assignments (list): [[name, due_date], ...]
        updated_assignments (list): [[name, old_date, new_date], ...]
        service_name (str): "Todoist" or "Notion"
    """
    try:
        load_dotenv()
        sc_email = os.getenv("EMAIL")
        sc_pass = os.getenv("EMAIL_PASS")

        if not sc_email or not sc_pass:
            logger.warning("Email credentials not configured. Skipping sync email.")
            return

        body = build_sync_email_html(
            added_count, updated_count,
            new_assignments, updated_assignments,
            service_name
        )

        yag = yagmail.SMTP(user=sc_email, password=sc_pass)

        yag.send(
            to=recipient_email,
            subject=f"Student Connect Report — {added_count} Added, {updated_count} Updated ({service_name})",
            contents=body
        )
        logger.info(f"Sync completion email sent successfully")
    except Exception as e:
        # Email failure should never break the sync flow
        logger.error(f"Failed to send sync email: {e}")
