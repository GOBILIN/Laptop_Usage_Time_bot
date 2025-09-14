import firebase_admin
from firebase_admin import credentials, db
import json
from secret import DATABASE_URL

# Replace with the path to your service account key file.
# You can generate this from your Firebase console:
# Project settings -> Service accounts -> Generate new private key.
SERVICE_ACCOUNT_KEY_FILE = "serviceAccountKey.json"

# Replace with your Firebase project's database URL.
# You can find this in your Firebase console under "Realtime Database."
DATABASE_URL = DATABASE_URL


def get_data_from_db(path):
    """
    Fetches data from the Firebase Realtime Database at a given path.

    Args:
        path (str): The path to the data in the database (e.g., "users/john_doe").

    Returns:
        dict or None: The data as a Python dictionary, or None if no data exists.
    """
    try:
        # Load the service account credentials from the JSON file.
        cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_FILE)

        # Initialize the app with a service account, granting admin privileges.
        # Check if the app is already initialized to avoid re-initialization errors.
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred, {
                'databaseURL': DATABASE_URL
            })

        # Get a database reference to the specified path.
        ref = db.reference(path)

        # Read the data at the reference. This is a blocking operation.
        data = ref.get()

        if data:
            print(f"Successfully fetched data from '{path}':")
            print(json.dumps(data, indent=2))
            return data
        else:
            print(f"No data found at '{path}'.")
            return None

    except FileNotFoundError:
        print(f"Error: Service account key file not found at '{SERVICE_ACCOUNT_KEY_FILE}'.")
        print("Please download your service account key from the Firebase console and place it in the correct path.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


if __name__ == "__main__":
    # Example usage:
    # Assuming you have a node called 'data' in your database.
    get_data_from_db('data')
