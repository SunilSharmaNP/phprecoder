import os
import asyncio
import time
from pyrogram import Client, filters

# --- Setup ---
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# 👉 Yahan owner/admin ID daalo
OWNER_IDS = [8347137417, 2032446867]  # apni Telegram IDs

bot = Client("ProStreamer", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


def get_progress_bar(current, total):
    percentage = current / total
    done = int(percentage * 10)
    remain = 10 - done
    return f"[{'🔴' * done}{'⚪' * remain}] {int(percentage * 100)}%"


async def progress_callback(current, total, status_msg, start_time):
    now = time.time()
    diff = now - start_time
    if round(diff % 4) == 0 or current == total:
        speed = current / diff if diff > 0 else 0
        bar = get_progress_bar(current, total)

        try:
            await status_msg.edit(
                f"📤 Uploading...\n\n{bar}\n"
                f"{round(current/1048576,2)}MB / {round(total/1048576,2)}MB\n"
                f"⚡ {round(speed/1024,2)} KB/s"
            )
        except:
            pass


@bot.on_message(filters.command("record"))
async def start_recording(client, message):

    # ✅ OWNER CHECK
    if message.from_user.id not in OWNER_IDS:
        return await message.reply_text("❌ Only bot owner/admin can use this command.")

    input_data = message.text.split(" ")
    if len(input_data) < 3:
        return await message.reply_text("Format:\n`/record link seconds`")

    target_url = input_data[1]
    duration = int(input_data[2])
    file_path = f"stream_{message.from_user.id}.mp4"
    status = await message.reply_text("Initializing...")

    ffmpeg_cmd = [
        "ffmpeg", "-reconnect", "1",
        "-reconnect_streamed", "1",
        "-reconnect_delay_max", "5",
        "-i", target_url,
        "-t", str(duration),
        "-c", "copy",
        "-bsf:a", "aac_adtstoasc",
        file_path, "-y"
    ]

    try:
        process = await asyncio.create_subprocess_exec(*ffmpeg_cmd)

        start_rec = time.time()
        while process.returncode is None:
            elapsed = time.time() - start_rec
            if elapsed >= duration:
                break

            bar = get_progress_bar(elapsed, duration)
            try:
                await status.edit(
                    f"🔴 Recording...\n\n{bar}\n"
                    f"{int(elapsed)}s / {duration}s"
                )
            except:
                pass

            await asyncio.sleep(4)

        await process.wait()

        if not os.path.exists(file_path):
            return await status.edit("Recording failed!")

        await status.edit("Uploading...")

        start_upload = time.time()
        await message.reply_video(
            video=file_path,
            caption=f"Recorded {duration}s",
            progress=progress_callback,
            progress_args=(status, start_upload)
        )

        os.remove(file_path)
        await status.delete()

    except Exception as err:
        await status.edit(f"Error: {err}")


bot.run()
