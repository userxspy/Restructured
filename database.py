import re
import base64
import logging
from struct import pack
from hydrogram.file_id import FileId
from pymongo.errors import DuplicateKeyError
from motor.motor_asyncio import AsyncIOMotorClient
from config import DATABASE_URL, DATABASE_NAME, COLLECTION_NAME, MAX_BTN

# ==========================================
# 🗄️ SINGLE SHARED MOTOR CLIENT
# (पहले ia_filterdb + users_chats_db दोनों
#  अलग-अलग AsyncIOMotorClient बनाते थे —
#  अब एक ही connection पूरे project के लिए)
# ==========================================

_client = AsyncIOMotorClient(DATABASE_URL)
_db = _client[DATABASE_NAME]

# Collections
col     = _db[COLLECTION_NAME]   # Files collection
users   = _db["Users"]           # Users collection
bot_col = _db["bot_id"]          # Bot settings collection


# ==========================================
# 📁 FILES DATABASE  (was ia_filterdb.py)
# ==========================================

async def ensure_indexes():
    """बॉट स्टार्ट होते ही MongoDB में indexing फास्ट करने के लिए index सुनिश्चित करें"""
    try:
        await col.create_index([("file_name", "text"), ("caption", "text")])
        await col.create_index([("file_id", 1)])
    except Exception as e:
        logging.error(f"Index Creation Error: {e}")


class Media:
    """File documents का clean wrapper"""
    def __init__(self, data):
        self.file_id   = data.get('_id')
        self.file_name = data.get('file_name')
        self.file_size = data.get('file_size')
        self.caption   = data.get('caption', '')

    @staticmethod
    async def count_documents(filter_query=None):
        return await col.count_documents(filter_query or {})

    @staticmethod
    def find(filter_query=None):
        return col.find(filter_query or {})


async def save_file(media):
    """डेटाबेस में फ़ाइल सेव करें"""
    file_id   = unpack_new_file_id(media.file_id)
    file_name = re.sub(r"@\w+|([_\-\.+])", " ", str(media.file_name))
    file_cap  = re.sub(r"@\w+|([_\-\.+])", " ", str(media.caption)) if media.caption else ""

    document = {
        "_id":       file_id,
        "file_name": file_name,
        "file_size": media.file_size,
        "caption":   file_cap
    }
    try:
        await col.insert_one(document)
        print(f'Saved - {file_name}')
        return 'suc'
    except DuplicateKeyError:
        print(f'Already Saved - {file_name}')
        return 'dup'
    except Exception as e:
        print(f'Saving Error - {file_name}: {e}')
        return 'err'


async def get_search_results(query, max_results=MAX_BTN, offset=0):
    """MongoDB level पर pagination और fast searching"""
    query = str(query).strip()

    if not query:
        filter_dict = {}
    else:
        keywords       = query.split()
        regex_patterns = [re.compile(re.escape(kw), re.IGNORECASE) for kw in keywords]
        filter_dict    = {"$and": [{"file_name": rx} for rx in regex_patterns]}

    cursor       = col.find(filter_dict).sort("$natural", -1).skip(offset).limit(max_results)
    files_data   = await cursor.to_list(length=max_results)
    files        = [Media(d) for d in files_data]
    total        = await col.count_documents(filter_dict)
    next_offset  = offset + max_results
    if next_offset >= total:
        next_offset = ''
    return files, next_offset, total


async def delete_files(query):
    """Query के आधार पर files ढूँढें (delete confirmation के लिए)"""
    query = query.strip()
    if not query:
        filter_dict = {}
    else:
        keywords       = query.split()
        regex_patterns = [re.compile(re.escape(kw), re.IGNORECASE) for kw in keywords]
        filter_dict    = {"$and": [{"file_name": rx} for rx in regex_patterns]}

    total = await col.count_documents(filter_dict)
    files = [Media(d) async for d in col.find(filter_dict)]
    return total, files


async def get_file_details(query):
    """File ID के आधार पर single file विवरण निकालें"""
    files_data = await col.find({'_id': query}).to_list(length=1)
    return [Media(d) for d in files_data]


def encode_file_id(s: bytes) -> str:
    r = b""
    n = 0
    for i in s + bytes([22]) + bytes([4]):
        if i == 0:
            n += 1
        else:
            if n:
                r += b"\x00" + bytes([n])
                n = 0
            r += bytes([i])
    return base64.urlsafe_b64encode(r).decode().rstrip("=")


def unpack_new_file_id(new_file_id):
    decoded = FileId.decode(new_file_id)
    return encode_file_id(
        pack(
            "<iiqq",
            int(decoded.file_type),
            decoded.dc_id,
            decoded.media_id,
            decoded.access_hash
        )
    )


# ==========================================
# 👤 USERS DATABASE  (was users_chats_db.py)
# ==========================================

class Database:
    """Users और bot settings के लिए DB wrapper"""

    async def add_user(self, id, name):
        if not await self.is_user_exist(id):
            await users.insert_one({"id": id, "name": name})

    async def is_user_exist(self, id):
        return bool(await users.find_one({'id': int(id)}))

    async def total_users_count(self):
        return await users.count_documents({})

    async def get_all_users(self):
        return users.find({})

    async def delete_user(self, user_id):
        await users.delete_many({'id': int(user_id)})

    async def get_db_size(self):
        return (await _db.command("dbstats"))['dataSize']

    async def get_pm_search_status(self, bot_id):
        bot = await bot_col.find_one({'id': bot_id})
        if bot and "bot_pm_search" in bot:
            return bot['bot_pm_search']
        return True

    async def update_pm_search_status(self, bot_id, enable):
        await bot_col.update_one(
            {'id': int(bot_id)},
            {'$set': {'bot_pm_search': enable}},
            upsert=True
        )

    async def get_group_search_status(self, bot_id):
        bot = await bot_col.find_one({'id': bot_id})
        if bot and "bot_group_search" in bot:
            return bot['bot_group_search']
        return True

    async def update_group_search_status(self, bot_id, enable):
        await bot_col.update_one(
            {'id': int(bot_id)},
            {'$set': {'bot_group_search': enable}},
            upsert=True
        )


db = Database()
