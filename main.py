#!/usr/bin/env python3
"""
TikTok Downloader Bot - Working Slideshow Support
"""

import os
import sys
import requests
import re
from datetime import datetime

print("=" * 60)
print("🎬 TikTok Downloader Bot with Slideshow Support")
print("=" * 60)

try:
    from telegram import Update, InputMediaPhoto
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    print("✅ Packages imported successfully!")
except ImportError as e:
    print(f"❌ Missing package: {e}")
    print("Run: pip install python-telegram-bot requests")
    sys.exit(1)

# ============ CONFIGURATION ============
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not BOT_TOKEN:
    print("❌ ERROR: TELEGRAM_TOKEN not found!")
    print("\nHow to fix:")
    print("1. Get token from @BotFather")
    print("2. In Replit, click 🔒 Lock icon")
    print("3. Add: TELEGRAM_TOKEN = your_token")
    sys.exit(1)

# ============ TIKTOK API FUNCTIONS ============


def extract_photo_id(url: str) -> str:
    """Extract photo ID from TikTok URL"""
    patterns = [
        r'/photo/(\d+)', r'/video/(\d+)', r'@[^/]+/(?:photo|video)/(\d+)'
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    # If no pattern matches, try to extract any numeric ID
    numbers = re.findall(r'\d+', url)
    if numbers:
        # Take the longest number (most likely the ID)
        return max(numbers, key=len)

    return ""


def get_tiktok_content(url: str):
    """Get TikTok content using multiple API endpoints"""

    # Try different API endpoints
    api_endpoints = [
        # Primary API for slideshows
        {
            "name": "TikWM Slideshow",
            "url": f"https://www.tikwm.com/api/?url={url}",
            "parse_func": parse_tikwm_response
        },
        # Alternative API
        {
            "name": "TikTok Download API",
            "url": f"https://api.tiklydown.eu.org/api/download?url={url}",
            "parse_func": parse_tiklydown_response
        },
        # Another backup API
        {
            "name": "TikMate",
            "url": f"https://tikmate.online/api/ajaxSearch?url={url}",
            "parse_func": parse_tikmate_response
        }
    ]

    headers = {
        "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": "https://www.tiktok.com/"
    }

    for api in api_endpoints:
        try:
            print(f"🔧 Trying {api['name']}...")
            response = requests.get(api["url"], headers=headers, timeout=15)

            if response.status_code == 200:
                try:
                    data = response.json()
                    result = api["parse_func"](data)
                    if result:
                        print(f"✅ Success from {api['name']}")
                        return result
                except Exception as e:
                    print(f"❌ Parse error from {api['name']}: {e}")
                    continue
        except Exception as e:
            print(f"❌ API {api['name']} failed: {e}")
            continue

    return {"success": False, "error": "All APIs failed"}


def parse_tikwm_response(data: dict):
    """Parse TikWM API response"""
    if isinstance(data, dict) and data.get("code") == 0 and data.get("data"):
        content = data["data"]

        # Check for slideshow
        images = content.get("images")
        if images:
            if isinstance(images, str):
                images = [images]
            elif isinstance(images, list):
                pass
            else:
                return None

            return {
                "success": True,
                "type": "slideshow",
                "images": images,
                "title": content.get("title", "TikTok Slideshow"),
                "author": content.get("author", {}).get("nickname", "Unknown")
            }

        # Check for video
        video_url = content.get("hdplay") or content.get("play")
        if video_url:
            return {
                "success": True,
                "type": "video",
                "video_url": video_url,
                "title": content.get("title", "TikTok Video")
            }

    return None


def parse_tiklydown_response(data: dict):
    """Parse Tiklydown API response"""
    if not isinstance(data, dict):
        return None

    # Check for slideshow
    if data.get("type") == "image":
        images = data.get("imageUrls", [])
        if isinstance(images, str):
            images = [images]

        if images:
            return {
                "success": True,
                "type": "slideshow",
                "images": images,
                "title": data.get("desc", "TikTok Slideshow")
            }

    # Check for video
    video_url = data.get("videoUrl")
    if video_url:
        return {
            "success": True,
            "type": "video",
            "video_url": video_url,
            "title": data.get("desc", "TikTok Video")
        }

    return None


def parse_tikmate_response(data: dict):
    """Parse TikMate API response"""
    if not isinstance(data, dict):
        return None

    # TikMate returns different structure
    if data.get("success"):
        content = data.get("data", {})

        # Check for slideshow
        images = content.get("images", [])
        if images:
            if isinstance(images, str):
                images = [images]

            return {
                "success": True,
                "type": "slideshow",
                "images": images,
                "title": content.get("desc", "TikTok Slideshow")
            }

        # Check for video
        video_url = content.get("play")
        if video_url:
            return {
                "success": True,
                "type": "video",
                "video_url": video_url,
                "title": content.get("desc", "TikTok Video")
            }

    return None


# ============ BOT FUNCTIONS ============


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message"""
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Hello {user.first_name}!\n\n"
        "🎬 *TikTok Downloader Bot*\n\n"
        "📥 *I can download:*\n"
        "• Videos (with sound)\n"
        "• Slideshows (multiple photos)\n\n"
        "📤 *How to use:*\n"
        "Just send me any TikTok URL!\n\n"
        "*Examples:*\n"
        "• https://vm.tiktok.com/abc123/\n"
        "• https://www.tiktok.com/@user/photo/123456\n\n"
        "Try it now! Send me a TikTok link. 🚀",
        parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message"""
    await update.message.reply_text(
        "🆘 *Help Center*\n\n"
        "Send any TikTok URL and I'll download it for you!\n\n"
        "*For slideshows:*\n"
        "I'll send all photos as an album.\n\n"
        "*For videos:*\n"
        "I'll send the video with sound.\n\n"
        "*Having issues?*\n"
        "• Try a different TikTok URL\n"
        "• Make sure the content is public\n"
        "• Wait a minute and try again",
        parse_mode='Markdown')


async def handle_tiktok_url(update: Update,
                            context: ContextTypes.DEFAULT_TYPE):
    """Handle TikTok URLs"""
    url = update.message.text.strip()
    user = update.effective_user

    print(f"📥 URL received from {user.username or user.id}: {url[:50]}...")

    # Validate URL
    if not any(domain in url for domain in ["tiktok.com", "douyin.com"]):
        await update.message.reply_text(
            "❌ Please send a valid TikTok URL\n\n"
            "Example: https://vm.tiktok.com/abc123/")
        return

    # Show processing message
    msg = await update.message.reply_text(
        "🔍 *Processing your request...*\n"
        "⏳ This may take 10-20 seconds",
        parse_mode='Markdown')

    try:
        # Get content from TikTok APIs
        result = get_tiktok_content(url)

        if not result["success"]:
            await msg.edit_text(
                f"❌ *Download Failed*\n\n"
                f"Error: {result.get('error', 'Unknown error')}\n\n"
                f"*Try:*\n"
                f"• Check if the content is public\n"
                f"• Try a different TikTok URL\n"
                f"• The API might be temporarily down",
                parse_mode='Markdown')
            return

        # Handle SLIDESHOW
        if result["type"] == "slideshow":
            images = result["images"]
            title = result.get("title", "TikTok Slideshow")[:100]

            print(f"📸 Found {len(images)} images for slideshow")

            # Ensure images is a list
            if isinstance(images, str):
                images = [images]

            if not images:
                await msg.edit_text("❌ No images found in slideshow")
                return

            # Limit to 10 images (Telegram limit)
            images = images[:10]

            await msg.edit_text(
                f"🖼️ *Slideshow Detected!*\n\n"
                f"📸 *Info:*\n"
                f"• Images: {len(images)} photos\n"
                f"• Title: {title}\n\n"
                f"⏬ *Downloading images...*",
                parse_mode='Markdown')

            try:
                # Create media group
                media_group = []

                for i, image_url in enumerate(images):
                    # Clean URL - remove any tracking parameters
                    clean_url = image_url.split(
                        '?')[0] if '?' in image_url else image_url

                    # First image gets caption
                    if i == 0:
                        caption = f"🖼️ {title}\n"
                        if result.get("author"):
                            caption += f"👤 By: {result['author']}\n"
                        caption += f"📸 {len(images)} photos\n"
                        caption += "\n📥 Downloaded via TikTok Bot"

                        media_group.append(
                            InputMediaPhoto(media=clean_url,
                                            caption=caption[:1024]))
                    else:
                        media_group.append(InputMediaPhoto(media=clean_url))

                # Send the album
                await update.message.reply_media_group(media=media_group)
                await msg.delete()

            except Exception as e:
                print(f"Error sending album: {e}")

                # Fallback: send images one by one
                await msg.edit_text(f"📸 *Sending images individually...*\n"
                                    f"{len(images)} photos")

                sent_count = 0
                for i, image_url in enumerate(images[:5]):  # Limit to 5
                    try:
                        if i == 0:
                            await update.message.reply_photo(
                                photo=image_url,
                                caption=
                                f"🖼️ {title} (1/{min(len(images), 5)})\n📥 TikTok Bot"
                            )
                        else:
                            await update.message.reply_photo(
                                photo=image_url,
                                caption=f"🖼️ ({i+1}/{min(len(images), 5)})")
                        sent_count += 1
                    except:
                        continue

                if sent_count > 0:
                    await msg.edit_text(f"✅ Sent {sent_count} images!")
                else:
                    await msg.edit_text("❌ Could not send any images")

        # Handle VIDEO
        elif result["type"] == "video":
            video_url = result["video_url"]
            title = result.get("title", "TikTok Video")[:100]

            await msg.edit_text(
                f"🎬 *Video Detected!*\n\n"
                f"📹 *Title:* {title}\n\n"
                f"⏬ *Downloading video...*",
                parse_mode='Markdown')

            try:
                await update.message.reply_video(
                    video=video_url,
                    caption=f"🎬 {title}\n📥 Downloaded via TikTok Bot",
                    supports_streaming=True,
                    read_timeout=60,
                    write_timeout=60)
                await msg.delete()

            except Exception as e:
                print(f"Error sending video: {e}")
                await msg.edit_text(
                    f"✅ *Video Downloaded!*\n\n"
                    f"📹 *Title:* {title}\n"
                    f"🔗 *Direct Link:* {video_url[:50]}...\n\n"
                    f"⚠️ Could not send via Telegram\n"
                    f"Copy the link above to download",
                    parse_mode='Markdown')

    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()

        await msg.edit_text(
            f"❌ *Unexpected Error*\n\n"
            f"`{str(e)[:100]}`\n\n"
            f"Please try again or use /help",
            parse_mode='Markdown')


# ============ KEEP ALIVE ============
print("🔄 Setting up keep-alive...")

try:
    from keep_alive import keep_alive
    keep_alive()
except:
    # Create keep_alive.py
    with open("keep_alive.py", "w") as f:
        f.write('''from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "TikTok Bot is running!"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
''')

    from keep_alive import keep_alive
    keep_alive()

print("✅ Keep-alive started!")

# ============ MAIN FUNCTION ============


def main():
    """Start the bot"""
    print(f"\n🤖 Bot Token: {BOT_TOKEN[:15]}...")

    try:
        app = Application.builder().token(BOT_TOKEN).build()

        # Add handlers
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tiktok_url))

        print("=" * 60)
        print("✅ Bot is RUNNING!")
        print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print("\n📱 Send /start to begin")

        app.run_polling(drop_pending_updates=True)

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")


if __name__ == "__main__":
    main()
