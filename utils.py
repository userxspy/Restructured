import pytz
from datetime import datetime


class temp:
    """State manager for the bot's live session"""
    START_TIME = 0
    ME = None
    CANCEL = False
    U_NAME = None
    B_NAME = None
    FILES = {}
    BOT = None
    INDEX_CANCEL = set()


def get_size(size):
    """Fast method to convert file size from Bytes to KB, MB, GB"""
    units = ["Bytes", "KB", "MB", "GB", "TB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units) - 1:
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])


def get_readable_time(seconds):
    """Function to make the bot's live uptime human-readable"""
    periods = [('d', 86400), ('h', 3600), ('m', 60), ('s', 1)]
    result = ''
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            result += f'{int(period_value)}{period_name}'
    return result if result else '0s'


def get_wish():
    """Function to greet the admin based on the time of day"""
    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(tz).strftime("%H")
    if now < "12":
        return "ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ 🌞"
    elif now < "18":
        return "ɢᴏᴏᴅ ᴀꜰᴛᴇʀɴᴏᴏɴ 🌗"
    else:
        return "ɢᴏᴏᴅ ᴇᴠᴇɴɪɴɢ 🌘"


async def get_seconds(time_string):
    """Function to convert a time string (e.g. 5m, 1h) into seconds"""
    def extract_value_and_unit(ts):
        value = ""
        index = 0
        while index < len(ts) and ts[index].isdigit():
            value += ts[index]
            index += 1
        unit = ts[index:].strip().lower()
        return int(value) if value else 0, unit

    value, unit = extract_value_and_unit(time_string)

    if unit in ['s', 'sec', 'secs']:
        return value
    elif unit in ['min', 'mins', 'm']:
        return value * 60
    elif unit in ['hour', 'hours', 'h']:
        return value * 3600
    elif unit in ['day', 'days', 'd']:
        return value * 86400
    elif unit in ['month', 'months']:
        return value * 86400 * 30
    elif unit in ['year', 'years']:
        return value * 86400 * 365
    return 0
