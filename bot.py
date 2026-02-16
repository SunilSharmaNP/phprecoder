import os
import asyncio
import time
import subprocess
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- Setup ---
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Client("ProStreamer", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Progress Bar Generator (Attractive Design)
def get_progress_bar(current, total):
    percentage = current / total
    done = int(percentage * 10)
    remain = 10 - done
    return f"[{'🔴' * done}{'⚪' * remain}] {int(percentage * 100)}%"

# Uploading progress callback
async def progress_callback(current, total, status_msg, start_time):
    now = time.time()
    diff = now - start_time
    if round(diff % 4) == 0 or current == total: # Har 4 second mein update (Telegram limit se bachne ke liye)
        speed = current / diff if diff > 0 else 0
        percentage = current * 100 / total
        bar = get_progress_bar(current, total)
        
        tmp = (f"📤 **Uploading Video...**\n\n"
               f"{bar}\n"
               f"📁 Size: {round(current / (1024 * 1024), 2)}MB / {round(total / (1024 * 1024), 2)}MB\n"
               f"⚡ Speed: {round(speed / 1024, 2)} KB/s")
        try:
            await status_msg.edit(tmp)
        except:
            pass

@bot.on_message(filters.command("record"))
async def start_recording(client, message):
    input_data = message.text.split(" ")
    if len(input_data) < 3:
        return await message.reply_text("❌ **Format:** `/record [link] [seconds]`")

    target_url = input_data[1]
    duration = int(input_data[2])
    file_path = f"stream_{message.from_user.id}.mp4"
    status = await message.reply_text("🔍 **Initializing Engine...**")

    # Command for Recording
    ffmpeg_cmd = [
        "ffmpeg", "-reconnect", "1", "-reconnect_streamed", "1", "-reconnect_delay_max", "5",
        "-i", target_url, "-t", str(duration), "-c", "copy", "-bsf:a", "aac_adtstoasc",
        file_path, "-y"
    ]

    try:
        # --- Recording Phase ---
        process = await asyncio.create_subprocess_exec(*ffmpeg_cmd)
        
        start_rec = time.time()
        while process.returncode is None:
            elapsed = time.time() - start_rec
            if elapsed >= duration: break
            
            # Live Recording Progress Update
            bar = get_progress_bar(elapsed, duration)
            try:
                await status.edit(f"🔴 **Recording Live Stream...**\n\n{bar}\n⏱ `{int(elapsed)}s` / `{duration}s`")
            except: pass
            
            await asyncio.sleep(4) # Flood waite protection

        await process.wait()
        
        if not os.path.exists(file_path):
            return await status.edit("❌ **Recording failed!** Check URL.")

        # --- Uploading Phase ---
        await status.edit("⚡ **Encoding Finished. Starting Upload...**")
        start_upload = time.time()
        
        await message.reply_video(
            video=file_path,
            caption=f"✅ **Recorded Successfully!**\n⏱ Duration: `{duration}s`",
            progress=progress_callback,
            progress_args=(status, start_upload)
        )
        
        os.remove(file_path)
        await status.delete()

    except Exception as err:
        await status.edit(f"⚠️ **Error:** `{err}`")

bot.run()
