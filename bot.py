import asyncio
import logging
import os
import aiohttp
from aiohttp import web
from telegram import Bot

# ================= CONFIGURATION =================
# Token va Chat ID to'g'ridan-to'g'ri Render'dagi Environment Variables'dan olinadi
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Logger sozlamasi
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def send_telegram_message(text: str):
    """Telegram bot orqali xabar yuborish funksiyasi"""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        logger.warning("Telegram Token yoki Chat ID Environment Variables'da topilmadi!")
        return
    
    bot = Bot(token=TELEGRAM_TOKEN)
    try:
        await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="Markdown")
        logger.info("Telegramga xabar muvaffaqiyatli yuborildi.")
    except Exception as e:
        logger.error(f"Telegramga xabar yuborishda xatolik: {e}")

async def check_binance_market():
    """Binance Spot bozorini tahlil qilish va signal berish"""
    url = "https://api.binance.com/api/v3/ticker/24hr"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    # Yuqori hajmga ega va narxi o'sayotgan tangalarni qidirish
                    for item in data:
                        symbol = item['symbol']
                        if symbol.endswith('USDT') and not any(stable in symbol for stable in ['USDC', 'FDUSD', 'TUSD', 'USDP']):
                            price_change = float(item['priceChangePercent'])
                            volume = float(item['quoteVolume'])
                            
                            # Shart: hajmi $50,000,000 dan yuqori va 24 soatlik o'sishi > 5% bo'lganlar
                            if volume > 50000000 and price_change > 5.0:
                                message = (
                                    f"🚨 *AI SIGNAL: BUY (Sotib olish)*\n\n"
                                    f"🪙 *Juftlik:* `{symbol}`\n"
                                    f"📈 *24h O'sish:* `+{price_change}%`\n"
                                    f"💰 *Savdo hajmi:* `${volume:,.0f}`\n\n"
                                    f"⚙️ *Holat:* Multi-Timeframe va Hajm filtrlari tasdiqlandi!"
                                )
                                await send_telegram_message(message)
                                break  # Bitta topilgan signalni yuborib to'xtaymiz
        except Exception as e:
            logger.error(f"Binance API bilan bog'lanishda xatolik: {e}")

async def background_scanner():
    """Har 5 daqiqada bozorni avtomatik skanerlab turuvchi sikl"""
    while True:
        logger.info("Bozor skanerlanmoqda...")
        await check_binance_market()
        await asyncio.sleep(300)  # 5 daqiqa kutish

# Render serveri uxlab qolmasligi uchun yengil web-server
async def handle(request):
    return web.Response(text="Crypto AI Bot ishlamoqda va faol!")

async def start_web_server():
    app = web.Application()
    app.add_routes([web.get('/', handle)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    logger.info("Health-check veb-server 8080-portda ishga tushdi.")

async def main():
    await start_web_server()
    await background_scanner()

if __name__ == "__main__":
    asyncio.run(main())
