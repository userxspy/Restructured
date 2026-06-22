import re
from os import environ


# ==========================================
# ⚙️ HELPER FUNCTIONS
# ==========================================

def is_enabled(type, value):
    data = environ.get(type, str(value))
    if data.lower() in ["true", "yes", "1", "enable", "y"]:
        return True
    elif data.lower() in ["false", "no", "0", "disable", "n"]:
        return False
    else:
        print(f'Error - {type} is invalid, exiting now')
        exit()

def is_valid_ip(ip):
    ip_pattern = r'\b(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
    return re.match(ip_pattern, ip) is not None


# ==========================================
# 🤖 BOT CREDENTIALS
# ==========================================

API_ID = environ.get('API_ID', '')
if len(API_ID) == 0:
    print('Error - API_ID is missing, exiting now')
    exit()
else:
    API_ID = int(API_ID)

API_HASH = environ.get('API_HASH', '')
if len(API_HASH) == 0:
    print('Error - API_HASH is missing, exiting now')
    exit()

BOT_TOKEN = environ.get('BOT_TOKEN', '')
if len(BOT_TOKEN) == 0:
    print('Error - BOT_TOKEN is missing, exiting now')
    exit()

PORT = int(environ.get('PORT', '80'))
PICS = (environ.get('PICS', 'https://telegra.ph/file/58fef5cb458d5b29b0186.jpg')).split()


# ==========================================
# 👮 AUTHORIZED ADMINS
# ==========================================

ADMINS = environ.get('ADMINS', '')
if len(ADMINS) == 0:
    print('Error - ADMINS is missing, exiting now')
    exit()
else:
    ADMINS = [int(x) for x in ADMINS.split()]


# ==========================================
# 📂 INDEX CHANNELS & LOG CHANNEL
# ==========================================

INDEX_CHANNELS = [
    int(x) if x.startswith("-") else x
    for x in environ.get('INDEX_CHANNELS', '').split()
]

LOG_CHANNEL = environ.get('LOG_CHANNEL', '')
if len(LOG_CHANNEL) == 0:
    print('Error - LOG_CHANNEL is missing, exiting now')
    exit()
else:
    LOG_CHANNEL = int(LOG_CHANNEL)


# ==========================================
# 🗄️ MONGODB CONFIGURATION
# ==========================================

DATABASE_URL = environ.get('DATABASE_URL', "")
if len(DATABASE_URL) == 0:
    print('Error - DATABASE_URL is missing, exiting now')
    exit()

DATABASE_NAME = environ.get('DATABASE_NAME', "Cluster0")
COLLECTION_NAME = environ.get('COLLECTION_NAME', 'Files')


# ==========================================
# 🌐 STREAMING ENGINE SETTINGS
# ==========================================

IS_STREAM = is_enabled('IS_STREAM', True)

BIN_CHANNEL = environ.get("BIN_CHANNEL", "")
if len(BIN_CHANNEL) == 0:
    print('Error - BIN_CHANNEL is missing, exiting now')
    exit()
else:
    BIN_CHANNEL = int(BIN_CHANNEL)

URL = environ.get("URL", "")
if len(URL) == 0:
    print('Error - URL is missing, exiting now')
    exit()
else:
    if URL.startswith(('https://', 'http://')):
        if not URL.endswith("/"):
            URL += '/'
    elif is_valid_ip(URL):
        URL = f'http://{URL}/'
    else:
        print('Error - URL is not valid, exiting now')
        exit()


# ==========================================
# 🔧 MISC SETTINGS
# ==========================================

FILE_CAPTION = environ.get("FILE_CAPTION", "<b>{file_name}</b>")
MAX_BTN = int(environ.get('MAX_BTN', 12))
CACHE_TIME = int(environ.get('CACHE_TIME', 300))
IS_PM_SEARCH = is_enabled('IS_PM_SEARCH', True)
PROTECT_CONTENT = is_enabled('PROTECT_CONTENT', False)
REACTIONS = ["🤝", "😇", "🤗", "😍", "👍", "⚡️", "😎", "🔥"]


# ==========================================
# 📝 MESSAGE TEMPLATES  (was Script.py)
# ==========================================

class script:

    START_TXT = """<b>Hey {}, <i>{}</i>

I am your personal auto filter bot. Send me the movie or file name to get direct links instantly... ⚡️</b>"""

    STATUS_TXT = """🗃️ <b>Database Status (Bot Stats):</b>

📂 Total Files: <code>{}</code>
🦹 Total Admins: <code>{}</code>
🚀 Used Storage: <code>{}</code>
🗂️ Free Storage: <code>{}</code>
⏰ Uptime: <code>{}</code>"""

    NOT_FILE_TXT = """👋 <b>Hey {},

No file found in the database with the keyword <code>{}</code>! 🥲

👉 Please check the spelling or search again with the correct name.</b>"""

    FILE_CAPTION = FILE_CAPTION

    HELP_TXT = """<b>🤖 Admin Commands List:</b>

📂 <b>Indexing</b>
🔹 /index_channels - View indexed channels
🔹 Forward a channel message to start indexing

📊 <b>Stats & Info</b>
🔹 /stats - Live bot & database status
🔹 /ping - Check response speed
🔹 /id - View user or chat ID

🗑️ <b>Database</b>
🔹 /delete &lt;keyword&gt; - Delete files by keyword
🔹 /delete_all - Wipe entire database

🔍 <b>Search</b>
🔹 /search on/off - Toggle search in current chat (PM or Group)

🔗 <b>Links</b>
🔹 /link - Reply to any file to get stream & download links"""
