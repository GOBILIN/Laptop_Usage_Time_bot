import datetime
import psutil
import time
import firebase_admin
from firebase_admin import credentials, db
import pygetwindow as gw
import re
from secret import DATABASE_URL

# Initialize the Firebase app
try:
    # Use your Firebase service account key file
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': DATABASE_URL
    })
    print("Firebase connection successful!")
except Exception as e:
    print(f"Error initializing Firebase: {e}")
    exit()

# Get references to the database paths
# We'll use separate paths for system usage and app usage
system_usage_ref = db.reference('system_usage')
app_usage_ref = db.reference('app_usage')


def sanitize_app_name(app_name):
    """
    Sanitizes the application name to be a valid Firebase key.

    Replaces characters that are not alphanumeric, spaces, or hyphens with underscores.
    Then, replaces spaces with underscores. This is a robust way to handle special
    characters that might come from window titles.
    """
    # Replace illegal characters with underscores
    sanitized = re.sub(r'[.#$\[\]/]', '_', app_name)
    return sanitized


def get_current_data():
    """Fetches current CPU, memory, and disk usage."""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    disk_info = psutil.disk_usage('C:')

    return {
        'cpu_percent': cpu_percent,
        'memory_percent': memory_info.percent,
        'disk_percent': disk_info.percent,
        'timestamp': datetime.datetime.now().isoformat()
    }


def update_system_data(current_data):
    """
    Updates the database with new system usage data using a transaction.

    This ensures that concurrent updates don't overwrite each other.
    """

    def transaction_callback(current_db_data):
        if current_db_data is None:
            current_db_data = {}

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_db_data[timestamp] = current_data

        sorted_keys = sorted(current_db_data.keys(), reverse=True)
        if len(sorted_keys) > 5:
            for key_to_delete in sorted_keys[5:]:
                del current_db_data[key_to_delete]

        return current_db_data

    try:
        system_usage_ref.transaction(transaction_callback)
    except Exception as e:
        print(f"Error updating system data: {e}")


def update_app_usage_data(app_name, duration):
    """
    Updates the total usage time for a specific application in the database.

    Uses a transaction to safely increment the total time.
    """

    def transaction_callback(current_app_data):
        # If the app is new, initialize its time to the current duration
        if current_app_data is None:
            return duration
        # Otherwise, add the new duration to the existing total
        return current_app_data + duration

    try:
        app_usage_ref.child(app_name).transaction(transaction_callback)
    except Exception as e:
        print(f"Error updating app usage data: {e}")


if __name__ == "__main__":
    print(f"Switched to: LaptopUsageTracker – main.py")
    print("Tracking active window and system usage. Press Ctrl+C to stop.")

    # Store the last time we checked the active window
    last_check_time = time.time()

    try:
        while True:
            # Get the current active window title
            active_window = gw.getActiveWindow()
            if active_window:
                app_name = active_window.title
                # Some windows have no title, we'll ignore them
                if app_name:
                    # Sanitize the app name before using it as a database key
                    sanitized_app_name = sanitize_app_name(app_name)

                    # Calculate time elapsed since last check
                    current_time = time.time()
                    duration = current_time - last_check_time

                    # Update the app usage time in the database
                    update_app_usage_data(sanitized_app_name, duration)

                    print(f"Current App: {app_name}, Time Spent: {duration:.2f} seconds")

                    # Also update the system usage data every 30 seconds to avoid excessive calls
                    if int(current_time) % 30 == 0:
                        usage_data = get_current_data()
                        update_system_data(usage_data)
                        print("System usage data updated.")

                    last_check_time = current_time

            # Pause for 1 second to not overwhelm the system or database
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping the tracker. Goodbye!")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
