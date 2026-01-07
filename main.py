#!/usr/bin/env python3
"""
TikTok Downloader Bot - Koyeb Optimized
"""

import os
import sys
import requests
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

print("=" * 60)
print("🤖 TikTok Bot - Koyeb Deployment")
print("=" * 60)

# Import Telegram modules
try:
    from telegram import Update, InputMediaPhoto
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    print("✅ Packages imported")
except ImportError as e:
    print(f"❌ Missing: {e}")
    sys.exit(1)

# ============ CONFIGURATION ============
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not BOT_TOKEN:
    print("❌ ERROR: TELEGRAM_TOKEN not set!")
    print("\nSet in Koyeb Dashboard:")
    print("1. Go to your Service")
    print("2. Click 'Variables' tab")
    print("3. Add: TELEGRAM_TOKEN = your_token")
    sys.exit(1)

PORT = int(os.environ.get("PORT", 8080))

# ============ HEALTH CHECK SERVER ============
print("🚀 Starting health check server...")

from flask import Flask, jsonify
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <html>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
            <h1>🤖 TikTok Downloader Bot</h1>
            <p>Bot is running on Koyeb! 🚀</p>
            <p><a href="/health">Health Check</a></p>
            <p><a href="/status">Status</a></p>
        </body>
    </html>
    """

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "service": "tiktok-bot",
        "timestamp": datetime.now().isoformat(),
        "telegram": "connected"
    })

@app.route('/status')
def status():
    return jsonify({
        "bot": "running",
        "platform": "koyeb",
        "tier": "free",
        "uptime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

def run_flask():
    """Run Flask in separate thread"""
    app.run(host='0.0.0.0', port=PORT, debug=False)

# Start health check
Thread(target=run_flask, daemon=True).start()
print(f"✅ Health check running on port {PORT}")

# ============ TIKTOK FUNCTIONS ============

def download_tiktok(url: str):
    """Download TikTok video or slideshow"""
    try:
        api_url = f"https://www.tikwm.com/api/?url={url}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json"
        }
        
        response = requests.get(api_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("code") == 0 and data.get("data"):
                content = data["data"]
                
                # Slideshow detection
                images = content.get("images")
                if images:
                    if isinstance(images, str):
                        images = [images]
                    
                    return {
                        "success": True,
                        "type": "slideshow",
                        "images": images[:10],  # Telegram limit
                        "title": content.get("title", "TikTok Slideshow")[:100],
                        "author": content.get("author", {}).get("nickname", "")
                    }
                
                # Video detection
                video_url = content.get("hdplay") or content.get("play")
                if video_url:
                    return {
                        "success": True,
                        "type": "video",
                        "video_url": video_url,
                        "title": content.get("title", "TikTok Video")[:100]
                    }
        
        return {"success": False, "error": "API failed"}
    
    except Exception as e:
        logger.error(f"Download error: {e}")
        return {"success": False, "error": str(e)}

# ============ BOT COMMANDS ============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Hello {user.first_name}!\n\n"
        "🎬 *TikTok Downloader Bot*\n\n"
        "📥 Just send me any TikTok URL and I'll download it!\n\n"
        "✅ *Features:*\n"
        "• Videos with sound\n"
        "• Slideshow images\n"
        "• HD quality\n"
        "• 24/7 on Koyeb\n\n"
        "🔗 *Examples:*\n"
        "• https://vm.tiktok.com/abc123/\n"
        "• https://tiktok.com/@user/video/123\n\n"
        "Try it now! 🚀",
        parse_mode='Markdown'
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command"""
    await update.message.reply_text(
        "🆘 *Help*\n\n"
        "Just send a TikTok URL!\n\n"
        "*Commands:*\n"
        "/start - Welcome\n"
        "/help - This message\n"
        "/ping - Check bot\n\n"
        "*Need help?*\n"
        "1. Use public TikTok URLs\n"
        "2. Try different URL if fails\n"
        "3. Some videos are private\n\n"
        "Hosted on Koyeb • Always Free",
        parse_mode='Markdown'
    )

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ping command"""
    await update.message.reply_text(
        f"🏓 Pong!\n\n"
        f"🤖 Bot is online\n"
        f"🕐 {datetime.now().strftime('%H:%M:%S')}\n"
        f"⚡ Powered by Koyeb",
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle TikTok URLs"""
    url = update.message.text.strip()
    
    if "tiktok.com" not in url:
        await update.message.reply_text("❌ Please send a valid TikTok URL")
        return
    
    msg = await update.message.reply_text("⏳ Processing... This may take 20-30 seconds.")
    
    try:
        result = download_tiktok(url)
        
        if not result["success"]:
            await msg.edit_text(f"❌ Failed: {result.get('error', 'Unknown error')}")
            return
        
        # Slideshow
        if result["type"] == "slideshow":
            images = result["images"]
            title = result["title"]
            
            await msg.edit_text(f"📸 Found {len(images)} images. Sending...")
            
            media_group = []
            for i, img in enumerate(images):
                if i == 0:
                    caption = f"🖼️ {title}\n"
                    if result.get("author"):
                        caption += f"👤 By: {result['author']}\n"
                    caption += f"📸 {len(images)} photos\n"
                    caption += "\n📥 TikTok Bot • Koyeb"
                    media_group.append(InputMediaPhoto(media=img, caption=caption[:1024]))
                else:
                    media_group.append(InputMediaPhoto(media=img))
            
            await update.message.reply_media_group(media=media_group)
            await msg.delete()
        
        # Video
        elif result["type"] == "video":
            video_url = result["video_url"]
            title = result["title"]
            
            await msg.edit_text(f"🎬 Downloading video...")
            
            await update.message.reply_video(
                video=video_url,
                caption=f"🎬 {title}\n📥 TikTok Bot • Koyeb",
                supports_streaming=True,
                read_timeout=60,
                write_timeout=60
            )
            await msg.delete()
    
    except Exception as e:
        logger.error(f"Error: {e}")
        await msg.edit_text(f"❌ Error: {str(e)[:100]}")

# ============ MAIN ============

def main():
    """Start the bot"""
    print(f"🔑 Token loaded: {BOT_TOKEN[:10]}...")
    
    try:
        # Create bot
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_cmd))
        application.add_handler(CommandHandler("ping", ping))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Start
        print("=" * 60)
        print("✅ Telegram bot starting...")
        print("=" * 60)
        
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        
    except Exception as e:
        logger.error(f"Bot failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Wait a moment for Flask to start
    import time
    time.sleep(2)
    
    print("🚀 Starting bot components...")
    main()
