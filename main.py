import datetime
import psutil
import time
import firebase_admin
from firebase_admin import credentials, db
import pygetwindow as gw
import re
import sys
import os
from secret import DATABASE_URL


def resource_path(filename: str) -> str:
    """
    Get absolute path to a resource, works for both .py and .exe.
    """
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.abspath("."), filename)


# Initialize the Firebase app
try:
    key_path = resource_path("serviceAccountKey.json")
    cred = credentials.Certificate(key_path)
    firebase_admin.initialize_app(cred, {
        'databaseURL': DATABASE_URL
    })
    print("Firebase connection successful!")
except Exception as e:
    print(f"Error initializing Firebase: {e}")
    sys.exit(1)

# Get references to the database paths
# The path now includes the current date to create a new record each day.
def get_daily_refs():
    today = datetime.date.today().isoformat()
    return {
        'system_usage_ref': db.reference(f'system_usage/{today}'),
        'app_usage_ref': db.reference(f'app_usage/{today}')
    }


def sanitize_app_name(app_name):
    """
    Sanitizes app names to be valid Firebase keys.
    """
    sanitized = re.sub(r'[.#$\[\]/]', '_', app_name)
    return sanitized


def get_current_data():
    """
    Retrieves current system resource usage data.
    """
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
    Updates the system usage data in Firebase for the current day.
    """
    system_usage_ref = get_daily_refs()['system_usage_ref']

    def transaction_callback(current_db_data):
        if current_db_data is None:
            current_db_data = {}

        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        current_db_data[timestamp] = current_data

        # Keep only the latest 10 records for better performance
        sorted_keys = sorted(current_db_data.keys(), reverse=True)
        if len(sorted_keys) > 10:
            for key_to_delete in sorted_keys[10:]:
                del current_db_data[key_to_delete]

        return current_db_data

    try:
        system_usage_ref.transaction(transaction_callback)
    except Exception as e:
        print(f"Error updating system data: {e}")


def update_app_usage_data(app_name, duration):
    """
    Updates the app usage data in Firebase for the current day.
    """
    app_usage_ref = get_daily_refs()['app_usage_ref']
    sanitized_app_name = sanitize_app_name(app_name)

    def transaction_callback(current_app_data):
        if current_app_data is None:
            return duration
        return current_app_data + duration

    try:
        app_usage_ref.child(sanitized_app_name).transaction(transaction_callback)
    except Exception as e:
        print(f"Error updating app usage data for {app_name}: {e}")


if __name__ == "__main__":
    print(f"Switched to: LaptopUsageTracker – main.py")
    print("Tracking active window and system usage. Press Ctrl+C to stop.")

    last_check_time = time.time()

    try:
        while True:
            active_window = gw.getActiveWindow()
            if active_window:
                app_name = active_window.title
                if app_name:
                    current_time = time.time()
                    duration = current_time - last_check_time

                    update_app_usage_data(app_name, duration)
                    print(f"Current App: {app_name}, Time Spent: {duration:.2f} seconds")

                    # Update system data every 30 seconds
                    if int(current_time) % 30 == 0:
                        usage_data = get_current_data()
                        update_system_data(usage_data)
                        print("System usage data updated.")

                    last_check_time = current_time

            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping the tracker. Goodbye!")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
