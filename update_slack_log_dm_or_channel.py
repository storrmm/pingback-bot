import os
from slack_sdk import WebClient
import openpyxl
from datetime import datetime, timedelta
import pytz

# === CONFIGURATION FROM ENV VARIABLES ===
SLACK_TOKEN = os.environ.get("SLACK_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
EXCEL_FILE = os.environ.get("EXCEL_FILE")
MY_USER_ID = os.environ.get("MY_USER_ID")
POST_TO_CHANNEL = os.environ.get("POST_MODE", "channel") == "channel"

# Optional: Parse excluded users from comma-separated env var
excluded = os.environ.get("EXCLUDED_USERS", "")
EXCLUDED_USERS = set(excluded.split(",")) if excluded else set()

client = WebClient(token=SLACK_TOKEN)

def fetch_messages():
    tz = pytz.timezone("Asia/Kolkata")
    now = datetime.now(tz)

    if 0 <= now.hour < 6:
        target_day = now - timedelta(days=1)
    else:
        target_day = now

    start = target_day.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)

    oldest = int(start.timestamp())
    latest = int(end.timestamp())

    response = client.conversations_history(channel=CHANNEL_ID, oldest=oldest, latest=latest, limit=1000)
    messages = response['messages']

    users = {}
    for msg in messages:
        if 'user' not in msg: continue
        user = msg['user']
        ts = float(msg['ts'])
        time = datetime.fromtimestamp(ts, tz)
        hour = time.hour

        if user not in users:
            users[user] = {'morning': None, 'evening': None}

        if 6 <= hour < 12 and not users[user]['morning']:
            users[user]['morning'] = time
        elif 17 <= hour <= 22:
            users[user]['evening'] = time

    return users, start

def get_user_name(user_id):
    try:
        response = client.users_info(user=user_id)
        return response['user']['real_name']
    except:
        return user_id

def get_all_user_ids_in_channel():
    user_ids = set()
    cursor = None
    while True:
        response = client.conversations_members(channel=CHANNEL_ID, cursor=cursor)
        for user_id in response['members']:
            try:
                user_info = client.users_info(user=user_id)
                if user_info['user'].get('is_bot'):
                    continue
                user_ids.add(user_id)
            except:
                continue
        cursor = response.get('response_metadata', {}).get('next_cursor')
        if not cursor:
            break
    return user_ids

def get_excluded_users(reporting_day):
    weekday = reporting_day.weekday()  # Monday = 0, Sunday = 6
    if weekday == 6:
        return "ALL"  # Sunday
    elif weekday == 5:
        return BASE_EXCLUDED_USERS.union(SATURDAY_SKIP_USERS)
    else:
        return BASE_EXCLUDED_USERS

def write_to_excel(user_data, date):
    wb = openpyxl.load_workbook(EXCEL_FILE)
    ws = wb.active
    
    ws.delete_rows(2, ws.max_row)
    
    date_str = date.strftime("%Y-%m-%d")

    all_users = get_all_user_ids_in_channel()

    excluded_users = get_excluded_users(date)
    if excluded_users == "ALL":
        print("🛑 Sunday — skipping all users.")
        return

    for user_id in all_users:
        if user_id in excluded_users:
            continue

        times = user_data.get(user_id, {})
        morning = times.get('morning')
        evening = times.get('evening')
        name = get_user_name(user_id)

        morning_str = morning.strftime("%I:%M %p") if morning else ""
        evening_str = evening.strftime("%I:%M %p") if evening else ""
        status = "✅" if morning and evening else "❌"

        ws.append([date_str, user_id, name, morning_str, evening_str, status])

    wb.save(EXCEL_FILE)

def send_reminder(missing_user_ids):
    if not missing_user_ids:
        return

    mentions = " ".join([f"<@{uid}>" for uid in missing_user_ids])
    message = (
        f"👋 These users haven’t posted their evening update yet:\n"
        f"{mentions}\n\nPlease follow up."
    )

    target = CHANNEL_ID if POST_TO_CHANNEL else YOUR_USER_ID
    print("Sending message to:", target)
    client.chat_postMessage(
        channel=target,
        text=message
    )

def is_evening_or_early():
    now = datetime.now(pytz.timezone("Asia/Kolkata"))
#    return 17 <= now.hour < 24 or 0 <= now.hour < 6
    return 11 <= now.hour < 24 or 0 <= now.hour < 6


def main():
    user_data, reporting_day = fetch_messages()
    all_user_ids = get_all_user_ids_in_channel()
    excluded_users = get_excluded_users(reporting_day)

    if excluded_users == "ALL":
        print(" Sunday — skipping log and reminders.")
        return
      
#  uncomment the line below if you want to write the user info to an excel.
#    write_to_excel(user_data, reporting_day)

    if is_evening_or_early():
        print("DM window active (5 PM – 6 AM)")

        incomplete_evening_users = [
            uid for uid in all_user_ids
            if uid not in excluded_users and
               user_data.get(uid) and
               user_data[uid].get('morning') and
               not user_data[uid].get('evening')
        ]

        print("Users to be reminded:", incomplete_evening_users)

        if not incomplete_evening_users:
            print(" No reminder needed — all users posted.")
        else:
            send_reminder(incomplete_evening_users)
            print(" Reminder sent.")
    else:
        print(" Not in DM window — no reminder sent.")

if __name__ == "__main__":
    main() 
