import time
import math
import random
import asyncio
from hydrogram import Client, filters, enums
from hydrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

from config import (
    ADMINS, INDEX_CHANNELS, LOG_CHANNEL,
    PICS, REACTIONS, BIN_CHANNEL, URL, MAX_BTN
)
from utils import get_size, temp, get_readable_time, get_wish
from database import Media, get_file_details, delete_files, get_search_results, db

BUTTONS = {}


# /start
@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    if message.from_user.id not in ADMINS:
        return await message.reply(
            "🚫 <b>Access Denied!</b>\n\nThis is an <b>Admin-Only</b> bot.\nYou are not authorized to use it."
        )

    try:
        await message.react(emoji=random.choice(REACTIONS), big=True)
    except Exception:
        await message.react(emoji="⚡️", big=True)

    mc = message.command[1] if len(message.command) == 2 else None

    if mc and (mc.startswith("file") or mc.startswith("all")):
        try:
            _, file_id = mc.split("_", 1)
        except ValueError:
            return await message.reply("Invalid Link! ❌")
        file_details = await get_file_details(file_id)
        if not file_details:
            return await message.reply("File not found in database! 😕")
        file = file_details[0]
        from config import script
        cap = script.FILE_CAPTION.format(file_name=file.file_name)
        btn = [[InlineKeyboardButton("🚀 Watch And Download ⚡", callback_data=f"stream#{file.file_id}")],
               [InlineKeyboardButton("🙅 Close", callback_data="close_data")]]
        await client.send_cached_media(chat_id=message.from_user.id, file_id=file.file_id,
                                       caption=cap, reply_markup=InlineKeyboardMarkup(btn))
        return

    from config import script
    buttons = [[InlineKeyboardButton("⚙️ Commands List", callback_data="help")]]
    await message.reply_photo(
        photo=random.choice(PICS),
        caption=script.START_TXT.format(message.from_user.mention, get_wish()),
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# /index_channels
@Client.on_message(filters.command('index_channels') & filters.incoming)
async def channels_info(bot, message):
    if message.from_user.id not in ADMINS:
        return
    if not INDEX_CHANNELS:
        return await message.reply("INDEX_CHANNELS is not configured! ⚙️")
    text = '<b>📂 Indexed Channels:</b>\n\n'
    for id in INDEX_CHANNELS:
        try:
            chat  = await bot.get_chat(id)
            text += f'🔹 {chat.title} (<code>{id}</code>)\n'
        except Exception:
            text += f'❌ {id} (Channel not found / Bot is not admin)\n'
    text += f'\n<b>📊 Total Channels: {len(INDEX_CHANNELS)}</b>'
    await message.reply(text)


# /stats
@Client.on_message(filters.command('stats') & filters.incoming)
async def stats(bot, message):
    if message.from_user.id not in ADMINS:
        return
    try:
        await message.react(emoji=random.choice(REACTIONS), big=True)
    except Exception:
        await message.react(emoji="⚡️", big=True)
    from config import script
    files        = await Media.count_documents()
    admins_count = len(ADMINS)
    uptime       = get_readable_time(time.time() - temp.START_TIME)
    u_size       = get_size(await db.get_db_size())
    f_size       = get_size(max(0, 536870912 - await db.get_db_size()))
    await message.reply_text(script.STATUS_TXT.format(files, admins_count, u_size, f_size, uptime))


# /delete
@Client.on_message(filters.command('delete') & filters.incoming)
async def delete_file(bot, message):
    if message.from_user.id not in ADMINS:
        return
    try:
        query = message.text.split(" ", 1)[1].strip()
    except IndexError:
        return await message.reply_text("<b>Usage: <code>/delete keyword</code></b>")
    msg   = await message.reply_text('Searching... ⏱️')
    total, _ = await delete_files(query)
    if int(total) == 0:
        return await msg.edit('No files found with this keyword! ❌')
    btn = [[InlineKeyboardButton("✅ Yes, Delete", callback_data=f"delete_{query}")],
           [InlineKeyboardButton("❌ Cancel",      callback_data="close_data")]]
    await msg.edit(
        f"🔍 Found <b>{total}</b> files for: <code>{query}</code>\n\nDelete permanently?",
        reply_markup=InlineKeyboardMarkup(btn)
    )


# /delete_all
@Client.on_message(filters.command('delete_all') & filters.incoming)
async def delete_all_index(bot, message):
    if message.from_user.id not in ADMINS:
        return
    files = await Media.count_documents()
    if int(files) == 0:
        return await message.reply_text('Database is already empty! 🗃️')
    btn = [[InlineKeyboardButton("⚠️ Yes, Wipe Entire Database", callback_data="delete_all")],
           [InlineKeyboardButton("❌ Cancel",                     callback_data="close_data")]]
    await message.reply_text(
        f'❗ <b>Warning:</b> <b>{files}</b> files will be deleted.\nAre you sure?',
        reply_markup=InlineKeyboardMarkup(btn)
    )


# /ping
@Client.on_message(filters.command('ping') & filters.incoming)
async def ping(client, message):
    if message.from_user.id not in ADMINS:
        return
    start_time = time.monotonic()
    msg        = await message.reply("⚡")
    end_time   = time.monotonic()
    await msg.edit(f'<b>⏱️ Response Speed: {round((end_time - start_time) * 1000)} ms</b>')


# /id
@Client.on_message(filters.command('id') & filters.incoming)
async def showid(client, message):
    if message.from_user.id not in ADMINS:
        return
    if message.reply_to_message:
        reply = message.reply_to_message
        if reply.forward_from_chat:
            return await message.reply_text(
                f"📣 Channel: <b>{reply.forward_from_chat.title}</b>\n"
                f"🆔 ID: <code>{reply.forward_from_chat.id}</code>"
            )
        elif reply.from_user:
            return await message.reply_text(
                f"🦹 User: {reply.from_user.mention}\n"
                f"🆔 ID: <code>{reply.from_user.id}</code>"
            )
    await message.reply_text(
        f'<b>🦹 Your ID: <code>{message.from_user.id}</code>\n'
        f'💬 Chat ID: <code>{message.chat.id}</code></b>'
    )


# /search on/off  — जहाँ से चलाओ वहाँ का toggle
@Client.on_message(filters.command('search') & filters.incoming)
async def toggle_search(client, message):
    if message.from_user.id not in ADMINS:
        return
    try:
        action = message.command[1].lower()
    except IndexError:
        is_pm    = message.chat.type.name == "PRIVATE"
        location = "PM" if is_pm else "Group"
        current  = await (db.get_pm_search_status(temp.ME) if is_pm else db.get_group_search_status(temp.ME))
        status   = "✅ Enabled" if current else "❌ Disabled"
        return await message.reply(f"<b>{location} Search is currently: {status}</b>\nUsage: <code>/search on</code> or <code>/search off</code>")

    if action not in ['on', 'off']:
        return await message.reply("<b>Usage: <code>/search on</code> or <code>/search off</code></b>")

    is_pm    = message.chat.type.name == "PRIVATE"
    enable   = action == 'on'
    location = "PM" if is_pm else "Group"

    if is_pm:
        await db.update_pm_search_status(temp.ME, enable)
    else:
        await db.update_group_search_status(temp.ME, enable)

    icon = "✅ Enabled" if enable else "❌ Disabled"
    await message.reply(f"<b>{location} Search: {icon}</b>")


# PM Search
@Client.on_message(filters.private & filters.text & filters.incoming & ~filters.regex(r"^/"))
async def pm_search(client, message):
    if message.from_user.id not in ADMINS:
        return
    if not await db.get_pm_search_status(temp.ME):
        return

    search = message.text.strip()
    files, offset, total_results = await get_search_results(search)
    if not files:
        from config import script
        return await message.reply(script.NOT_FILE_TXT.format(message.from_user.mention, search), quote=True)

    req = message.from_user.id
    key = f"{message.chat.id}-{message.id}"
    BUTTONS[key] = search

    files_link = ""
    for file in files:
        files_link += f"\n\n📁 <a href='https://t.me/{temp.U_NAME}?start=file_{file.file_id}'>[{get_size(file.file_size)}] {file.file_name}</a>"

    btn = []
    if offset != "":
        btn.append([InlineKeyboardButton(text=f"🗓 1/{math.ceil(int(total_results) / MAX_BTN)}", callback_data="buttons"),
                    InlineKeyboardButton(text="NEXT ⏩", callback_data=f"next_{req}_{key}_{offset}")])
    btn.append([InlineKeyboardButton("🙅 Close", callback_data=f"close#{req}")])

    await message.reply(
        text=f"<blockquote>🎬 <b>Total {total_results} Files</b></blockquote>{files_link}",
        reply_markup=InlineKeyboardMarkup(btn),
        disable_web_page_preview=True,
        parse_mode=enums.ParseMode.HTML,
        quote=True
    )


# Group Search
@Client.on_message((filters.group | filters.channel) & filters.text & filters.incoming & ~filters.regex(r"^/"))
async def group_search(client, message):
    if not message.from_user or message.from_user.id not in ADMINS:
        return
    if not await db.get_group_search_status(temp.ME):
        return

    search = message.text.strip()
    if not search:
        return
    files, offset, total_results = await get_search_results(search)
    if not files:
        from config import script
        return await message.reply(script.NOT_FILE_TXT.format(message.from_user.mention, search), quote=True)

    req = message.from_user.id
    key = f"{message.chat.id}-{message.id}"
    BUTTONS[key] = search

    files_link = ""
    for file in files:
        files_link += f"\n\n📁 <a href='https://t.me/{temp.U_NAME}?start=file_{file.file_id}'>[{get_size(file.file_size)}] {file.file_name}</a>"

    btn = []
    if offset != "":
        btn.append([InlineKeyboardButton(text=f"🗓 1/{math.ceil(int(total_results) / MAX_BTN)}", callback_data="buttons"),
                    InlineKeyboardButton(text="NEXT ⏩", callback_data=f"next_{req}_{key}_{offset}")])
    btn.append([InlineKeyboardButton("🙅 Close", callback_data=f"close#{req}")])

    await message.reply(
        text=f"<blockquote>🎬 <b>Total {total_results} Files</b></blockquote>{files_link}",
        reply_markup=InlineKeyboardMarkup(btn),
        disable_web_page_preview=True,
        parse_mode=enums.ParseMode.HTML,
        quote=True
    )


# Pagination
@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):
    ident, req, key, offset = query.data.split("_")
    if int(req) != query.from_user.id:
        return await query.answer("This is not for you! ❌", show_alert=True)
    search = BUTTONS.get(key)
    if not search:
        return await query.answer("Search again with a new keyword! 🔄", show_alert=True)

    files, n_offset, total = await get_search_results(search, offset=int(offset))
    if not files:
        return

    files_link = ""
    for file in files:
        files_link += f"\n\n📁 <a href='https://t.me/{temp.U_NAME}?start=file_{file.file_id}'>[{get_size(file.file_size)}] {file.file_name}</a>"

    current_page = math.ceil(int(offset) / MAX_BTN) + 1
    total_pages  = math.ceil(total / MAX_BTN)
    p_buttons = []
    if int(offset) > 0:
        p_buttons.append(InlineKeyboardButton("⏪ BACK", callback_data=f"next_{req}_{key}_{max(0, int(offset) - MAX_BTN)}"))
    p_buttons.append(InlineKeyboardButton(f"🗓 {current_page}/{total_pages}", callback_data="buttons"))
    if n_offset != "":
        p_buttons.append(InlineKeyboardButton("NEXT ⏩", callback_data=f"next_{req}_{key}_{n_offset}"))

    await query.message.edit_text(
        text=f"<blockquote>🎬 <b>Total {total} Files found</b></blockquote>{files_link}",
        reply_markup=InlineKeyboardMarkup([p_buttons, [InlineKeyboardButton("🙅 Close", callback_data=f"close#{req}")]]),
        disable_web_page_preview=True,
        parse_mode=enums.ParseMode.HTML
    )


# All Callbacks
@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    data    = query.data
    user_id = query.from_user.id

    if data.startswith("stream"):
        file_id = data.split('#', 1)[1]
        await query.answer("Generating streaming links... ⏱️")
        msg      = await client.send_cached_media(chat_id=BIN_CHANNEL, file_id=file_id)
        watch    = f"{URL}watch/{msg.id}"
        download = f"{URL}download/{msg.id}"
        btn = [[InlineKeyboardButton("⚡ Watch Online", url=watch),
                InlineKeyboardButton("🚀 Fast Download", url=download)],
               [InlineKeyboardButton("🙅 Close", callback_data="close_data")]]
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(btn))

    elif data == "help":
        from config import script
        await query.message.edit_caption(
            caption=script.HELP_TXT,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]])
        )

    elif data == "back":
        from config import script
        await query.message.edit_caption(
            caption=script.START_TXT.format(query.from_user.mention, get_wish()),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⚙️ Commands List", callback_data="help")]])
        )

    elif data.startswith("delete_") and data != "delete_all":
        query_text = data[len("delete_"):]
        from database import col
        import re
        keywords = query_text.split()
        regex_patterns = [re.compile(re.escape(kw), re.IGNORECASE) for kw in keywords]
        filter_dict = {"$and": [{"file_name": rx} for rx in regex_patterns]}
        result = await col.delete_many(filter_dict)
        await query.message.edit_text(f"<b>✅ Deleted <code>{result.deleted_count}</code> files!</b>")

    elif data == "delete_all":
        from database import col
        result = await col.delete_many({})
        await query.message.edit_text(f"<b>✅ Database wiped! Deleted <code>{result.deleted_count}</code> files.</b>")

    elif data == "close_data":
        await query.message.delete()

    elif data.startswith("close"):
        _, req = data.split("#")
        if int(req) == user_id:
            await query.message.delete()
        else:
            await query.answer("This is not for you! ❌", show_alert=True)

    elif data == "buttons":
        await query.answer("⚙️", show_alert=False)
