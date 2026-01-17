import logging
import sqlite3
import time
import requests
import uuid
import json
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# Включить логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен вашего бота (замените на реальный токен из @BotFather)
TOKEN = '8272166182:AAGxnXg-rfFC0s5_fhSCrmISGC6eWDeSrws'

def create_trial_inbound(user_id):
    try:
        login_url = "http://144.31.120.167:54321/dvoykinsecretpanel/"
        login_data = {"username": "H20shka", "password": "aH0908bH?!"}
        session = requests.Session()
        response = session.post(login_url, data=login_data)
        if response.status_code != 200:
            return f"Ошибка входа в панель: {response.status_code} {response.text}"
        
        client_id = str(uuid.uuid4())
        
        settings = {
            "clients": [
                {
                    "id": client_id,
                    "flow": "",
                    "email": f"user{user_id}@gmail.com",
                    "limitIp": 0,
                    "totalGB": 1,
                    "expiryTime": int(time.time() + 86400),
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
                    "fingerprint": "random",
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
            "expiryTime": int(time.time() + 86400),
            "listen": "",
            "port": 443,
            "protocol": "vless",
            "settings": json.dumps(settings),
            "streamSettings": json.dumps(stream_settings),
            "sniffing": json.dumps(sniffing)
        }
        
        create_url = "http://144.31.120.167:54321/dvoykinsecretpanel/panel/api/inbounds"
        response = session.post(create_url, data=inbound_data)
        
        if response.status_code == 200:
            # update db
            conn = sqlite3.connect('vpn_bot.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET trial_used = 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
            return f"Пробный период активирован!\n\nВаш Vless ключ: {client_id}\n\nПорт: 443\nТранспорт: TCP\nБезопасность: Reality\nСервер: 144.31.120.167"
        else:
            return f"Ошибка создания инбаунда: {response.text}"
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
