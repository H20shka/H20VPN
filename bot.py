import logging
import sqlite3
import time
import requests
import uuid
import json
import asyncio
import random
import base64
from cryptography.hazmat.primitives.asymmetric import x25519
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

        # Проверить существующие inbound для пользователя
        list_url = f"{base_url}/panel/api/inbounds/list"
        response = session.get(list_url)
        if response.status_code == 200:
            try:
                inbounds_response = response.json()
                if inbounds_response.get('success') and inbounds_response.get('obj'):
                    for inbound in inbounds_response['obj']:
                        if inbound.get('remark') == "H2O":
                            if inbound.get('enable') and inbound.get('expiryTime', 0) > time.time() * 1000:
                                # Найден активный inbound, извлечь ключ
                                settings_str = inbound.get('settings')
                                if settings_str:
                                    try:
                                        settings = json.loads(settings_str)
                                        clients = settings.get('clients', [])
                                        if clients:
                                            client_id = clients[0].get('id')
                                            port = inbound.get('port')
                                            stream_settings_str = inbound.get('streamSettings')
                                            if stream_settings_str:
                                                stream_settings = json.loads(stream_settings_str)
                                                reality_settings = stream_settings.get('realitySettings', {})
                                                inner_settings = reality_settings.get('settings', {})
                                                public_key = inner_settings.get('publicKey')
                                                if client_id and port and public_key:
                                                    server = "144.31.120.167"
                                                uri = f"vless://{client_id}@{server}:{port}?type=tcp&encryption=none&security=reality&pbk={public_key}&fp=chrome&sni=google.com&sid={stream_settings['realitySettings']['shortIds'][0]}&spx=%2F#H2O"
                                                return uri
                                    except json.JSONDecodeError:
                                        pass
                            else:
                                # Найден истекший inbound, извлечь ключ и вернуть сообщение активации
                                settings_str = inbound.get('settings')
                                if settings_str:
                                    try:
                                        settings = json.loads(settings_str)
                                        clients = settings.get('clients', [])
                                        if clients:
                                            client_id = clients[0].get('id')
                                            port = inbound.get('port')
                                            stream_settings_str = inbound.get('streamSettings')
                                            if stream_settings_str:
                                                stream_settings = json.loads(stream_settings_str)
                                                reality_settings = stream_settings.get('realitySettings', {})
                                                inner_settings = reality_settings.get('settings', {})
                                                public_key = inner_settings.get('publicKey')
                                                if client_id and port and public_key:
                                                    server = "144.31.120.167"
                                                    uri = f"vless://{client_id}@{server}:{port}?type=tcp&encryption=none&security=reality&pbk={public_key}&fp=chrome&sni=google.com&sid={stream_settings['realitySettings']['shortIds'][0]}&spx=%2F#H2O"
                                                    return uri
                                    except json.JSONDecodeError:
                                        pass
            except json.JSONDecodeError:
                pass

        # Если не найден активный, создать новый
        client_id = str(uuid.uuid4())
        port = random.randint(10000, 25000)

        # Генерация ключей X25519 для Reality
        private_key = x25519.X25519PrivateKey.generate()
        public_key_b64 = base64.urlsafe_b64encode(private_key.public_key().public_bytes_raw()).decode().rstrip('=')
        private_key_b64 = base64.urlsafe_b64encode(private_key.private_bytes_raw()).decode().rstrip('=')

        settings = {
            "clients": [
                {
                    "id": client_id,
                    "flow": "xtls-rprx-vision",
                    "email": f"user{user_id}_{int(time.time())}@gmail.com",
                    "limitIp": 0,
                    "totalGB": 0,
                    "expiryTime": int((time.time() + 259200) * 1000),
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
                "dest": "google.com:443",
                "serverNames": ["google.com", "www.google.com"],
                "privateKey": private_key_b64,
                "minClient": "25.9.11",
                "maxClient": "25.9.11",
                "maxTimediff": 0,
                "shortIds": [f"{random.randint(0, 0xFFFFFFFF):08x}"],
                "settings": {
                    "publicKey": public_key_b64,
                    "fingerprint": "chrome",
                    "serverName": "google.com",
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
            "total": 0,
            "remark": "H2O",
            "enable": True,
            "expiryTime": int((time.time() + 259200) * 1000),
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
                # Генерация полного Vless URI с заранее сгенерированными ключами
                server = "144.31.120.167"
                uri = f"vless://{client_id}@{server}:{port}?type=tcp&encryption=none&security=reality&pbk={public_key_b64}&fp=chrome&sni=google.com&sid={stream_settings['realitySettings']['shortIds'][0]}&spx=%2F#H2O"

                return uri
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
        if result.startswith("vless://"):
            message = f"Ключ выдается едино-разово на 3 дня.\nКлюч: {result}\n⬇️Выберите устройство ниже:⬇️"
            keyboard = [
                [InlineKeyboardButton("iOs", callback_data="ios"), InlineKeyboardButton("Android", callback_data="android")],
                [InlineKeyboardButton("MacOs", callback_data="macos"), InlineKeyboardButton("Windows", callback_data="windows")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup)
        else:
            await query.edit_message_text(result)
    elif data == "ios":
        message = (
            "Скачать приложение:\n"
            "Для пользователей с iOs 16 и выше: https://apps.apple.com/ru/app/v2raytun/id6476628951\n"
            "Для пользователей с iOs до 16: https://apps.apple.com/ru/app/v2box-v2ray-client/id6446814690\n"
            "Для активации зайдите в приложение и скопировав ключ, нажмите добавить из буфера обмена"
        )
        keyboard = [[InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    elif data == "android":
        message = (
            "Скачать приложение: https://play.google.com/store/apps/details?id=com.v2raytun.android&pcampaignid=web_share\n"
            "Для активации зайдите в приложение и скопировав ключ, нажмите добавить из буфера обмена"
        )
        keyboard = [[InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    elif data == "macos":
        message = (
            "Скачать приложение: https://apps.apple.com/us/app/v2raytun/id6476628951?platform=mac\n"
            "Для активации зайдите в приложение и скопировав ключ, нажмите добавить из буфера обмена"
        )
        keyboard = [[InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    elif data == "windows":
        message = (
            "Скачать приложение: https://github.com/hiddify/hiddify-app/releases/latest/download/Hiddify-Windows-Setup-x64.Msix\n"
            "Для активации зайдите в приложение и скопировав ключ, нажмите добавить из буфера обмена"
        )
        keyboard = [[InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
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
