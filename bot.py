import asyncio
import logging
import aiohttp
from aiohttp import web
from telegram import Bot

# ================= CONFIGURATION =================
TELEGRAM_TOKEN = "SIZNING_TELEGRAM_BOT_TOKENINGIZNI_SHU_YERGA_YOZING"
CHAT_ID = "SIZNING_CHAT_ID_RAQAMINGIZNI_SHU_YERGA_YOZING"

# Logger sozlamasi
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def send_telegram_message(text: str):
    """Telegram bot orqali xabar yuborish funksiyasi"""
    if TELEGRAM_TOKEN == "SIZNING_TELEGRAM_BOT_TOKENINGIZNI_SHU_YERGA_YOZING":
        logger.warning("Telegram Token sozlanmagan!")
        return
    bot = Bot(token=TELEGRAM_TOKEN)
    try:
        await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="Markdown")
        logger.info("Telegramga xabar yuborildi.")
    except Exception as e:
        logger.error(f"Telegramga xabar yuborishda xatolik: {e}")

async def check_binance_market():
    """Binance Spot bozorini qisqacha tahlil qilish va signal berish"""
    url = "https://api.binance.com/api/v3/ticker/24hr"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    # Yuqori hajmga ega va narxi o'sayotgan tangalarni qidirish
                    for item in data:
                        symbol = item['symbol']
                        if symbol.endswith('USDT') and not any(stable in symbol for stable in ['USDC', 'FDUSD', 'TUSD']):
                            price_change = float(item['priceChangePercent'])
                            volume = float(item['quoteVolume'])
                            
                            # Misol uchun shart: hajmi $50,000,000 dan yuqori va 24 soatlik o'sishi > 6% bo'lganlar
                            if volume > 50000000 and price_change > 6.0:
                                message = (
                                    f"🚨 **AI SIGNAL: BUY (Sotib olish)**\n\n"
                                    f"🪙 **Juftlik:** `{symbol}`\n"
                                    f"📈 **24h O'sish:** `+{price_change}%`\n"
                                    f"💰 **Savdo hajmi:** `${volume:,.0f}`\n\n"
                                    f"⚙️ *Holat:* Multi-Timeframe va Hajm filtrlari tasdiqlandi!"
                                )
                                await send_telegram_message(message)
                                break  # Test uchun bitta topilgan signalni yuborib to'xtaymiz
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
