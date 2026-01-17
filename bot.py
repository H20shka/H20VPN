import logging
import sqlite3
import time
import requests
import uuid
import json
import asyncio
import random
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# Включить логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен вашего бота (замените на реальный токен из @BotFather)
TOKEN = '8272166182:AAGxnXg-rfFC0s5_fhSCrmISGC6eWDeSrws'

def create_trial_inbound(user_id):
    try:
        base_url = "http://144.31.120.167:54321/dvoykinsecretpanel"
        login_url = f"{base_url}/login"
        login_data = {"username": "H20shka", "password": "aH0908bH?!"}
        session = requests.Session()
        response = session.post(login_url, data=login_data)
        if response.status_code != 200:
            return f"Ошибка входа в панель: {response.status_code} {response.text}"

        client_id = str(uuid.uuid4())
        port = random.randint(10000, 65535)

        settings = {
            "clients": [
                {
                    "id": client_id,
                    "flow": "",
                    "email": f"user{user_id}_{int(time.time())}@gmail.com",
                    "limitIp": 0,
                    "totalGB": 1,
                    "expiryTime": int(time.time() + 259200),
                    "enable": True,
                    "tgId": str(user_id),
                    "subId": ""
                }
            ],
            "decryption": "none",
            "fallbacks": []
        }

        stream_settings = {
            "network": "tcp",
            "security": "reality",
            "realitySettings": {
                "show": False,
                "xver": 0,
                "dest": "yahoo.com:443",
                "serverNames": ["yahoo.com"],
                "privateKey": "",
                "minClient": "",
                "maxClient": "",
                "maxTimediff": 0,
                "shortIds": ["b1"],
                "settings": {
                    "publicKey": "",
                    "fingerprint": "chrome",
                    "serverName": "yahoo.com",
                    "spiderX": "/"
                }
            },
            "tcpSettings": {
                "acceptProxyProtocol": False,
                "header": {
                    "type": "none"
                }
            }
        }

        sniffing = {
            "enabled": True,
            "destOverride": ["http", "tls", "quic"]
        }

        inbound_data = {
            "up": 0,
            "down": 0,
            "total": 1073741824,
            "remark": f"Trial-{user_id}",
            "enable": True,
            "expiryTime": int(time.time() + 259200),
            "listen": "",
            "port": port,
            "protocol": "vless",
            "settings": json.dumps(settings),
            "streamSettings": json.dumps(stream_settings),
            "sniffing": json.dumps(sniffing)
        }

        create_url = f"{base_url}/panel/api/inbounds/add"
        response = session.post(create_url, json=inbound_data)

        if response.status_code == 200:
            try:
                inbound_response = response.json()
                if not isinstance(inbound_response, dict):
                    return f"Ошибка: некорректный ответ от API: {inbound_response}"
            except json.JSONDecodeError:
                return f"Ошибка: ответ не является JSON: {response.text}"
            if inbound_response.get('success') and inbound_response.get('obj'):
                inbound_obj = inbound_response['obj']
                if not inbound_obj or not isinstance(inbound_obj, dict):
                    return "Ошибка: некорректная структура данных inbound в ответе"
                stream_settings = inbound_obj.get('streamSettings', {})
                if not isinstance(stream_settings, dict):
                    return "Ошибка: некорректная структура streamSettings в ответе"
                reality_settings = stream_settings.get('realitySettings', {})
                if not isinstance(reality_settings, dict):
                    return "Ошибка: некорректная структура realitySettings в ответе"
                settings = reality_settings.get('settings', {})
                if not isinstance(settings, dict):
                    return "Ошибка: некорректная структура settings в ответе"
                public_key = settings.get('publicKey', '')
                if not public_key:
                    return "Ошибка: publicKey не найден в ответе создания inbound"

                # Генерация полного Vless URI
                server = "144.31.120.167"
                uri = f"vless://{client_id}@{server}:{port}?type=tcp&security=reality&pbk={public_key}&fp=chrome&sni=yahoo.com&sid=b1&spx=%2F#Trial-{user_id}"

                return f"Пробный период активирован!\n\nВаш Vless ключ:\n{uri}\n\nСервер: {server}"
            else:
                return f"Ошибка создания инбаунда: {inbound_response}"
        else:
            return f"Ошибка создания инбаунда: {response.status_code} {response.text}"
    except Exception as e:
        return f"Ошибка: {str(e)}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение при команде /start."""
    if update.message is None:
        return
    welcome_message = (
        "Привет👋\n\n"
        "Мы работаем и наша команда готова освободить Вас от:\n\n"
        "Зависающих видео в запрещённой сети;\n"
        "Бесконечного просмотра рекламы;\n"
        "Блокировки из-за частой смены IP-адреса;\n"
        "Утечки заряда батареи и ваших данных (как у бесплатных VPN)."
    )
    keyboard = [
        [InlineKeyboardButton("Пробный период⌚️", callback_data="trial")],
        [InlineKeyboardButton("Помощь🆘", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    # Добавить пользователя в базу
    conn = sqlite3.connect('vpn_bot.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (update.message.from_user.id,))
    conn.commit()
    conn.close()

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    if data == "trial":
        # Создать инбаунд
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, create_trial_inbound, user_id)
        await query.edit_message_text(result)
    elif data == "help":
        message = (
            "Возникли вопросы❓❗️\n"
            "Напиши нам и мы поможем со всем✅\n"
            "Пиши: @H20tag"
        )
        keyboard = [[InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    elif data == "back":
        welcome_message = (
            "Привет👋\n\n"
            "Мы работаем и наша команда готова освободить Вас от:\n\n"
            "Зависающих видео в запрещённой сети;\n"
            "Бесконечного просмотра рекламы;\n"
            "Блокировки из-за частой смены IP-адреса;\n"
            "Утечки заряда батареи и ваших данных (как у бесплатных VPN)."
        )
        keyboard = [
            [InlineKeyboardButton("Пробный период⌚️", callback_data="trial")],
            [InlineKeyboardButton("Помощь🆘", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(welcome_message, reply_markup=reply_markup)

def main() -> None:
    """Запуск бота."""
    # Создание таблицы пользователей, если не существует
    conn = sqlite3.connect('vpn_bot.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        trial_used INTEGER DEFAULT 0,
        subscription_expiry INTEGER DEFAULT 0
    )''')
    # Add column if not exists
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN subscription_expiry INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # Column already exists
    conn.commit()
    conn.close()

    application = ApplicationBuilder().token(TOKEN).build()

    # Добавление обработчика команды /start
    application.add_handler(CommandHandler("start", start))

    # Добавление обработчика callback запросов
    application.add_handler(CallbackQueryHandler(handle_callback))

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
