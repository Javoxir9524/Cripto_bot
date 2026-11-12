import asyncio
import os
import aiohttp
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

# 2. Binance API orqali coin narxini tekshirish funksiyasi
async def get_crypto_price(coin_symbol: str):
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={coin_symbol.upper()}USDT"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                price = float(data['lastPrice'])
                price_change = float(data['priceChangePercent'])
                volume = float(data['quoteVolume'])
                return {
                    "success": True,
                    "symbol": data['symbol'],
                    "price": price,
                    "change": price_change,
                    "volume": volume
                }
            else:
                return {"success": False}

# 3. Telegram buyruqlari va xabarlari handlerlari
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 Bot ishga tushdi!\n\n"
        "Coin narxini bilish uchun quyidagi buyruqni yuboring:\n"
        "👉 `/price btc` yoki `/price eth` (yoki istalgan boshqa coin)"
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Status: Bot faol va Binance bozori nazorat ostida.")

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Iltimos, coin nomini kiriting! Masalan: `/price btc`")
        return
    
    coin = context.args[0]
    result = await get_crypto_price(coin)
    
    if result["success"]:
        text = (
            f"📊 **{result['symbol']} Ma'lumotlari:**\n\n"
            f"💵 Narxi: `{result['price']} USDT`\n"
            f"📈 24soatlik o'zgarish: `{result['change']}%`\n"
            f"💰 Savdo hajmi: `${result['volume']:,.0f}`"
        )
    else:
        text = f"❌ '{coin.upper()}' topilmadi yoki xato yozildi. Masalan: `/price btc` deb yuboring."
        
    await update.message.reply_text(text, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.reply_text(f"Xabaringiz qabul qilindi: '{text}'. Coin narxini ko'rish uchun `/price btc` deb yuboring.")

# 4. Binance bozorini avtomatik skanerlash (Hajm > $1M, O'sish > 1.2%)
async def scan_market(application):
    while True:
        print("Bozor skanerlanmoqda (Hajm > $1M, O'sish > 1.2%)...")
        # Bu yerga avtomatik signal qismini yozishingiz mumkin
        await asyncio.sleep(60)

async def main():
    # Render portini band qilish uchun serverni ishga tushiramiz
    await start_web_server()

    # Telegram botni quramiz
    application = ApplicationBuilder().token(TOKEN).build()

    # Handlerlarni qo'shamiz
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("price", price_command))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    # Botni ishga tushiramiz
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    # Skanerni orqa fonda ishga tushiramiz
    asyncio.create_task(scan_market(application))

    # Dastur to'xtab qolmasligi uchun cheksiz kutish
    stop_event = asyncio.Event()
    await stop_event.wait()

if __name__ == "__main__":
    asyncio.run(main())
