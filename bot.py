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
import csv
import io
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import BadRequest
import requests
from flask import Flask, request
import threading

nest_asyncio.apply()

# Flask app for webhook
app = Flask(__name__)

@app.route('/crypto_webhook', methods=['POST'])
def crypto_webhook():
    data = request.get_json()
    logger.info(f"Crypto Pay webhook received: {data}")
    update_type = data.get('update_type')
    if update_type == 'invoice_paid':
        invoice = data.get('payload', {}).get('invoice', {})
        invoice_id = invoice.get('invoice_id')
        if invoice_id:
            conn = sqlite3.connect('vpn_bot.db')
            cursor = conn.cursor()
            cursor.execute("UPDATE payments SET status = 'paid' WHERE payment_id = ?", (invoice_id,))
            conn.commit()
            conn.close()
            logger.info(f"Invoice {invoice_id} marked as paid")
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

# Crypto Pay API Token
CRYPTO_PAY_TOKEN = '524317:AAEWe7SuOrymzNU31p661wRM6W91DaCejH4'


def log_action(action, user_id, details):
    conn = sqlite3.connect('vpn_bot.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO logs (timestamp, action, user_id, details) VALUES (?, ?, ?, ?)", (int(time.time()), action, user_id, details))
    conn.commit()
    conn.close()


def create_crypto_pay_invoice(amount, currency='RUB', description='VPN subscription'):
    try:
        url = 'https://pay.crypt.bot/api/createInvoice'
        headers = {
            'Crypto-Pay-API-Token': CRYPTO_PAY_TOKEN,
            'Content-Type': 'application/json'
        }
        data = {
            'amount': str(amount),
            'currency_type': 'fiat',
            'fiat': currency,
            'description': description
        }
        response = requests.post(url, json=data, headers=headers, timeout=10)
        logger.info(f"Crypto Pay create invoice response: {response.status_code} {response.text}")
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                invoice = result['result']
                return invoice['invoice_id'], invoice['pay_url']
        return None, None
    except Exception as e:
        logger.error(f"Error creating Crypto Pay invoice: {e}")
        return None, None

def get_crypto_pay_invoice_status(invoice_id):
    try:
        url = 'https://pay.crypt.bot/api/getInvoices'
        headers = {
            'Crypto-Pay-API-Token': CRYPTO_PAY_TOKEN,
            'Content-Type': 'application/json'
        }
        data = {
            'invoice_ids': [invoice_id]
        }
        response = requests.get(url, headers=headers, params=data, timeout=30)
        logger.info(f"Crypto Pay get invoices response: {response.status_code} {response.text}")
        if response.status_code == 200:
            result = response.json()
            if result.get('ok') and result['result'] and result['result']['items']:
                invoice = result['result']['items'][0]
                return invoice['status']
            else:
                logger.error(f"API error: {result}")
        else:
            logger.error(f"HTTP error: {response.status_code} {response.text}")
        return 'unknown'
    except requests.RequestException as e:
        logger.error(f"Request error getting Crypto Pay invoice status: {e}")
        return 'unknown'
    except Exception as e:
        logger.error(f"Error getting Crypto Pay invoice status: {e}")
        return 'unknown'



def create_trial_client(user_id, months=3):
    try:
        expiry_seconds = months * 30 * 24 * 3600  # Примерно месяцы
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
            "expiryTime": int((time.time() + expiry_seconds) * 1000),
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
            "remark": f"Subscription {user_id} {months}m",
            "enable": True,
            "expiryTime": int((time.time() + expiry_seconds) * 1000),
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
        [InlineKeyboardButton("Ваши ключи🔑", callback_data="my_keys")],
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
            [InlineKeyboardButton("Ваши ключи🔑", callback_data="my_keys")],
            [InlineKeyboardButton("Купить VPN💎", callback_data="buy_vpn")],
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
            [InlineKeyboardButton("Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton("Просмотр платежей", callback_data="admin_payments")],
            [InlineKeyboardButton("Рассылка", callback_data="admin_broadcast")],
            [InlineKeyboardButton("Управление тарифами", callback_data="admin_tariffs")],
            [InlineKeyboardButton("Экспорт данных", callback_data="admin_export")],
            [InlineKeyboardButton("Резервное копирование", callback_data="admin_backup")],
            [InlineKeyboardButton("Логи", callback_data="admin_logs")],
            [InlineKeyboardButton("Настройки", callback_data="admin_settings")],
            [InlineKeyboardButton("Управление контентом", callback_data="admin_content")],
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
    elif data == "admin_stats":
        if user_id not in ADMINS:
            return
        conn = sqlite3.connect('vpn_bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM users WHERE subscription_expiry > ?", (time.time(),))
        active_subs = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM users WHERE trial_used = 1")
        trial_used = cursor.fetchone()[0]
        cursor.execute("SELECT SUM(amount) FROM payments WHERE status = 'paid'")
        total_revenue = cursor.fetchone()[0] or 0
        cursor.execute("SELECT COUNT(*) FROM users WHERE banned = 1")
        banned_users = cursor.fetchone()[0]
        conn.close()
        message = f"Общее кол-во пользователей: {total_users}\nАктивные подписки: {active_subs}\nИспользовали trial: {trial_used}\nЗаблокированные: {banned_users}\nОбщий доход: {total_revenue} RUB"
        await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Вернуться в админку", callback_data="admin")]]))
    elif data == "admin_payments":
        if user_id not in ADMINS:
            return
        conn = sqlite3.connect('vpn_bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, amount, status, created_at FROM payments ORDER BY created_at DESC LIMIT 10")
        rows = cursor.fetchall()
        conn.close()
        message = "Последние платежи:\n" + "\n".join([f"User {r[0]}: {r[1]} RUB, {r[2]}, {time.strftime('%d.%m.%Y %H:%M', time.localtime(r[3]))}" for r in rows])
        await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Вернуться в админку", callback_data="admin")]]))
    elif data == "admin_broadcast":
        if user_id not in ADMINS:
            return
        await query.edit_message_text("Введите команду /broadcast <сообщение> для рассылки.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Вернуться в админку", callback_data="admin")]]))
    elif data == "admin_tariffs":
        if user_id not in ADMINS:
            return
        conn = sqlite3.connect('vpn_bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT months, price FROM tariffs ORDER BY months")
        rows = cursor.fetchall()
        conn.close()
        message = "Текущие тарифы:\n" + "\n".join([f"{r[0]} мес.: {r[1]} RUB" for r in rows]) + "\n\nКоманды для изменения:\n/setprice1 <цена>\n/setprice3 <цена>\n/setprice6 <цена>\n/setprice12 <цена>"
        await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Вернуться в админку", callback_data="admin")]]))
    elif data == "admin_export":
        if user_id not in ADMINS:
            return
        conn = sqlite3.connect('vpn_bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, trial_used, subscription_expiry, banned FROM users")
        rows = cursor.fetchall()
        conn.close()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['user_id', 'trial_used', 'subscription_expiry', 'banned'])
        writer.writerows(rows)
        csv_data = output.getvalue()
        output.close()
        await context.bot.send_document(chat_id=user_id, document=io.BytesIO(csv_data.encode('utf-8')), filename='users.csv')
        await query.edit_message_text("CSV файл отправлен.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Вернуться в админку", callback_data="admin")]]))
    elif data == "admin_backup":
        if user_id not in ADMINS:
            return
        import shutil
        shutil.copy('vpn_bot.db', 'backup_vpn_bot.db')
        with open('backup_vpn_bot.db', 'rb') as f:
            await context.bot.send_document(chat_id=user_id, document=f, filename='backup_vpn_bot.db')
        await query.edit_message_text("Резервная копия отправлена.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Вернуться в админку", callback_data="admin")]]))
    elif data == "admin_logs":
        if user_id not in ADMINS:
            return
        conn = sqlite3.connect('vpn_bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, action, user_id, details FROM logs ORDER BY timestamp DESC LIMIT 10")
        rows = cursor.fetchall()
        conn.close()
        message = "Последние логи:\n" + "\n".join([f"{time.strftime('%d.%m.%Y %H:%M', time.localtime(r[0]))}: {r[1]} - User {r[2]} - {r[3]}" for r in rows])
        await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Вернуться в админку", callback_data="admin")]]))
    elif data == "admin_settings":
        if user_id not in ADMINS:
            return
        conn = sqlite3.connect('vpn_bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        rows = cursor.fetchall()
        conn.close()
        message = "Настройки:\n" + "\n".join([f"{r[0]}: {r[1]}" for r in rows]) + "\n\nКоманды для изменения:\n/setchannel <ID канала>\n/settoken <токен Crypto Pay>"
        await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Вернуться в админку", callback_data="admin")]]))
    elif data == "admin_content":
        if user_id not in ADMINS:
            return
        conn = sqlite3.connect('vpn_bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM content")
        rows = cursor.fetchall()
        conn.close()
        message = "Контент:\n" + "\n".join([f"{r[0]}: {r[1][:100]}..." for r in rows]) + "\n\nКоманды для изменения:\n/setwelcome <сообщение>\n/setabout <сообщение>"
        await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Вернуться в админку", callback_data="admin")]]))
    elif data == "buy_vpn":
        message = (
            "1️⃣Выберите необходимый тариф.\n"
            "2️⃣Произвидите оплату удобным способом.\n"
            "3️⃣Получите ключ и используйте нам VPN с удовольствием!"
        )
        conn = sqlite3.connect('vpn_bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT months, price FROM tariffs ORDER BY months")
        rows = cursor.fetchall()
        conn.close()
        keyboard = []
        for months, price in rows:
            keyboard.append([InlineKeyboardButton(f"�{months} мес. - {int(price)}руб.�", callback_data=f"buy_{months}m")])
        keyboard.append([InlineKeyboardButton("Вернуться в главное меню", callback_data="back")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    elif data == "buy_1m":
        message = (
            "🔢Еще несколько шагов и вы получите стабильный VPN🗿 с быстрейшей скоростью🏎\n"
            "1️⃣Нажмите на кнопку \"Оплатить\" и внесите 129 руб. удобным вам способом и удобной вам валютой.\n"
            "2️⃣Нажмите \"Проверить оплату\" и получите ключ.Наслаждайтесь быстрой скоростью🔰"
        )
        keyboard = [
            [InlineKeyboardButton("Crypto Pay 🤖", callback_data="pay_1m")],
            [InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    elif data == "pay_1m":
        # Проверить активную подписку
        conn = sqlite3.connect('vpn_bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT subscription_expiry FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        cursor.execute("SELECT price FROM tariffs WHERE months = 1")
        price_row = cursor.fetchone()
        conn.close()
        if not price_row:
            await query.edit_message_text("Ошибка: тариф не найден.")
            return
        amount = price_row[0]
        current_time = time.time()
        if row and row[0] > current_time:
            await query.edit_message_text("У вас уже есть активная подписка. Дождитесь окончания или обратитесь в поддержку.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]]))
        else:
            payment_id, payment_url = create_crypto_pay_invoice(amount, description='VPN subscription 1 month')
            if payment_id:
                conn = sqlite3.connect('vpn_bot.db')
                cursor = conn.cursor()
                cursor.execute("INSERT INTO payments (user_id, amount, currency, status, payment_id, created_at) VALUES (?, ?, ?, ?, ?, ?)", (user_id, amount, 'RUB', 'pending', payment_id, int(time.time())))
                conn.commit()
                conn.close()
                message = "Ссылка на оплату ниже⬇️"
                keyboard = [
                    [InlineKeyboardButton(f"Оплатить | {int(amount)} руб.💸", url=payment_url)],
                    [InlineKeyboardButton("Проверить оплату📩", callback_data="check_payment")],
                    [InlineKeyboardButton("Отменить оплату❌", callback_data="cancel_payment")],
                    [InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(message, reply_markup=reply_markup)
            else:
                await query.edit_message_text("Ошибка создания платежа.")
    elif data == "buy_3m":
        message = (
            "🔢Еще несколько шагов и вы получите стабильный VPN🗿 с быстрейшей скоростью🏎\n"
            "1️⃣Нажмите на кнопку \"Оплатить\" и внесите 299 руб. удобным вам способом и удобной вам валютой.\n"
            "2️⃣Нажмите \"Проверить оплату\" и получите ключ.Наслаждайтесь быстрой скоростью🔰"
        )
        keyboard = [
            [InlineKeyboardButton("Crypto Pay 🤖", callback_data="pay_3m")],
            [InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    elif data == "pay_3m":
        # Проверить активную подписку
        conn = sqlite3.connect('vpn_bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT subscription_expiry FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        cursor.execute("SELECT price FROM tariffs WHERE months = 3")
        price_row = cursor.fetchone()
        conn.close()
        if not price_row:
            await query.edit_message_text("Ошибка: тариф не найден.")
            return
        amount = price_row[0]
        current_time = time.time()
        if row and row[0] > current_time:
            await query.edit_message_text("У вас уже есть активная подписка. Дождитесь окончания или обратитесь в поддержку.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]]))
        else:
            payment_id, payment_url = create_crypto_pay_invoice(amount, description='VPN subscription 3 months')
            if payment_id:
                conn = sqlite3.connect('vpn_bot.db')
                cursor = conn.cursor()
                cursor.execute("INSERT INTO payments (user_id, amount, currency, status, payment_id, created_at, months) VALUES (?, ?, ?, ?, ?, ?, ?)", (user_id, amount, 'RUB', 'pending', payment_id, int(time.time()), 3))
                conn.commit()
                conn.close()
                message = "Ссылка на оплату ниже⬇️"
                keyboard = [
                    [InlineKeyboardButton(f"Оплатить | {int(amount)} руб.💸", url=payment_url)],
                    [InlineKeyboardButton("Проверить оплату📩", callback_data="check_payment")],
                    [InlineKeyboardButton("Отменить оплату❌", callback_data="cancel_payment")],
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
            [InlineKeyboardButton("Crypto Pay 🤖", callback_data="pay_6m")],
            [InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    elif data == "pay_6m":
        # Проверить активную подписку
        conn = sqlite3.connect('vpn_bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT subscription_expiry FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        cursor.execute("SELECT price FROM tariffs WHERE months = 6")
        price_row = cursor.fetchone()
        conn.close()
        if not price_row:
            await query.edit_message_text("Ошибка: тариф не найден.")
            return
        amount = price_row[0]
        current_time = time.time()
        if row and row[0] > current_time:
            await query.edit_message_text("У вас уже есть активная подписка. Дождитесь окончания или обратитесь в поддержку.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]]))
        else:
            payment_id, payment_url = create_crypto_pay_invoice(amount, description='VPN subscription 6 months')
            if payment_id:
                conn = sqlite3.connect('vpn_bot.db')
                cursor = conn.cursor()
                cursor.execute("INSERT INTO payments (user_id, amount, currency, status, payment_id, created_at, months) VALUES (?, ?, ?, ?, ?, ?, ?)", (user_id, amount, 'RUB', 'pending', payment_id, int(time.time()), 6))
                conn.commit()
                conn.close()
                message = "Ссылка на оплату ниже⬇️"
                keyboard = [
                    [InlineKeyboardButton(f"Оплатить | {int(amount)} руб.💸", url=payment_url)],
                    [InlineKeyboardButton("Проверить оплату📩", callback_data="check_payment")],
                    [InlineKeyboardButton("Отменить оплату❌", callback_data="cancel_payment")],
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
            [InlineKeyboardButton("Crypto Pay 🤖", callback_data="pay_12m")],
            [InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup)
    elif data == "pay_12m":
        # Проверить активную подписку
        conn = sqlite3.connect('vpn_bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT subscription_expiry FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        cursor.execute("SELECT price FROM tariffs WHERE months = 12")
        price_row = cursor.fetchone()
        conn.close()
        if not price_row:
            await query.edit_message_text("Ошибка: тариф не найден.")
            return
        amount = price_row[0]
        current_time = time.time()
        if row and row[0] > current_time:
            await query.edit_message_text("У вас уже есть активная подписка. Дождитесь окончания или обратитесь в поддержку.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]]))
        else:
            payment_id, payment_url = create_crypto_pay_invoice(amount, description='VPN subscription 12 months')
            if payment_id:
                conn = sqlite3.connect('vpn_bot.db')
                cursor = conn.cursor()
                cursor.execute("INSERT INTO payments (user_id, amount, currency, status, payment_id, created_at, months) VALUES (?, ?, ?, ?, ?, ?, ?)", (user_id, amount, 'RUB', 'pending', payment_id, int(time.time()), 12))
                conn.commit()
                conn.close()
                message = "Ссылка на оплату ниже⬇️"
                keyboard = [
                    [InlineKeyboardButton(f"Оплатить | {int(amount)} руб.💸", url=payment_url)],
                    [InlineKeyboardButton("Проверить оплату📩", callback_data="check_payment")],
                    [InlineKeyboardButton("Отменить оплату❌", callback_data="cancel_payment")],
                    [InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(message, reply_markup=reply_markup)
            else:
                await query.edit_message_text("Ошибка создания платежа.")
    elif data == "check_payment":
        conn = sqlite3.connect('vpn_bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT payment_id, amount, months FROM payments WHERE user_id = ? AND status = 'pending' ORDER BY created_at DESC LIMIT 1", (user_id,))
        row = cursor.fetchone()
        if row:
            payment_id, amount, months = row
            status = get_crypto_pay_invoice_status(payment_id)
            if status == 'paid':
                cursor.execute("UPDATE payments SET status = 'paid' WHERE payment_id = ?", (payment_id,))
                if months > 0:
                    expiry_time = int(time.time() + months * 30 * 24 * 3600)
                    cursor.execute("UPDATE users SET subscription_expiry = ? WHERE user_id = ?", (expiry_time, user_id))
                    conn.commit()
                    # Создать ключ, аналогично trial
                    loop = asyncio.get_event_loop()
                    key = await loop.run_in_executor(None, create_trial_client, user_id, months)
                    if key.startswith("vless://"):
                        cursor.execute("UPDATE users SET trial_key = ? WHERE user_id = ?", (key, user_id))
                        conn.commit()
                        message = f"Оплата подтверждена! Подписка активирована на {months} месяцев. Ключ: <code>{key}</code>"
                    else:
                        message = f"Оплата подтверждена! Подписка активирована на {months} месяцев. Ошибка генерации ключа: {key}"
                else:
                    message = "Оплата подтверждена, но неизвестный тариф."
                keyboard = [[InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(message, reply_markup=reply_markup)
            else:
                conn.close()
                # Определить тариф для возврата
                if months == 1:
                    pay_callback = "pay_1m"
                elif months == 3:
                    pay_callback = "pay_3m"
                elif months == 6:
                    pay_callback = "pay_6m"
                elif months == 12:
                    pay_callback = "pay_12m"
                else:
                    pay_callback = "buy_vpn"
                await query.edit_message_text("Оплата не найдена или еще не подтверждена.", reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Вернуться к оплате", callback_data=pay_callback)],
                    [InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]
                ]))
        else:
            conn.close()
            await query.edit_message_text("Нет ожидающих платежей.")
    elif data == "my_keys":
        conn = sqlite3.connect('vpn_bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT subscription_expiry, trial_key FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        current_time = time.time()
        subscription_active = row and row[0] > current_time
        key = row[1] if row else None
        if subscription_active and key:
            date_str = time.strftime('%d.%m.%Y %H:%M', time.localtime(row[0]))
            message = f"Ваша подписка активна до {date_str}.\n🔑Ключ:\n<code>{key}</code>"
            keyboard = [
                [InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]
            ]
        elif subscription_active:
            date_str = time.strftime('%d.%m.%Y %H:%M', time.localtime(row[0]))
            message = f"Ваша подписка активна до {date_str}, но ключ не найден."
            keyboard = [[InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]]
        else:
            message = "У вас нет активной подписки."
            keyboard = [
                [InlineKeyboardButton("Купить VPN💎", callback_data="buy_vpn")],
                [InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')
    elif data == "cancel_payment":
        conn = sqlite3.connect('vpn_bot.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM payments WHERE id = (SELECT id FROM payments WHERE user_id = ? AND status = 'pending' ORDER BY created_at DESC LIMIT 1)", (user_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        if deleted:
            await query.edit_message_text("Оплата отменена. Вы можете вернуться и выбрать другой тариф.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Вернуться к тарифам", callback_data="buy_vpn")]]))
        else:
            await query.edit_message_text("Нет активных платежей для отмены.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Вернуться в главное меню", callback_data="back")]]))
    elif data == "copy_key":
        # Получить ключ из БД
        conn = sqlite3.connect('vpn_bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT trial_key FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row and row[0]:
            await query.answer()
            # Экранировать специальные символы для MarkdownV2
            escaped_key = row[0].replace('.', '\.').replace('-', '\-').replace('_', '\_').replace('*', '\*').replace('[', '\[').replace(']', '\]').replace('(', '\(').replace(')', '\)').replace('~', '\~').replace('`', '\`').replace('>', '\>').replace('#', '\#').replace('+', '\+').replace('=', '\=').replace('|', '\|').replace('{', '\{').replace('}', '\}').replace('!', '\!').replace('?', '\?')
            await update.callback_query.message.reply_text(f"```{escaped_key}```", parse_mode='MarkdownV2')
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
    log_action("ban", target_id, f"Admin {update.message.from_user.id}")
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
    log_action("unban", target_id, f"Admin {update.message.from_user.id}")
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
    log_action("cancel_subscription", target_id, f"Admin {update.message.from_user.id}")
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

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in ADMINS:
        await update.message.reply_text("У вас нет прав.")
        return
    if not context.args:
        await update.message.reply_text("Использование: /broadcast <сообщение>")
        return
    message = ' '.join(context.args)
    conn = sqlite3.connect('vpn_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE banned = 0")
    rows = cursor.fetchall()
    conn.close()
    sent = 0
    for (user_id,) in rows:
        try:
            await update.get_bot().send_message(chat_id=user_id, text=message)
            sent += 1
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
    log_action("broadcast", update.message.from_user.id, f"Sent to {sent} users")
    await update.message.reply_text(f"Сообщение отправлено {sent} пользователям.")

async def setprice1_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in ADMINS:
        await update.message.reply_text("У вас нет прав.")
        return
    if not context.args or len(context.args) != 1:
        await update.message.reply_text("Использование: /setprice1 <цена>")
        return
    try:
        price = float(context.args[0])
    except ValueError:
        await update.message.reply_text("Неверная цена.")
        return
    conn = sqlite3.connect('vpn_bot.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE tariffs SET price = ? WHERE months = 1", (price,))
    conn.commit()
    conn.close()
    log_action("set_price", 0, f"1 month: {price}")
    await update.message.reply_text(f"Цена за 1 месяц установлена на {price} RUB.")

async def setprice3_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in ADMINS:
        await update.message.reply_text("У вас нет прав.")
        return
    if not context.args or len(context.args) != 1:
        await update.message.reply_text("Использование: /setprice3 <цена>")
        return
    try:
        price = float(context.args[0])
    except ValueError:
        await update.message.reply_text("Неверная цена.")
        return
    conn = sqlite3.connect('vpn_bot.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE tariffs SET price = ? WHERE months = 3", (price,))
    conn.commit()
    conn.close()
    log_action("set_price", 0, f"3 months: {price}")
    await update.message.reply_text(f"Цена за 3 месяца установлена на {price} RUB.")

async def setprice6_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in ADMINS:
        await update.message.reply_text("У вас нет прав.")
        return
    if not context.args or len(context.args) != 1:
        await update.message.reply_text("Использование: /setprice6 <цена>")
        return
    try:
        price = float(context.args[0])
    except ValueError:
        await update.message.reply_text("Неверная цена.")
        return
    conn = sqlite3.connect('vpn_bot.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE tariffs SET price = ? WHERE months = 6", (price,))
    conn.commit()
    conn.close()
    log_action("set_price", 0, f"6 months: {price}")
    await update.message.reply_text(f"Цена за 6 месяцев установлена на {price} RUB.")

async def setprice12_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in ADMINS:
        await update.message.reply_text("У вас нет прав.")
        return
    if not context.args or len(context.args) != 1:
        await update.message.reply_text("Использование: /setprice12 <цена>")
        return
    try:
        price = float(context.args[0])
    except ValueError:
        await update.message.reply_text("Неверная цена.")
        return
    conn = sqlite3.connect('vpn_bot.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE tariffs SET price = ? WHERE months = 12", (price,))
    conn.commit()
    conn.close()
    log_action("set_price", 0, f"12 months: {price}")
    await update.message.reply_text(f"Цена за 12 месяцев установлена на {price} RUB.")

async def setchannel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in ADMINS:
        await update.message.reply_text("У вас нет прав.")
        return
    if not context.args or len(context.args) != 1:
        await update.message.reply_text("Использование: /setchannel <ID канала>")
        return
    channel_id = context.args[0]
    conn = sqlite3.connect('vpn_bot.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET value = ? WHERE key = 'channel_id'", (channel_id,))
    conn.commit()
    conn.close()
    log_action("set_channel", 0, f"Channel ID: {channel_id}")
    await update.message.reply_text(f"ID канала установлен на {channel_id}.")

async def settoken_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in ADMINS:
        await update.message.reply_text("У вас нет прав.")
        return
    if not context.args or len(context.args) != 1:
        await update.message.reply_text("Использование: /settoken <токен>")
        return
    token = context.args[0]
    conn = sqlite3.connect('vpn_bot.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET value = ? WHERE key = 'crypto_pay_token'", (token,))
    conn.commit()
    conn.close()
    log_action("set_token", 0, "Crypto Pay token updated")
    await update.message.reply_text("Токен Crypto Pay обновлен.")

async def setwelcome_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in ADMINS:
        await update.message.reply_text("У вас нет прав.")
        return
    if not context.args:
        await update.message.reply_text("Использование: /setwelcome <сообщение>")
        return
    message = ' '.join(context.args)
    conn = sqlite3.connect('vpn_bot.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE content SET value = ? WHERE key = 'welcome_message'", (message,))
    conn.commit()
    conn.close()
    log_action("set_welcome", 0, "Welcome message updated")
    await update.message.reply_text("Приветственное сообщение обновлено.")

async def setabout_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.from_user.id not in ADMINS:
        await update.message.reply_text("У вас нет прав.")
        return
    if not context.args:
        await update.message.reply_text("Использование: /setabout <сообщение>")
        return
    message = ' '.join(context.args)
    conn = sqlite3.connect('vpn_bot.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE content SET value = ? WHERE key = 'about_message'", (message,))
    conn.commit()
    conn.close()
    log_action("set_about", 0, "About message updated")
    await update.message.reply_text("Сообщение о сервисе обновлено.")

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
        created_at INTEGER,
        months INTEGER
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS tariffs (
        id INTEGER PRIMARY KEY,
        months INTEGER,
        price REAL
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp INTEGER,
        action TEXT,
        user_id INTEGER,
        details TEXT
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS content (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')

    # Insert default tariffs if empty
    cursor.execute("SELECT COUNT(*) FROM tariffs")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO tariffs (id, months, price) VALUES (?, ?, ?)", [
            (1, 1, 129),
            (2, 3, 299),
            (3, 6, 499),
            (4, 12, 899)
        ])

    # Insert default settings if empty
    cursor.execute("SELECT COUNT(*) FROM settings")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO settings (key, value) VALUES (?, ?)", [
            ('channel_id', CHANNEL_ID),
            ('crypto_pay_token', CRYPTO_PAY_TOKEN)
        ])

    # Insert default content if empty
    cursor.execute("SELECT COUNT(*) FROM content")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO content (key, value) VALUES (?, ?)", [
            ('welcome_message', "Привет👋\n\nМы работаем и наша команда готова освободить Вас от:\n\nЗависающих видео в запрещённой сети;\nБесконечного просмотра рекламы;\nБлокировки из-за частой смены IP-адреса;\nУтечки заряда батареи и ваших данных (как у бесплатных VPN)."),
            ('about_message', "Мы предоставляем VPN с самой высокой скоростью и комфортной настройкой за считанные секунды.\n\nКоличество активных пользователей-{active_users}🧮;\nСколько мы уже работаем-мы работаем для вас каждый день с 02.11.2025🗓;\nАктивная поддержка 24/7📩;\nВысокая скорость и доступность нескольких локаций🏎;")
        ])

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
        cursor.execute("ALTER TABLE payments ADD COLUMN months INTEGER")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

    # Start Flask webhook server in a thread
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000)).start()

    application = Application.builder().token(TOKEN).build()

    # Добавление обработчика команды /start
    application.add_handler(CommandHandler("start", start))

    # Добавление обработчика callback запросов
    application.add_handler(CallbackQueryHandler(handle_callback))

    # Добавление админ команд
    application.add_handler(CommandHandler("ban", ban_command))
    application.add_handler(CommandHandler("unban", unban_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(CommandHandler("users", users_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("setprice1", setprice1_command))
    application.add_handler(CommandHandler("setprice3", setprice3_command))
    application.add_handler(CommandHandler("setprice6", setprice6_command))
    application.add_handler(CommandHandler("setprice12", setprice12_command))
    application.add_handler(CommandHandler("setchannel", setchannel_command))
    application.add_handler(CommandHandler("settoken", settoken_command))
    application.add_handler(CommandHandler("setwelcome", setwelcome_command))
    application.add_handler(CommandHandler("setabout", setabout_command))

    # Запустить фоновую задачу для проверки истекших пробных периодов
    asyncio.create_task(check_trial_expiry(application))

    # Запуск бота
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
