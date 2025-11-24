import datetime
import logging
import os
import uvicorn

from dotenv import load_dotenv

from fastapi import FastAPI, Request
from contextlib import asynccontextmanager

from telegram import Bot, Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ENV = os.getenv("ENVIRONMENT")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

class AutomacaoProwayBot(Bot):
    def __init__(self):
        return super().__init__(TELEGRAM_TOKEN)

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_name = update.message.from_user.first_name

    timestamp = datetime.datetime.now(datetime.UTC).strftime(
        "%H:%M:%S de %d/%m/%Y"
    )

    logger.info("Mensagem de texto recebida.")

    await update.message.reply_text(f"Olá {user_name}. Você digitou '{user_text}'. Agora são {timestamp}.")

bot_app = ApplicationBuilder().bot(AutomacaoProwayBot()).build()
bot_app.add_handler(MessageHandler(filters.TEXT, echo))

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    if ENV.lower() == "production":
        logger.info("Iniciando bot em modo WEBHOOK...")
        await bot_app.initialize()
        await bot_app.start()

        logger.info("Registrando o webhook no telegram...")
        await bot_app.bot.set_webhook(WEBHOOK_URL)

    yield

    if ENV.lower() == "production":
        logger.info("Encerrando a aplicação...")
        await bot_app.stop()
        await bot_app.shutdown()

api_app = FastAPI(lifespan=lifespan)

if __name__ == "__main__":

    if ENV.lower() == "production":

        @api_app.post("/webhook")
        async def webhook(request: Request):
            data = await request.json()
            update = Update.de_json(data, bot_app.bot)

            await bot_app.process_update(update)

            return {"status": "OK"}
        
        uvicorn.run(api_app, host="0.0.0.0", port=8000)

    else:
        logger.info("Iniciando bot em modo POLLING...")
        bot_app.run_polling()