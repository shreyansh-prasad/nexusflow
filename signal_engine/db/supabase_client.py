# ============================================================
# db/supabase_client.py
# ============================================================
# What is this file?
#   This file handles ALL communication with our database
#   (Supabase). Think of it like a post office:
#     - We hand it a letter (DisruptionSignal)
#     - It puts it in the correct envelope
#     - And delivers it to the database
#
# What is Supabase?
#   Supabase is like Google Sheets but for professional apps.
#   It lives in the cloud. We can add rows, read rows, and
#   even get notified when a new row is added (Person C uses this
#   for the live dashboard).
#
# What is async / await?
#   When your code asks the database "please save this data",
#   it normally WAITS doing nothing. async/await lets Python
#   do other things while it waits — like a waiter who takes
#   your order, then goes to serve another table while the
#   kitchen cooks, instead of just standing there staring.
# ============================================================

from supabase import create_client, Client   # official Supabase Python library
from config import SUPABASE_URL, SUPABASE_KEY
from models.disruption_signal import DisruptionSignal
from datetime import datetime, timezone, timedelta
import asyncio   # asyncio is Python's toolbox for async programming
import logging   # logging prints messages to the terminal (like a diary)

# ── Set up logging ────────────────────────────────────────────
# Instead of print(), professionals use logging.
# It adds timestamps and log levels (INFO, WARNING, ERROR).
logger = logging.getLogger(__name__)


# ── Create the database connection ───────────────────────────
# create_client() connects to our Supabase project.
# This connection is created ONCE when the file is imported,
# then reused for every database call (efficient!).
_supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ── Main function: save a disruption to the database ─────────
async def insert_disruption_event(signal: DisruptionSignal) -> str | None:
    """
    Takes a DisruptionSignal and saves it to the
    'disruption_events' table in Supabase.

    Returns the new row's UUID if successful, None if it failed.

    Example:
        new_id = await insert_disruption_event(my_signal)
        print(f"Saved with ID: {new_id}")
    """
    try:
        # .model_dump() converts the Pydantic object into a plain dictionary.
        # Databases don't understand Python objects — they understand key:value pairs.
        data = signal.model_dump()

        # Run the database insert in a thread pool because supabase-py
        # is synchronous (blocking) but our app is async.
        # Think of it as: "Run this slow task in a side room
        #  so the main room stays free."
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,                                          # use default thread pool
            lambda: _supabase.table("disruption_events")  # pick the table
                              .insert(data)                # insert our data dict
                              .execute()                   # actually run the query
        )

        # response.data is a list of the rows that were inserted.
        # We grab the first one and return its id.
        if response.data:
            new_id = response.data[0]["id"]
            logger.info(f"✅ Saved disruption: {signal.signal_type} @ "
                        f"{signal.affected_location} (id={new_id})")
            return new_id
        else:
            logger.warning("⚠️  Insert returned no data.")
            return None

    except Exception as e:
        # If anything goes wrong (network error, wrong table name, etc.)
        # we log the error but DON'T crash the app.
        # The polling loop must keep running even if one insert fails.
        logger.error(f"❌ Failed to insert disruption event: {e}")
        return None


# ── Deduplication check ───────────────────────────────────────
async def is_duplicate(signal: DisruptionSignal, window_hours: int = 2) -> bool:
    """
    Checks if we already saved a very similar signal in the last
    `window_hours` hours.

    Why? Without this, every 60-second poll would insert the same
    "Mumbai cyclone" 50 times in a row, spamming the dashboard.

    Returns True  → we already have this, skip it.
    Returns False → this is new, save it.
    """
    try:
        # Calculate the cutoff time: now minus 2 hours
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=window_hours)).isoformat()

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: _supabase.table("disruption_events")
                              .select("id")              # we only need the id column
                              .eq("signal_type", signal.signal_type)          # same type?
                              .eq("affected_location", signal.affected_location) # same place?
                              .gte("created_at", cutoff) # created after our cutoff?
                              .execute()
        )

        # If the result has any rows → duplicate found
        duplicate_found = len(response.data) > 0
        if duplicate_found:
            logger.debug(f"🔁 Duplicate skipped: {signal.signal_type} @ "
                         f"{signal.affected_location}")
        return duplicate_found

    except Exception as e:
        logger.error(f"❌ Deduplication check failed: {e}")
        # If the check itself fails, return False to be safe
        # (better to have a duplicate than to miss a real alert)
        return False


# ── Fetch disruption history ──────────────────────────────────
async def get_disruption_history(limit: int = 10) -> list[dict]:
    """
    Fetches the last `limit` disruption events from the database,
    newest first.

    Used by the GET /api/disruptions/history endpoint.
    """
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: _supabase.table("disruption_events")
                              .select("*")               # all columns
                              .order("created_at", desc=True)  # newest first
                              .limit(limit)
                              .execute()
        )
        return response.data or []

    except Exception as e:
        logger.error(f"❌ Failed to fetch disruption history: {e}")
        return []
