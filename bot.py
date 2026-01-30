import logging
import sqlite3
import time
import requests
import uuid
import json
import asyncio
import nest_asyncio
import random
import base64
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from telegram.error import BadRequest
import requests
from flask import Flask, request
import threading

nest_asyncio.apply()

# Flask app for webhook
app = Flask(__name__)

@app.route('/xrocket_webhook', methods=['POST'])
def xrocket_webhook():
    data = request.get_json()
    logger.info(f"Webhook received: {data}")
    payment_id = data.get('payment_id')
    status = data.get('status')
    if status == 'paid':
        conn = sqlite3.connect('vpn_bot.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE payments SET status = 'paid' WHERE payment_id = ?", (payment_id,))
        conn.commit()
        conn.close()
        logger.info(f"Payment {payment_id} marked as paid")
    return 'OK', 200

# Включить логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен вашего бота (замените на реальный токен из @BotFather)
TOKEN = '8272166182:AAGxnXg-rfFC0s5_fhSCrmISGC6eWDeSrws'

# ID канала для проверки подписки
CHANNEL_ID = '@H20_shop1'

# Список админов (добавьте свои user_id)
ADMINS = [863968972, 551107612]

# XRocket API Token
XROCKET_TOKEN = '990b34706f156a52746adbb7a'

# XRocket API Token
XROCKET_TOKEN = '990b34706f156a52746adbb7a'

def create_xrocket_payment(amount, currency='RUB', description='VPN subscription'):
    try:
        url = 'https://api.xrocket.tg/payments'
        headers = {
            'Authorization': f'Bearer {XROCKET_TOKEN}',
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Referer': 'https://xrocket.tg/'
        }
        data = {
            'amount': amount,
            'currency': currency,
            'description': description
        }
        response = requests.post(url, json=data, headers=headers, timeout=10)
        logger.info(f"XRocket create payment response: {response.status_code} {response.text}")
        if response.status_code == 200:
            result = response.json()
            return result.get('payment_id'), result.get('payment_url')
        return None, None
    except Exception as e:
        logger.error(f"Error creating XRocket payment: {e}")
        return None, None

def get_xrocket_payment_status(payment_id):
    try:
        url = f'https://api.xrocket.tg/payments/{payment_id}'
        headers = {
            'Authorization': f'Bearer {XROCKET_TOKEN}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Referer': 'https://xrocket.tg/'
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            result = response.json()
            return result.get('status', 'unknown')
        return 'unknown'
    except Exception as e:
        logger.error(f"Error getting XRocket payment status: {e}")
        return 'unknown'

def create_trial_client(user_id):
    try:
        base_url = "http://144.31.120.167:54321/dvoykinsecretpanel"
        login_url = f"{base_url}/login"
        login_data = {"username": "H20shka", "password": "aH0908bH?!"}
        session = requests.Session()
        response = session.post(login_url, data=login_data)
        if response.status_code != 200:
            return f"Ошибка авторизации: {response.status_code}"

        # Получить шаблон inbound
        template_inbound_id = 1203
        get_inbound_url = f"{base_url}/panel/api/inbounds/get/{template_inbound_id}"
        response = session.get(get_inbound_url)
        if response.status_code != 200:
            return f"Ошибка получения inbound: {response.status_code}"

        try:
            inbound_response = response.json()
            if not inbound_response.get('success'):
                return "Inbound id=1203 не найден"
            template_inbound = inbound_response['obj']
        except json.JSONDecodeError:
            return f"Ошибка: ответ не является JSON: {response.text}"

        # Создать нового клиента
        client_id = str(uuid.uuid4())
        client = {
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

        # Создать новый inbound
        port = random.randint(10000, 20000)

        # Использовать предоставленные ключи
        private_key_b64 = "aB5BtDQgMyKc-R7wew7L6aHD3MxQO59X0gWJDbDC60I"
        public_key_b64 = "WkV5D_PHJ-wMZL3pV24EA2uZZDj35Knkaaj8Odtyh2U"

        stream_settings = {
            "network": "tcp",
            "security": "reality",
            "realitySettings": {
                "show": False,
                "xver": 0,
                "dest": "google.com:443",
                "serverNames": ["google.com"],
                "privateKey": private_key_b64,
                "publicKey": public_key_b64,
                "shortIds": [""],
                "spiderX": "/"
            },
            "tcpSettings": {
                "acceptProxyProtocol": False,
                "header": {
                    "type": "none"
                }
            }
        }
        new_inbound = {
            "up": 0,
            "down": 0,
            "total": 0,
            "remark": f"Trial {user_id}",
            "enable": True,
            "expiryTime": 0,
            "listen": "",
            "port": port,
            "protocol": "vless",
            "settings": json.dumps({"clients": [client], "decryption": "none", "fallbacks": []}),
            "streamSettings": json.dumps(stream_settings),
            "sniffing": json.dumps({"enabled": True, "destOverride": ["http", "tls", "quic"]})
        }

        add_inbound_url = f"{base_url}/panel/api/inbounds/add"
        response = session.post(add_inbound_url, json=new_inbound)
        if response.status_code == 200:
            try:
                add_response = response.json()
                if add_response.get('success'):
                    # Использовать сгенерированные ключи для URI
                    server = "144.31.120.167"
                    uri = f"vless://{client_id}@{server}:{port}?type=tcp&encryption=none&security=reality&pbk={public_key_b64}&fp=chrome&sni=google.com&sid=&spx=%2F#H2O"
                    return uri
                else:
                    return f"Ошибка создания inbound: {add_response}"
            except json.JSONDecodeError:
                return f"Ошибка: ответ не является JSON: {response.text}"
        else:
            return f"Ошибка создания inbound: {response.status_code} {response.text}"
    except Exception as e:
        return f"Ошибка: {str(e)}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение при команде /start."""
    if update.message is None:
        return

    user_id = update.message.from_user.id

    # Проверить блокировку
    conn = sqlite3.connect('vpn_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT banned FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row and row[0] == 1:
        await update.message.reply_text("Вы заблокированы.")
        return

    await update.message.reply_text("Привет👋")

    info_message = (
        "🔋Мы работаем и наша команда готова освободить Вас от:\n\n"
        "⌛️Зависающих видео в запрещённой сети;\n"
        "📲Бесконечного просмотра рекламы;\n"
        "❌Блокировки из-за частой смены IP-адреса;\n"
        "🪫Утечки заряда батареи и ваших данных (как у бесплатных VPN)."
    )
    await update.message.reply_text(info_message)

    # Проверить подписку на канал
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status not in ['member', 'administrator', 'creator']:
            keyboard = [
                [InlineKeyboardButton("Подписаться✅", url="https://t.me/H20_shop1")],
                [InlineKeyboardButton("Проверить подписку", callback_data="check_sub")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Для использования бота подпишитесь на наш канал.", reply_markup=reply_markup)
            return
    except BadRequest:
        await update.message.reply_text("Не удалось проверить подписку на канал.")
        return

    keyboard = [
        [InlineKeyboardButton("Пробный период⌚️", callback_data="trial")],
        [InlineKeyboardButton("Купить VPN💎", callback_data="buy_vpn")],
        [InlineKeyboardButton("О сервисе📊", callback_data="about")],
        [InlineKeyboardButton("Помощь🆘", callback_data="help")]
    ]
    if user_id in ADMINS:
        keyboard.insert(0, [InlineKeyboardButton("Админка", callback_data="admin")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("⬇️Выберите опцию из доступных ниже:⬇️", reply_markup=reply_markup)
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
        # Проверить статус пробного периода
        conn = sqlite3.connect('vpn_bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT trial_used, subscription_expiry, trial_key FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        current_time = time.time()
        if row:
            trial_used, subscription_expiry, trial_key = row
            if trial_used == 0:
                # Не активирован, предложить активировать
                keyboard = [
                    [InlineKeyboardButton("Активировать пробный период⌚️", callback_data="activate_trial")],
                    [InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text("Пробный период не активирован. Хотите активировать?", reply_markup=reply_markup)
            else:
                # Использован, показать ключ и кнопки
                status = "активен" if subscription_expiry > current_time else "истек"
                if trial_key:
                    message = f"Ваш пробный период {status}.\n🔴Ключ: {trial_key}\n⬇️Выберите устройство ниже:⬇️"
                    keyboard = [
                        [InlineKeyboardButton("Скопировать ключ", callback_data="copy_key")],
                        [InlineKeyboardButton("iOs📱", callback_data="ios"), InlineKeyboardButton("Android📱", callback_data="android")],
                        [InlineKeyboardButton("MacOs💻", callback_data="macos"), InlineKeyboardButton("Windows🖥", callback_data="windows")],
                        [InlineKeyboardButton("Linux💻", callback_data="linux")],
                        [InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]
                    ]
                else:
                    message = f"Ваш пробный период {status}, но ключ недоступен.\n⬇️Выберите устройство ниже:⬇️"
                    keyboard = [
                        [InlineKeyboardButton("iOs📱", callback_data="ios"), InlineKeyboardButton("Android📱", callback_data="android")],
                        [InlineKeyboardButton("MacOs💻", callback_data="macos"), InlineKeyboardButton("Windows🖥", callback_data="windows")],
                        [InlineKeyboardButton("Linux💻", callback_data="linux")],
                        [InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]
                    ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(message, reply_markup=reply_markup)
        else:
            # Пользователь не найден, но это маловероятно
            await query.edit_message_text("Ошибка: пользователь не найден.")
    elif data == "activate_trial":
        # Активировать пробный период
        conn = sqlite3.connect('vpn_bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT trial_used FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row and row[0] == 1:
            await query.edit_message_text("Вы уже использовали пробный период.")
            conn.close()
            return
        # Создать клиента
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, create_trial_client, user_id)
        if result.startswith("vless://"):
            # Обновить базу данных
            expiry_time = int(time.time() + 259200)
            cursor.execute("UPDATE users SET trial_used = 1, subscription_expiry = ?, trial_notification_sent = 0, trial_key = ? WHERE user_id = ?", (expiry_time, result, user_id))
            conn.commit()
            conn.close()
            message = f"🟢Ключ выдается едино-разово на 3 дня🟢\n🔴Ключ: {result}\n⬇️Выберите устройство ниже:⬇️"
            keyboard = [
                [InlineKeyboardButton("Скопировать ключ", callback_data="copy_key")],
                [InlineKeyboardButton("iOs📱", callback_data="ios"), InlineKeyboardButton("Android📱", callback_data="android")],
                [InlineKeyboardButton("MacOs💻", callback_data="macos"), InlineKeyboardButton("Windows🖥", callback_data="windows")],
                [InlineKeyboardButton("Linux💻", callback_data="linux")],
                [InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup)
        else:
            conn.close()
            await query.edit_message_text(result)
    elif data == "ios":
        message = "Скачать приложение можно выбрав снизу подходящию версию iOs и нажав на нужную кнопку⬇️\nДля активации зайдите в приложение и скопировав ключ, нажмите добавить из буфера обмена."
        keyboard = [
            [InlineKeyboardButton("Для пользователей с iOs 16 и выше🟡", url="https://apps.apple.com/ru/app/v2raytun/id6476628951")],
            [InlineKeyboardButton("Для пользователей с iOs до 16🟢", url="https://apps.apple.com/ru/app/v2box-v2ray-client/id6446814690")],
            [InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    elif data == "android":
        message = "Скачать приложение можно ниже по нажатию на кнопку⬇️\nДля активации зайдите в приложение и скопировав ключ, нажмите добавить из буфера обмена"
        keyboard = [
            [InlineKeyboardButton("Скачать для Android🟠", url="https://play.google.com/store/apps/details?id=com.v2raytun.android&pcampaignid=web_share")],
            [InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    elif data == "macos":
        message = "Скачать приложение можно ниже по нажатию на кнопку⬇️\nДля активации зайдите в приложение и скопировав ключ, нажмите добавить из буфера обмена"
        keyboard = [
            [InlineKeyboardButton("Скачать для MacOs💻", url="https://apps.apple.com/us/app/v2raytun/id6476628951?platform=mac")],
            [InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    elif data == "windows":
        message = "Скачать приложение можно ниже по нажатию на кнопку⬇️\nДля активации зайдите в приложение и скопировав ключ, нажмите добавить из буфера обмена"
        keyboard = [
            [InlineKeyboardButton("Скачать для Windows🖥", url="https://github.com/hiddify/hiddify-app/releases/latest/download/Hiddify-Windows-Setup-x64.Msix")],
            [InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    elif data == "linux":
        message = "Скачать приложение можно ниже по нажатию на кнопку⬇️\nДля активации зайдите в приложение и скопировав ключ, нажмите добавить из буфера обмена"
        keyboard = [
            [InlineKeyboardButton("Скачать для Linux💻", url="https://github.com/hiddify/hiddify-app/releases/latest/download/Hiddify-Linux-x64.AppImage")],
            [InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]
        ]
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
    elif data == "about":
        conn = sqlite3.connect('vpn_bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        active_users = cursor.fetchone()[0]
        conn.close()
        message = (
            "Мы предоставляем VPN с самой высокой скоростью и комфортной настройкой за считанные секунды.\n\n"
            f"Количество активных пользователей-{active_users}🧮;\n"
            "Сколько мы уже работаем-мы работаем для вас каждый день с 02.11.2025🗓;\n"
            "Активная поддержка 24/7📩;\n"
            "Высокая скорость и доступность нескольких локаций🏎;"
        )
        keyboard = [[InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    elif data == "check_sub":
        # Проверить подписку
        try:
            member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                keyboard = [
                    [InlineKeyboardButton("Подписаться✅", url="https://t.me/H20_shop1")],
                    [InlineKeyboardButton("Проверить подписку", callback_data="check_sub")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text("Вы не подписаны на канал. Для использования бота подпишитесь на наш канал.", reply_markup=reply_markup)
            else:
                keyboard = [
                    [InlineKeyboardButton("Пробный период⌚️", callback_data="trial")],
                    [InlineKeyboardButton("О сервисе📊", callback_data="about")],
                    [InlineKeyboardButton("Помощь🆘", callback_data="help")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text("Подписка проверена! Выберите опцию:", reply_markup=reply_markup)
        except BadRequest:
            await query.edit_message_text("Не удалось проверить подписку на канал.")
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
            [InlineKeyboardButton("О сервисе📊", callback_data="about")],
            [InlineKeyboardButton("Помощь🆘", callback_data="help")]
        ]
        if user_id in ADMINS:
            keyboard.insert(0, [InlineKeyboardButton("Админка", callback_data="admin")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(welcome_message, reply_markup=reply_markup)
    elif data == "admin":
        if user_id not in ADMINS:
            return
        keyboard = [
            [InlineKeyboardButton("Просмотр пользователей", callback_data="admin_users")],
            [InlineKeyboardButton("Заблокировать пользователя", callback_data="admin_ban")],
            [InlineKeyboardButton("Анулировать подписку", callback_data="admin_cancel")],
            [InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Админ меню:", reply_markup=reply_markup)
    elif data == "admin_users":
        if user_id not in ADMINS:
            return
        conn = sqlite3.connect('vpn_bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, trial_used, subscription_expiry, banned FROM users")
        rows = cursor.fetchall()
        conn.close()
        message = "Пользователи:\n"
        for row in rows:
            status = "Заблокирован" if row[3] else ("Активен" if row[2] > time.time() else "Неактивен")
            message += f"ID: {row[0]}, Trial: {'Да' if row[1] else 'Нет'}, Status: {status}\n"
        await query.edit_message_text(message[:4000], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]]))
    elif data == "admin_ban":
        if user_id not in ADMINS:
            return
        await query.edit_message_text("Введите команду /ban <user_id> для блокировки.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]]))
    elif data == "admin_cancel":
        if user_id not in ADMINS:
            return
        await query.edit_message_text("Введите команду /cancel <user_id> для анулирования подписки.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]]))
    elif data == "buy_vpn":
        message = (
            "1️⃣Выберите необходимый тариф.\n"
            "2️⃣Произвидите оплату удобным способом.\n"
            "3️⃣Получите ключ и используйте нам VPN с удовольствием!"
        )
        keyboard = [
            [InlineKeyboardButton("🔴1 мес. - 129руб.🔴", callback_data="buy_1m")],
            [InlineKeyboardButton("🟠3 мес. - 299руб.🟠", callback_data="buy_3m")],
            [InlineKeyboardButton("🟡6 месяцев - 499руб🟡", callback_data="buy_6m")],
            [InlineKeyboardButton("🟢12 месяцев - 899 руб.🟢", callback_data="buy_12m")],
            [InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    elif data == "buy_1m":
        message = (
            "🔢Еще несколько шагов и вы получите стабильный VPN🗿 с быстрейшей скоростью🏎\n"
            "1️⃣Нажмите на кнопку \"Оплатить\" и внесите 129 руб. удобным вам способом и удобной вам валютой.\n"
            "2️⃣Нажмите \"Проверить оплату\" и получите ключ.Наслаждайтесь быстрой скоростью🔰"
        )
        keyboard = [
            [InlineKeyboardButton("xRocket pay 🤖", callback_data="pay_1m")],
            [InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    elif data == "pay_1m":
        payment_id, payment_url = create_xrocket_payment(129, description='VPN subscription 1 month')
        if payment_id:
            conn = sqlite3.connect('vpn_bot.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO payments (user_id, amount, currency, status, payment_id, created_at) VALUES (?, ?, ?, ?, ?, ?)", (user_id, 129, 'RUB', 'pending', payment_id, int(time.time())))
            conn.commit()
            conn.close()
            message = "Ссылка на оплату ниже⬇️"
            keyboard = [
                [InlineKeyboardButton("Оплатить", url=payment_url)],
                [InlineKeyboardButton("Проверить оплату", callback_data="check_payment")],
                [InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup)
        else:
            await query.edit_message_text("Ошибка создания платежа.")
    elif data == "buy_3m":
        # Аналогично для 3 месяцев
        message = (
            "🔢Еще несколько шагов и вы получите стабильный VPN🗿 с быстрейшей скоростью🏎\n"
            "1️⃣Нажмите на кнопку \"Оплатить\" и внесите 299 руб. удобным вам способом и удобной вам валютой.\n"
            "2️⃣Нажмите \"Проверить оплату\" и получите ключ.Наслаждайтесь быстрой скоростью🔰"
        )
        keyboard = [
            [InlineKeyboardButton("xRocket pay 🤖", callback_data="pay_3m")],
            [InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    elif data == "pay_3m":
        payment_id, payment_url = create_xrocket_payment(299, description='VPN subscription 3 months')
        if payment_id:
            conn = sqlite3.connect('vpn_bot.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO payments (user_id, amount, currency, status, payment_id, created_at) VALUES (?, ?, ?, ?, ?, ?)", (user_id, 299, 'RUB', 'pending', payment_id, int(time.time())))
            conn.commit()
            conn.close()
            message = "Ссылка на оплату ниже⬇️"
            keyboard = [
                [InlineKeyboardButton("Оплатить", url=payment_url)],
                [InlineKeyboardButton("Проверить оплату", callback_data="check_payment")],
                [InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup)
        else:
            await query.edit_message_text("Ошибка создания платежа.")
    elif data == "buy_6m":
        message = (
            "🔢Еще несколько шагов и вы получите стабильный VPN🗿 с быстрейшей скоростью🏎\n"
            "1️⃣Нажмите на кнопку \"Оплатить\" и внесите 499 руб. удобным вам способом и удобной вам валютой.\n"
            "2️⃣Нажмите \"Проверить оплату\" и получите ключ.Наслаждайтесь быстрой скоростью🔰"
        )
        keyboard = [
            [InlineKeyboardButton("xRocket pay 🤖", callback_data="pay_6m")],
            [InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    elif data == "pay_6m":
        payment_id, payment_url = create_xrocket_payment(499, description='VPN subscription 6 months')
        if payment_id:
            conn = sqlite3.connect('vpn_bot.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO payments (user_id, amount, currency, status, payment_id, created_at) VALUES (?, ?, ?, ?, ?, ?)", (user_id, 499, 'RUB', 'pending', payment_id, int(time.time())))
            conn.commit()
            conn.close()
            message = "Ссылка на оплату ниже⬇️"
            keyboard = [
                [InlineKeyboardButton("Оплатить", url=payment_url)],
                [InlineKeyboardButton("Проверить оплату", callback_data="check_payment")],
                [InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup)
        else:
            await query.edit_message_text("Ошибка создания платежа.")
    elif data == "buy_12m":
        message = (
            "🔢Еще несколько шагов и вы получите стабильный VPN🗿 с быстрейшей скоростью🏎\n"
            "1️⃣Нажмите на кнопку \"Оплатить\" и внесите 899 руб. удобным вам способом и удобной вам валютой.\n"
            "2️⃣Нажмите \"Проверить оплату\" и получите ключ.Наслаждайтесь быстрой скоростью🔰"
        )
        keyboard = [
            [InlineKeyboardButton("xRocket pay 🤖", callback_data="pay_12m")],
            [InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    elif data == "pay_12m":
        payment_id, payment_url = create_xrocket_payment(899, description='VPN subscription 12 months')
        if payment_id:
            conn = sqlite3.connect('vpn_bot.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO payments (user_id, amount, currency, status, payment_id, created_at) VALUES (?, ?, ?, ?, ?, ?)", (user_id, 899, 'RUB', 'pending', payment_id, int(time.time())))
            conn.commit()
            conn.close()
            message = "Ссылка на оплату ниже⬇️"
            keyboard = [
                [InlineKeyboardButton("Оплатить", url=payment_url)],
                [InlineKeyboardButton("Проверить оплату", callback_data="check_payment")],
                [InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(message, reply_markup=reply_markup)
        else:
            await query.edit_message_text("Ошибка создания платежа.")
    elif data == "check_payment":
        conn = sqlite3.connect('vpn_bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT payment_id, amount FROM payments WHERE user_id = ? AND status = 'pending' ORDER BY created_at DESC LIMIT 1", (user_id,))
        row = cursor.fetchone()
        if row:
            payment_id, amount = row
            status = get_xrocket_payment_status(payment_id)
            if status == 'paid':
                cursor.execute("UPDATE payments SET status = 'paid' WHERE payment_id = ?", (payment_id,))
                # Определить месяцы
                if amount == 129:
                    months = 1
                elif amount == 299:
                    months = 3
                elif amount == 499:
                    months = 6
                elif amount == 899:
                    months = 12
                else:
                    months = 0
                if months > 0:
                    expiry_time = int(time.time() + months * 30 * 24 * 3600)
                    cursor.execute("UPDATE users SET subscription_expiry = ? WHERE user_id = ?", (expiry_time, user_id))
                    conn.commit()
                    # Создать ключ, аналогично trial
                    loop = asyncio.get_event_loop()
                    key = await loop.run_in_executor(None, create_trial_client, user_id)
                    if key.startswith("vless://"):
                        cursor.execute("UPDATE users SET trial_key = ? WHERE user_id = ?", (key, user_id))
                        conn.commit()
                        message = f"Оплата подтверждена! Подписка активирована на {months} месяцев. Ключ: {key}"
                    else:
                        message = f"Оплата подтверждена! Подписка активирована на {months} месяцев. Ошибка генерации ключа: {key}"
                else:
                    message = "Оплата подтверждена, но неизвестный тариф."
                keyboard = [[InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(message, reply_markup=reply_markup)
            else:
                conn.close()
                await query.edit_message_text("Оплата не найдена или еще не подтверждена. Попробуйте позже.")
        else:
            conn.close()
            await query.edit_message_text("Нет ожидающих платежей.")
    elif data == "copy_key":
        # Получить ключ из БД
        conn = sqlite3.connect('vpn_bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT trial_key FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row and row[0]:
            await query.answer()
            await update.callback_query.message.reply_text(f"```{row[0]}```", parse_mode='MarkdownV2')
        else:
            await query.answer("Ключ не найден.")

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in ADMINS:
        await update.message.reply_text("У вас нет прав.")
        return
    if not context.args:
        await update.message.reply_text("Использование: /ban <user_id>")
        return
    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Неверный user_id")
        return
    conn = sqlite3.connect('vpn_bot.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET banned = 1 WHERE user_id = ?", (target_id,))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"Пользователь {target_id} заблокирован.")

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in ADMINS:
        await update.message.reply_text("У вас нет прав.")
        return
    if not context.args:
        await update.message.reply_text("Использование: /unban <user_id>")
        return
    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Неверный user_id")
        return
    conn = sqlite3.connect('vpn_bot.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET banned = 0 WHERE user_id = ?", (target_id,))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"Пользователь {target_id} разблокирован.")

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in ADMINS:
        await update.message.reply_text("У вас нет прав.")
        return
    if not context.args:
        await update.message.reply_text("Использование: /cancel <user_id>")
        return
    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Неверный user_id")
        return
    conn = sqlite3.connect('vpn_bot.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET subscription_expiry = 0 WHERE user_id = ?", (target_id,))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"Подписка пользователя {target_id} анулирована.")

async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in ADMINS:
        await update.message.reply_text("У вас нет прав.")
        return
    conn = sqlite3.connect('vpn_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, trial_used, subscription_expiry, banned FROM users")
    rows = cursor.fetchall()
    conn.close()
    message = "Пользователи:\n"
    for row in rows:
        status = "Заблокирован" if row[3] else ("Активен" if row[2] > time.time() else "Неактивен")
        message += f"ID: {row[0]}, Trial: {'Да' if row[1] else 'Нет'}, Status: {status}\n"
    await update.message.reply_text(message[:4000])

async def check_trial_expiry(application):
    """Проверяет истекшие пробные периоды и отправляет уведомления."""
    while True:
        conn = sqlite3.connect('vpn_bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE subscription_expiry > 0 AND subscription_expiry < ? AND trial_notification_sent = 0", (time.time(),))
        expired_users = cursor.fetchall()
        for (user_id,) in expired_users:
            try:
                await application.bot.send_message(chat_id=user_id, text="Ваш пробный период закончился. Для продолжения приобретите подписку.")
                cursor.execute("UPDATE users SET trial_notification_sent = 1 WHERE user_id = ?", (user_id,))
            except Exception as e:
                logger.error(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
        conn.commit()
        conn.close()
        await asyncio.sleep(3600)  # Проверка каждый час

async def main() -> None:
    """Запуск бота."""
    # Создание таблицы пользователей, если не существует
    conn = sqlite3.connect('vpn_bot.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        trial_used INTEGER DEFAULT 0,
        subscription_expiry INTEGER DEFAULT 0,
        trial_notification_sent INTEGER DEFAULT 0,
        banned INTEGER DEFAULT 0,
        trial_key TEXT DEFAULT ''
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        currency TEXT,
        status TEXT,
        payment_id TEXT,
        created_at INTEGER
    )''')
    # Add columns if not exists
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN trial_notification_sent INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN banned INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN trial_key TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE payments ADD COLUMN payment_id TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE payments ADD COLUMN created_at INTEGER")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

    # Start Flask webhook server in a thread
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000)).start()

    application = ApplicationBuilder().token(TOKEN).build()

    # Добавление обработчика команды /start
    application.add_handler(CommandHandler("start", start))

    # Добавление обработчика callback запросов
    application.add_handler(CallbackQueryHandler(handle_callback))

    # Добавление админ команд
    application.add_handler(CommandHandler("ban", ban_command))
    application.add_handler(CommandHandler("unban", unban_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(CommandHandler("users", users_command))

    # Запустить фоновую задачу для проверки истекших пробных периодов
    asyncio.create_task(check_trial_expiry(application))

    # Запуск бота
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
