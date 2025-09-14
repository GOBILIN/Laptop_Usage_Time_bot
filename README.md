Laptop Usage Tracker and Telegram Bot

This project is a two-part system designed to track your laptop usage and provide reports on demand via a Telegram bot. The system consists of a background script that logs system and application usage to a Firebase Realtime Database and a separate Telegram bot that can be queried for this data.
Features

    System Usage Tracking: Monitors and logs CPU, memory, and disk usage.

    Application Usage Tracking: Tracks the time spent on each active application.

    Real-time Data Storage: All data is stored in a Firebase Realtime Database.

    Telegram Bot Interface: Interact with the usage data using simple commands.

    On-Demand Reports:

        /usage: Get a report on the latest system resource usage.

        /app_usage: See the total time spent on each application.

        /total_time: View your total on-screen time.

Prerequisites

Before running the scripts, you will need to set up the following:

    Python 3.7+: Ensure you have a recent version of Python installed.

    Firebase Realtime Database:

        Create a new Firebase project and a Realtime Database instance.

        Navigate to Project Settings -> Service Accounts -> Generate new private key. This will download a firebase_key.json file.

        Place this firebase_key.json file in the same directory as your Python scripts.

    Telegram Bot:

        Open Telegram and search for the "BotFather" bot.

        Use the /newbot command and follow the instructions to create a new bot.

        BotFather will provide you with a unique bot token. Copy this token.

Installation

    Clone this repository:

    git clone [https://github.com/your-username/your-repository.git](https://github.com/your-username/your-repository.git)
    cd your-repository

    Install the required Python libraries:

    pip install firebase-admin psutil pygetwindow python-telegram-bot

Usage

This project has two separate scripts that should be run independently.
1. Start the Tracker

The tracker.py script continuously logs data to Firebase. Run it in a terminal to begin tracking your laptop usage.

python tracker.py

This script will run in the background.
2. Start the Telegram Bot

The main.py script runs the Telegram bot. Before running it, open main.py and replace "YOUR_TELEGRAM_BOT_TOKEN_HERE" with the token you copied from BotFather.

Then, run the script in a separate terminal:

python main.py

Once the bot is running, you can open Telegram and use the commands to get reports on your usage.
