import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler

BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")

async def start(update: Update, context):
    await update.message.reply_text("✅ Bot working!")

async def main():
    # Create bot
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    
    # Clear any existing connection
    await app.bot.delete_webhook(drop_pending_updates=True)
    
    # Start polling
    print("🚀 Starting bot...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    
    # Keep running
    print("✅ Bot running!")
    await asyncio.Event().wait()

# Run with conflict handling
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("\n🛑 Bot stopped")
except Exception as e:
    print(f"❌ Error: {e}")
