# pingback-bot
A Python-based automation tool that tracks daily task updates posted by team members in a Slack channel. It logs morning and evening messages to an Excel sheet and reminds users (via channel or DM) if they haven't posted their status.

## 🔧 Features

- ✅ Logs daily task updates to an Excel file
- ✅ Checks for both morning and evening messages
- ✅ Sends automated Slack reminders to users who haven't posted
- ✅ Can post reminders in-channel or via DM
- ✅ Configurable excluded users (including weekend handling)
- ✅ GitHub Actions support for automated daily runs

## 📁 Folder Structure

├── update_slack_log.py # Main Python script
├── DailySlackTaskTracker.xlsx # Excel output (auto-updated)
├── requirements.txt
└── .github
└── workflows
└── schedule.yml # GitHub Actions workflow

## ⚙️ Configuration

Edit the following in `update_slack_log.py`:

```python
SLACK_TOKEN = "xoxb-..."  # Your bot token
CHANNEL_ID = "C0XXXXXXX"  # Channel ID where tasks are posted
EXCEL_FILE = "path/to/DailySlackTaskTracker.xlsx"
EXCLUDED_USERS = {"U01234", "U05678"}  # Users to ignore
MY_USER_ID = "U0YOURID"  # Your Slack User ID for DMs
POST_MODE = "dm"  # Options: "channel", "dm"

Weekend logic:
Sunday: no reminders sent
Saturday: specific users can be excluded
