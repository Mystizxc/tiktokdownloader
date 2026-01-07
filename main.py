#!/usr/bin/env python3
"""
TikTok Downloader Bot - Optimized for Koyeb
"""

import os
import sys
import requests
import logging
from datetime import datetime

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

print("=" * 60)
print("🎬 TikTok Downloader Bot - Koyeb Edition")
print("=" * 60)

try:
    from telegram import Update, InputMediaPhoto
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    print("✅ Packages imported!")
except ImportError as e:
    print(f"❌ Missing: {e}")
    sys.exit(1)

# ============ CONFIGURATION ============
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not BOT_TOKEN:
    print("❌ ERROR: TELEGRAM_TOKEN not found!")
    print("\nSet it in Koyeb Dashboard:")
    print("1. Go to your service")
    print("2. Click 'Variables'")
    print("3. Add: TELEGRAM_TOKEN")
    print("4. Value: your_bot_token")
    sys.exit(1)

PORT = int(os.environ.get("PORT", 8080))

# ============ TIKTOK API ============

def get_tiktok_data(url: str):
    """Get TikTok video/slideshow data"""
    try:
        # Use TikWM API
        api_url = f"https://www.tikwm.com/api/?url={url}&hd=1"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }
        
        response = requests.get(api_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("code") == 0 and data.get("data"):
                content = data["data"]
                
                # Check for slideshow
                images = content.get("images")
                if images:
                    if isinstance(images, str):
                        images = [images]
                    
                    return {
                        "success": True,
                        "type": "slideshow",
                        "images": images[:10],  # Max 10 for Telegram
                        "title": content.get("title", "TikTok Slideshow"),
                        "author": content.get("author", {}).get("nickname", "")
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
        
        return {"success": False, "error": "API failed"}
    
    except Exception as e:
        logger.error(f"TikTok API error: {e}")
        return {"success": False, "error": str(e)}

# ============ BOT COMMANDS ============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message"""
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Hello {user.first_name}!\n\n"
        "🎬 *TikTok Downloader Bot*\n\n"
        "📥 Send me any TikTok URL and I'll download it!\n\n"
        "✅ Supports:\n• Videos\n• Slideshows\n• HD Quality\n\n"
        "🔗 Example: https://vm.tiktok.com/abc123/\n\n"
        "Hosted on Koyeb • Always Free 🚀",
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command"""
    await update.message.reply_text(
        "🆘 *Help*\n\n"
        "Just send a TikTok URL!\n\n"
        "*Commands:*\n"
        "/start - Welcome message\n"
        "/help - This message\n"
        "/status - Check bot status\n\n"
        "*Issues?*\n"
        "1. Try different URL\n"
        "2. Check if video is public\n"
        "3. Wait 1 minute",
        parse_mode='Markdown'
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check bot status"""
    uptime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await update.message.reply_text(
        f"🤖 *Bot Status*\n\n"
        f"✅ Online\n"
        f"🕐 Uptime: {uptime}\n"
        f"⚡ Host: Koyeb\n"
        f"🌐 Always Free",
        parse_mode='Markdown'
    )

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle TikTok URLs"""
    url = update.message.text.strip()
    
    # Validate
    if "tiktok.com" not in url:
        await update.message.reply_text("❌ Please send a valid TikTok URL")
        return
    
    # Send processing message
    msg = await update.message.reply_text("⏳ Processing... Please wait up to 30 seconds.")
    
    try:
        # Get TikTok data
        result = get_tiktok_data(url)
        
        if not result["success"]:
            await msg.edit_text(f"❌ Failed: {result.get('error', 'Unknown error')}")
            return
        
        # Handle slideshow
        if result["type"] == "slideshow":
            images = result["images"]
            title = result.get("title", "TikTok Slideshow")[:100]
            
            await msg.edit_text(f"📸 Found {len(images)} images. Sending...")
            
            # Create media group
            media_group = []
            for i, img in enumerate(images[:10]):  # Telegram limit
                if i == 0:
                    caption = f"🖼️ {title}\n"
                    if result.get("author"):
                        caption += f"👤 By: {result['author']}\n"
                    caption += f"📸 {len(images)} photos\n"
                    caption += "\n📥 TikTok Bot • Koyeb"
                    media_group.append(InputMediaPhoto(media=img, caption=caption))
                else:
                    media_group.append(InputMediaPhoto(media=img))
            
            await update.message.reply_media_group(media=media_group)
            await msg.delete()
        
        # Handle video
        elif result["type"] == "video":
            video_url = result["video_url"]
            title = result.get("title", "TikTok Video")[:100]
            
            await msg.edit_text(f"🎬 Downloading video...")
            
            await update.message.reply_video(
                video=video_url,
                caption=f"🎬 {title}\n📥 TikTok Bot • Koyeb",
                supports_streaming=True
            )
            await msg.delete()
    
    except Exception as e:
        logger.error(f"Error: {e}")
        await msg.edit_text(f"❌ Error: {str(e)[:100]}")

# ============ HEALTH CHECK (for Koyeb) ============

from flask import Flask
from threading import Thread
import time

web = Flask(__name__)

@web.route('/')
def home():
    return "🤖 TikTok Bot is running on Koyeb! 🚀"

@web.route('/health')
def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

def run_web():
    web.run(host='0.0.0.0', port=PORT)

# Start Flask in background
Thread(target=run_web, daemon=True).start()
print(f"✅ Health check running on port {PORT}")

# ============ MAIN ============

def main():
    """Start the Telegram bot"""
    print(f"🔑 Token: {BOT_TOKEN[:15]}...")
    
    try:
        # Create application
        app = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("status", status_command))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
        
        # Start
        print("=" * 60)
        print("✅ Bot is RUNNING on Koyeb!")
        print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print("\n📱 Open Telegram and:")
        print("1. Search for your bot")
        print("2. Send /start")
        print("3. Send TikTok URL")
        
        app.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
