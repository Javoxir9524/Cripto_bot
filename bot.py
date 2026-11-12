import asyncio
import os
from aiohttp import web
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# Konfiguratsiya
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
PORT = int(os.environ.get("PORT", 8080))

# 1. Render (Web Service) talabini qondirish uchun yengil veb-server
async def handle(request):
    return web.Response(text="Bot is running and alive!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"Health-check veb-server {PORT}-portda ishga tushdi.")

# 2. Telegram buyruqlari va xabarlari handlerlari
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Bot muvaffaqiyatli ishga tushdi va ishlamoqda!")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Status: Bot faol va Binance bozori nazorat ostida.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.reply_text(f"Xabaringiz qabul qilindi: '{text}'. Bot ishlayapti! 👍")

# 3. Binance bozorini skanerlash va signal yuborish funksiyasi
async def scan_market(application):
    while True:
        print("Bozor skanerlanmoqda...")
        
        # --- BU YERGA BINANCE LOGIKANGIZ YOZILADI ---
        # Masalan, shart bajarilganda CHAT_ID ga xabar yuborish uchun:
        # if CHAT_ID:
        #     await application.bot.send_message(
        #         chat_id=CHAT_ID, 
        #         text="🚨 Diqqat! Shartga mos tanga topildi!"
        #     )
        # ---------------------------------------------
        
        await asyncio.sleep(60)  # Har 1 daqiqada tekshiradi

async def main():
    # Render portini band qilish uchun serverni ishga tushiramiz
    await start_web_server()

    # Telegram botni quramiz
    application = ApplicationBuilder().token(TOKEN).build()

    # Handlerlarni qo'shamiz
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    # Botni ishga tushiramiz
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    # Skanerni orqa fonda ishga tushirib, bot obyektini uzatamiz
    asyncio.create_task(scan_market(application))

    # Dastur to'xtab qolmasligi uchun cheksiz kutish
    stop_event = asyncio.Event()
    await stop_event.wait()

if __name__ == "__main__":
    asyncio.run(main())
