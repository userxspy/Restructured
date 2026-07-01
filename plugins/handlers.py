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

# PM search ke liye in-memory pagination state
BUTTONS = {}


# ==========================================
# 🚀 /start  COMMAND
# ==========================================

@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    if message.from_user.id not in ADMINS:
        return

    try:
        await message.react(emoji=random.choice(REACTIONS), big=True)
    except Exception:
        await message.react(emoji="⚡️", big=True)

    mc = message.command[1] if len(message.command) == 2 else None

    # Deep link — file delivery
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
        btn = [[
            InlineKeyboardButton("🚀 Watch And Download ⚡", callback_data=f"stream#{file.file_id}")
        ], [
            InlineKeyboardButton("🙅 Close", callback_data="close_data")
        ]]
        await client.send_cached_media(
            chat_id=message.from_user.id,
            file_id=file.file_id,
            caption=cap,
            reply_markup=InlineKeyboardMarkup(btn)
        )
        return

    # Normal /start UI
    from config import script
    buttons = [
        [InlineKeyboardButton("⚙️ Commands List", callback_data="help")],
        [InlineKeyboardButton("🦹 About Us",       callback_data="about")]
    ]
    await message.reply_photo(
        photo=random.choice(PICS),
        caption=script.START_TXT.format(message.from_user.mention, get_wish()),
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# ==========================================
# 📂 /index_channels  COMMAND
# ==========================================

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


# ==========================================
# 📊 /stats  COMMAND
# ==========================================

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


# ==========================================
# 🗑️ /delete  COMMAND
# ==========================================

@Client.on_message(filters.command('delete') & filters.incoming)
async def delete_file(bot, message):
    if message.from_user.id not in ADMINS:
        return

    try:
        query = message.text.split(" ", 1)[1].strip()
    except IndexError:
        return await message.reply_text("<b>Command Incomplete!\nUsage: <code>/delete keyword</code></b>")

    msg   = await message.reply_text('Searching... ⏱️')
    total, _ = await delete_files(query)

    if int(total) == 0:
        return await msg.edit('No files found in the database with this keyword! ❌')

    btn = [
        [InlineKeyboardButton("✅ Yes, Delete", callback_data=f"delete_{query}")],
        [InlineKeyboardButton("❌ Cancel",      callback_data="close_data")]
    ]
    await msg.edit(
        f"🔍 Found total <b>{total}</b> files for your query: <code>{query}</code>.\n\n"
        f"Are you sure you want to delete them from the database permanently?",
        reply_markup=InlineKeyboardMarkup(btn)
    )


# ==========================================
# 💣 /delete_all  COMMAND
# ==========================================

@Client.on_message(filters.command('delete_all') & filters.incoming)
async def delete_all_index(bot, message):
    if message.from_user.id not in ADMINS:
        return

    files = await Media.count_documents()
    if int(files) == 0:
        return await message.reply_text('Database is already empty! 🗃️')

    btn = [
        [InlineKeyboardButton("⚠️ Yes, Wipe Entire Database", callback_data="delete_all")],
        [InlineKeyboardButton("❌ Cancel",                     callback_data="close_data")]
    ]
    await message.reply_text(
        f'❗ <b>Warning:</b> Total <b>{files}</b> files are saved in the database.\n'
        f'Are you absolutely sure you want to delete the entire database?',
        reply_markup=InlineKeyboardMarkup(btn)
    )


# ==========================================
# ⏱️ /ping  COMMAND
# ==========================================

@Client.on_message(filters.command('ping') & filters.incoming)
async def ping(client, message):
    if message.from_user.id not in ADMINS:
        return

    start_time = time.monotonic()
    msg        = await message.reply("⚡")
    end_time   = time.monotonic()
    await msg.edit(f'<b>⏱️ Response Speed: {round((end_time - start_time) * 1000)} ms</b>')


# ==========================================
# 🆔 /id  COMMAND
# ==========================================

@Client.on_message(filters.command('id') & filters.incoming)
async def showid(client, message):
    if message.from_user.id not in ADMINS:
        return

    if message.reply_to_message:
        reply = message.reply_to_message
        if reply.forward_from_chat:
            return await message.reply_text(
                f"📣 Forwarded Channel/Chat Name: <b>{reply.forward_from_chat.title}</b>\n"
                f"🆔 ID: <code>{reply.forward_from_chat.id}</code>"
            )
        elif reply.from_user:
            return await message.reply_text(
                f"🦹 User: {reply.from_user.mention}\n"
                f"🆔 ID: <code>{reply.from_user.id}</code>"
            )

    await message.reply_text(
        f'<b>🦹 Your Telegram ID: <code>{message.from_user.id}</code>\n'
        f'💬 This Private Chat ID: <code>{message.chat.id}</code></b>'
    )


# ==========================================
# 🔍 PM SEARCH  (was pm_filter.py)
# ==========================================

@Client.on_message(filters.private & filters.text & filters.incoming & ~filters.regex(r"^/"))
async def pm_search(client, message):
    if message.from_user.id not in ADMINS:
        return

    search = message.text.strip()
    files, offset, total_results = await get_search_results(search)

    if not files:
        from config import script
        await message.reply(
            script.NOT_FILE_TXT.format(message.from_user.mention, search),
            quote=True
        )
        return

    req = message.from_user.id
    key = f"{message.chat.id}-{message.id}"
    if len(BUTTONS) > 500:
        BUTTONS.clear()
    BUTTONS[key] = search

    files_link = ""
    for file in files:
        files_link += f"\n\n📁 <a href='https://t.me/{temp.U_NAME}?start=file_{file.file_id}'>[{get_size(file.file_size)}] {file.file_name}</a>"

    btn = []
    if offset != "":
        btn.append([
            InlineKeyboardButton(text=f"🗓 1/{math.ceil(int(total_results) / MAX_BTN)}", callback_data="buttons"),
            InlineKeyboardButton(text="NEXT ⏩", callback_data=f"next_{req}_{key}_{offset}")
        ])
    btn.append([InlineKeyboardButton("🙅 Close", callback_data=f"close#{req}")])

    caption = f"<blockquote>🎬 <b>Total {total_results} Files</b> </blockquote>{files_link}"
    await message.reply(
        text=caption,
        reply_markup=InlineKeyboardMarkup(btn),
        disable_web_page_preview=True,
        parse_mode=enums.ParseMode.HTML,
        quote=True
    )


# ==========================================
# ⏩ NEXT / BACK PAGINATION
# ==========================================

@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):
    ident, req, key, offset = query.data.split("_")
    if int(req) != query.from_user.id:
        return await query.answer("This is not for you! ❌", show_alert=True)

    search = BUTTONS.get(key)
    if not search:
        return await query.answer("Please search again with a new keyword! 🔄", show_alert=True)

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

    btn     = [p_buttons, [InlineKeyboardButton("🙅 Close", callback_data=f"close#{req}")]]
    caption = f"<blockquote>🎬 <b>Total {total} Files found</b> </blockquote>{files_link}"

    await query.message.edit_text(
        text=caption,
        reply_markup=InlineKeyboardMarkup(btn),
        disable_web_page_preview=True,
        parse_mode=enums.ParseMode.HTML
    )


# ==========================================
# 🎛️ ALL CALLBACKS  (was cb_handler)
# ==========================================

@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    data    = query.data
    user_id = query.from_user.id

    # --- Stream / Download links ---
    if data.startswith("stream"):
        file_id = data.split('#', 1)[1]
        await query.answer("Generating streaming links... ⏱️")

        msg      = await client.send_cached_media(chat_id=BIN_CHANNEL, file_id=file_id)
        watch    = f"{URL}watch/{msg.id}"
        download = f"{URL}download/{msg.id}"

        btn = [[
            InlineKeyboardButton("⚡ Watch Online", url=watch),
            InlineKeyboardButton("🚀 Fast Download", url=download)
        ], [
            InlineKeyboardButton("🙅 Close", callback_data="close_data")
        ]]
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(btn))

    # --- Close (generic) ---
    elif data == "close_data":
        await query.message.delete()

    # --- Close (user-specific) ---
    elif data.startswith("close"):
        _, req = data.split("#")
        if int(req) == user_id:
            await query.message.delete()
        else:
            await query.answer("This is not for you! ❌", show_alert=True)

    # --- Page indicator (no-op) ---
    elif data == "buttons":
        await query.answer("⚙️", show_alert=False)
